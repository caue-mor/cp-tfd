"""
Form routes - Buyer fills in anonymous message details
Supports multi-message flow (1 message at a time) with scheduling.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from src.models import OrderStatus, PlanType
from src.plans import get_plan_config
from src.services.cupido_service import cupido_service
from src.services.supabase_service import supabase_service
from src.utils.fancy_logger import log_error, log_form_submitted, log_presentation_created
from src.utils.logger import get_logger
from src.utils.validators import clean_phone_for_whatsapp, validate_phone

logger = get_logger(__name__)
router = APIRouter(prefix="/form", tags=["form"])
templates = Jinja2Templates(directory="src/templates")


@router.get("/{token}", response_class=HTMLResponse)
async def show_form(request: Request, token: str):
    """Render the message form for the buyer."""
    order = supabase_service.get_order_by_token(token)

    if not order:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "title": "Link invalido",
            "message": "Este link nao existe ou expirou.",
        })

    plan_config = get_plan_config(PlanType(order["plan"]))
    messages_sent = order.get("messages_sent", 0) or 0
    remaining = plan_config.max_messages - messages_sent

    # If all messages sent, show completion page
    if remaining <= 0:
        return templates.TemplateResponse("already_sent.html", {
            "request": request,
            "order": order,
        })

    # For premium plan with presentation already submitted
    if order["status"] in [OrderStatus.SUBMITTED.value, OrderStatus.DELIVERED.value]:
        if plan_config.has_presentation:
            return templates.TemplateResponse("already_sent.html", {
                "request": request,
                "order": order,
            })

    return templates.TemplateResponse("form.html", {
        "request": request,
        "order": order,
        "plan": plan_config,
        "token": token,
        "messages_sent": messages_sent,
        "remaining": remaining,
    })


@router.post("/{token}/submit")
async def submit_form(request: Request, token: str):
    """Process single message submission (supports multi-message flow)."""
    try:
        order = supabase_service.get_order_by_token(token)
        if not order:
            return JSONResponse(content={"error": "Order not found"}, status_code=404)

        plan_config = get_plan_config(PlanType(order["plan"]))
        messages_sent = order.get("messages_sent", 0) or 0
        remaining = plan_config.max_messages - messages_sent

        if remaining <= 0:
            return JSONResponse(content={"error": "Todas as mensagens ja foram enviadas"}, status_code=400)

        data = await request.json()

        recipient_phone = data.get("recipient_phone", "")
        message = data.get("message", "")
        sender_nickname = data.get("sender_nickname", "Alguem especial")
        audio_text = data.get("audio_text", "").strip() if data.get("audio_text") else None
        scheduled_at = data.get("scheduled_at", "").strip() if data.get("scheduled_at") else None

        if not validate_phone(recipient_phone):
            return JSONResponse(content={"error": "Telefone invalido"}, status_code=400)

        if not message.strip():
            return JSONResponse(content={"error": "Mensagem nao pode ser vazia"}, status_code=400)

        # Validate audio_text length
        if audio_text and plan_config.audio_char_limit > 0:
            if len(audio_text) > plan_config.audio_char_limit:
                return JSONResponse(
                    content={"error": f"Texto do audio excede {plan_config.audio_char_limit} caracteres"},
                    status_code=400,
                )

        recipient_clean = clean_phone_for_whatsapp(recipient_phone)

        # Always update recipient_phone on order (each msg can go to different number)
        supabase_service.update_order(order["id"], {
            "recipient_phone": recipient_clean,
        })
        order["recipient_phone"] = recipient_clean

        # Parse scheduled_at if provided
        scheduled_dt = None
        if scheduled_at:
            try:
                scheduled_dt = datetime.fromisoformat(scheduled_at)
                if scheduled_dt.tzinfo is None:
                    scheduled_dt = scheduled_dt.replace(tzinfo=timezone.utc)
            except ValueError:
                return JSONResponse(content={"error": "Data de agendamento invalida"}, status_code=400)

        # Save message to database
        message_data = {
            "order_id": order["id"],
            "message_index": messages_sent,
            "content": message.strip(),
            "sender_nickname": sender_nickname,
            "audio_text": audio_text,
            "scheduled_at": scheduled_dt.isoformat() if scheduled_dt else None,
            "delivered": False,
        }
        saved_message = supabase_service.create_message(message_data)

        if not saved_message:
            return JSONResponse(content={"error": "Falha ao salvar mensagem"}, status_code=500)

        # Increment messages_sent
        new_messages_sent = messages_sent + 1
        supabase_service.update_order(order["id"], {
            "messages_sent": new_messages_sent,
        })

        new_remaining = plan_config.max_messages - new_messages_sent

        log_form_submitted(order["id"], order["plan"], recipient_clean)

        # Check if scheduled for the future
        is_scheduled = False
        if scheduled_dt:
            now = datetime.now(timezone.utc)
            if scheduled_dt > now:
                is_scheduled = True

        if is_scheduled:
            # Don't deliver now, scheduler will handle it
            if new_remaining <= 0:
                supabase_service.update_order(order["id"], {
                    "status": OrderStatus.SUBMITTED.value,
                })
            return JSONResponse(content={
                "status": "scheduled",
                "message": "Mensagem agendada com sucesso!",
                "remaining": new_remaining,
            })

        # Deliver immediately
        order_fresh = supabase_service.get_order_by_token(token)
        success = await cupido_service.deliver_single_message(order_fresh, saved_message)

        if not success:
            return JSONResponse(content={"error": "Falha ao enviar mensagem"}, status_code=500)

        # If this was the last message, mark order as delivered
        if new_remaining <= 0:
            supabase_service.update_order(order["id"], {
                "status": OrderStatus.DELIVERED.value,
                "delivered_at": "now()",
            })

        return JSONResponse(content={
            "status": "ok",
            "message": "Mensagem enviada!",
            "remaining": new_remaining,
        })

    except Exception as e:
        log_error("submit_form", e)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/{token}/upload")
async def upload_premium(
    request: Request,
    token: str,
    title: str = Form("Uma historia para voce"),
    sender_nickname: str = Form("Alguem especial"),
    recipient_phone: str = Form(...),
    slides_data: str = Form("[]"),
    audio_text: str = Form(""),
    files: List[UploadFile] = File(default=[]),
):
    """Process premium upload with images for slideshow."""
    try:
        order = supabase_service.get_order_by_token(token)
        if not order:
            return JSONResponse(content={"error": "Order not found"}, status_code=404)

        if order["status"] in [OrderStatus.SUBMITTED.value, OrderStatus.DELIVERED.value]:
            return JSONResponse(content={"error": "Already submitted"}, status_code=400)

        if not validate_phone(recipient_phone):
            return JSONResponse(content={"error": "Telefone invalido"}, status_code=400)

        recipient_clean = clean_phone_for_whatsapp(recipient_phone)

        # Parse slides captions
        try:
            captions = json.loads(slides_data)
        except json.JSONDecodeError:
            captions = []

        # Upload images and build slides array
        slides = []
        for i, file in enumerate(files):
            if not file.filename:
                continue

            file_bytes = await file.read()
            ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
            file_path = f"presentations/{order['id']}/{uuid.uuid4().hex}.{ext}"

            content_type = file.content_type or "image/jpeg"
            image_url = supabase_service.upload_image(file_path, file_bytes, content_type)

            if image_url:
                caption = captions[i] if i < len(captions) else ""
                slides.append({"image_url": image_url, "caption": caption})

        if not slides:
            return JSONResponse(content={"error": "Nenhuma imagem enviada"}, status_code=400)

        # Create presentation
        presentation = supabase_service.create_presentation({
            "order_id": order["id"],
            "title": title,
            "slides": slides,
        })

        if not presentation:
            return JSONResponse(content={"error": "Falha ao criar apresentacao"}, status_code=500)

        log_presentation_created(presentation["id"], len(slides))

        # Update order and deliver
        supabase_service.update_order(order["id"], {
            "recipient_phone": recipient_clean,
            "status": OrderStatus.SUBMITTED.value,
        })

        # Save a message entry for the premium plan
        audio_text_clean = audio_text.strip() if audio_text else None
        supabase_service.create_message({
            "order_id": order["id"],
            "message_index": 0,
            "content": title,
            "sender_nickname": sender_nickname,
            "audio_text": audio_text_clean,
            "delivered": False,
        })

        order = supabase_service.get_order_by_token(token)
        success = await cupido_service.deliver_premium(order, presentation["id"], audio_text_clean)

        if success:
            return JSONResponse(content={"status": "ok", "message": "Apresentacao enviada!"})

        return JSONResponse(content={"error": "Falha ao enviar"}, status_code=500)

    except Exception as e:
        log_error("upload_premium", e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
