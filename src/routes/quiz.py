"""
Quiz routes - Stitch Cupido sales funnel quiz
"""
import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.config import settings
from src.services.supabase_service import supabase_service
from src.services.uazapi_service import uazapi_service
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["quiz"])
templates = Jinja2Templates(directory="src/templates")


class QuizContactPayload(BaseModel):
    nome: str
    telefone: str
    situacao: str = ""
    objetivo: str = ""


@router.get("/", response_class=HTMLResponse)
async def quiz_page(request: Request):
    """Render the Stitch Cupido quiz landing page."""
    return templates.TemplateResponse("quiz.html", {
        "request": request,
        "supabase_url": settings.SUPABASE_URL,
        "supabase_key": settings.SUPABASE_KEY,
        "video_url": settings.QUIZ_VIDEO_URL,
    })


@router.post("/api/quiz/contact")
async def quiz_contact(payload: QuizContactPayload):
    """Receive quiz answers, save to Supabase, send WhatsApp welcome."""
    nome = payload.nome.strip()
    telefone = payload.telefone.strip().replace("(", "").replace(")", "").replace("-", "").replace(" ", "")

    # Ensure country code
    if not telefone.startswith("55"):
        telefone = "55" + telefone

    # Save to Supabase
    try:
        data = {
            "nome": nome,
            "telefone": telefone,
            "situacao_atual": payload.situacao,
            "objetivo_principal": payload.objetivo,
            "origem": "quiz_v2",
        }
        supabase_service.client.table("STITCH_QUIZZ").insert(data).execute()
        logger.info(f"Quiz contact saved: {nome} / {telefone[:7]}...")
    except Exception as e:
        logger.error(f"Error saving quiz contact: {e}")

    # Send WhatsApp welcome message (fire-and-forget)
    mensagem = (
        f"💘 *Stitch Cupido — Mensagem Anônima*\n\n"
        f"Oi, {nome}! Vi que você quer enviar uma mensagem especial 💌\n\n"
        f"Funciona assim: você escolhe um plano, escreve sua mensagem, "
        f"e o Stitch entrega no WhatsApp da pessoa de forma anônima!\n\n"
        f"Nossos planos:\n"
        f"📝 *Básico* — 1 mensagem de texto — R$6\n"
        f"🎙️ *Com Áudio* — texto + áudio do Stitch — R$14\n"
        f"💬 *Multi* — 5 mensagens com texto e áudio — R$15\n"
        f"🎬 *Premium* — apresentação com fotos e música — R$25\n\n"
        f"Qual plano você quer? Me conta aqui que eu te ajudo! 😊"
    )

    asyncio.create_task(_send_whatsapp(telefone, mensagem))

    return {"success": True}


async def _send_whatsapp(phone: str, text: str):
    """Send WhatsApp message in background."""
    try:
        result = await uazapi_service.send_text(phone, text)
        if result.get("success"):
            logger.info(f"WhatsApp welcome sent to {phone[:7]}...")
        else:
            logger.error(f"WhatsApp send failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"Error sending WhatsApp: {e}")
