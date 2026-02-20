"""
Form routes - Buyer fills in anonymous message details
"""
import json
import uuid
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

    if order["status"] in [OrderStatus.SUBMITTED.value, OrderStatus.DELIVERED.value]:
        return templates.TemplateResponse("already_sent.html", {
            "request": request,
            "order": order,
        })

    plan_config = get_plan_config(PlanType(order["plan"]))

    return templates.TemplateResponse("form.html", {
        "request": request,
        "order": order,
        "plan": plan_config,
        "token": token,
    })


@router.post("/{token}/submit")
async def submit_form(request: Request, token: str):
    """Process form submission (basico, com_audio, multi_mensagem)."""
    try:
        order = supabase_service.get_order_by_token(token)
        if not order:
            return JSONResponse(content={"error": "Order not found"}, status_code=404)

        if order["status"] in [OrderStatus.SUBMITTED.value, OrderStatus.DELIVERED.value]:
            return JSONResponse(content={"error": "Message already sent"}, status_code=400)

        data = await request.json()

        recipient_phone = data.get("recipient_phone", "")
        message = data.get("message", "")
        sender_nickname = data.get("sender_nickname", "Alguem especial")
        extra_messages = data.get("extra_messages", [])

        if not validate_phone(recipient_phone):
            return JSONResponse(content={"error": "Telefone invalido"}, status_code=400)

        if not message.strip():
            return JSONResponse(content={"error": "Mensagem nao pode ser vazia"}, status_code=400)

        recipient_clean = clean_phone_for_whatsapp(recipient_phone)

        # Update order with recipient phone
        supabase_service.update_order(order["id"], {
            "recipient_phone": recipient_clean,
            "status": OrderStatus.SUBMITTED.value,
        })

        # Save message(s) to database
        supabase_service.create_message({
            "order_id": order["id"],
            "message_index": 0,
            "content": message,
            "sender_nickname": sender_nickname,
        })

        # For multi-message plan
        for i, extra_msg in enumerate(extra_messages[:4]):  # Max 4 extra
            if extra_msg.strip():
                supabase_service.create_message({
                    "order_id": order["id"],
                    "message_index": i + 1,
                    "content": extra_msg,
                    "sender_nickname": sender_nickname,
                })

        log_form_submitted(order["id"], order["plan"], recipient_clean)

        # Refresh order data and deliver
        order = supabase_service.get_order_by_token(token)
        success = await cupido_service.deliver_order(order)

        if success:
            return JSONResponse(content={"status": "ok", "message": "Mensagem enviada!"})

        return JSONResponse(content={"error": "Falha ao enviar mensagem"}, status_code=500)

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
        supabase_service.create_message({
            "order_id": order["id"],
            "message_index": 0,
            "content": title,
            "sender_nickname": sender_nickname,
        })

        order = supabase_service.get_order_by_token(token)
        success = await cupido_service.deliver_premium(order, presentation["id"])

        if success:
            return JSONResponse(content={"status": "ok", "message": "Apresentacao enviada!"})

        return JSONResponse(content={"error": "Falha ao enviar"}, status_code=500)

    except Exception as e:
        log_error("upload_premium", e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
