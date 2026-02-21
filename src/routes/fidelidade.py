"""
Fidelidade routes - Teste de Fidelidade pages and API
"""
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.config import settings
from src.services.fidelidade_service import fidelidade_service
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["fidelidade"])
templates = Jinja2Templates(directory="src/templates")


# ── Pydantic models ────────────────────────────────────────────

class RegisterPayload(BaseModel):
    nome: str
    email: str
    telefone: str
    senha: str


class LoginPayload(BaseModel):
    email: str
    senha: str


class CreateTestPayload(BaseModel):
    target_phone: str
    first_message: str


class SendMessagePayload(BaseModel):
    content: str


# ── Auth helper ────────────────────────────────────────────────

def get_user_id_from_request(request: Request) -> Optional[str]:
    """Extract user_id from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    return fidelidade_service.verify_token(token)


# ── HTML Pages ─────────────────────────────────────────────────

@router.get("/fidelidade/quiz", response_class=HTMLResponse)
async def fidelidade_quiz_page(request: Request):
    """Render instigating quiz before registration."""
    return templates.TemplateResponse("fidelidade_quiz.html", {
        "request": request,
    })


@router.get("/fidelidade", response_class=HTMLResponse)
async def fidelidade_register_page(request: Request):
    """Render register/login page."""
    return templates.TemplateResponse("fidelidade_register.html", {
        "request": request,
    })


@router.get("/fidelidade/painel", response_class=HTMLResponse)
async def fidelidade_painel_page(request: Request):
    """Render user dashboard."""
    return templates.TemplateResponse("fidelidade_painel.html", {
        "request": request,
        "checkout_url": settings.FIDELIDADE_CHECKOUT_URL,
    })


@router.get("/fidelidade/chat/{test_id}", response_class=HTMLResponse)
async def fidelidade_chat_page(request: Request, test_id: str):
    """Render chat interface."""
    return templates.TemplateResponse("fidelidade_chat.html", {
        "request": request,
        "test_id": test_id,
        "checkout_url": settings.FIDELIDADE_CHECKOUT_URL,
    })


# ── API Endpoints ──────────────────────────────────────────────

@router.post("/api/fidelidade/register")
async def api_register(payload: RegisterPayload):
    """Register a new user."""
    if not payload.nome or not payload.email or not payload.telefone or not payload.senha:
        return JSONResponse({"success": False, "error": "Preencha todos os campos"}, status_code=400)

    if len(payload.senha) < 6:
        return JSONResponse({"success": False, "error": "Senha deve ter no minimo 6 caracteres"}, status_code=400)

    result = fidelidade_service.register_user(
        payload.nome, payload.email, payload.telefone, payload.senha
    )

    status = 200 if result["success"] else 400
    return JSONResponse(result, status_code=status)


@router.post("/api/fidelidade/login")
async def api_login(payload: LoginPayload):
    """Login user."""
    if not payload.email or not payload.senha:
        return JSONResponse({"success": False, "error": "Preencha todos os campos"}, status_code=400)

    result = fidelidade_service.login_user(payload.email, payload.senha)
    status = 200 if result["success"] else 401
    return JSONResponse(result, status_code=status)


@router.post("/api/fidelidade/test")
async def api_create_test(request: Request, payload: CreateTestPayload):
    """Create a new fidelidade test."""
    user_id = get_user_id_from_request(request)
    if not user_id:
        return JSONResponse({"success": False, "error": "Nao autorizado"}, status_code=401)

    if not payload.target_phone or not payload.first_message:
        return JSONResponse({"success": False, "error": "Preencha todos os campos"}, status_code=400)

    result = await fidelidade_service.create_test(user_id, payload.target_phone, payload.first_message)
    status = 200 if result["success"] else 400
    return JSONResponse(result, status_code=status)


@router.get("/api/fidelidade/tests")
async def api_list_tests(request: Request):
    """List all tests for the logged-in user."""
    user_id = get_user_id_from_request(request)
    if not user_id:
        return JSONResponse({"success": False, "error": "Nao autorizado"}, status_code=401)

    tests = fidelidade_service.get_user_tests(user_id)
    return JSONResponse({"success": True, "tests": tests})


@router.get("/api/fidelidade/messages/{test_id}")
async def api_get_messages(request: Request, test_id: str):
    """Get messages for a test."""
    user_id = get_user_id_from_request(request)
    if not user_id:
        return JSONResponse({"success": False, "error": "Nao autorizado"}, status_code=401)

    result = fidelidade_service.get_messages(test_id, user_id)
    status = 200 if result["success"] else 403
    return JSONResponse(result, status_code=status)


@router.post("/api/fidelidade/messages/{test_id}")
async def api_send_message(request: Request, test_id: str, payload: SendMessagePayload):
    """Send a message in an active test."""
    user_id = get_user_id_from_request(request)
    if not user_id:
        return JSONResponse({"success": False, "error": "Nao autorizado"}, status_code=401)

    if not payload.content:
        return JSONResponse({"success": False, "error": "Mensagem vazia"}, status_code=400)

    result = await fidelidade_service.send_message(test_id, user_id, payload.content)
    status = 200 if result["success"] else 400
    return JSONResponse(result, status_code=status)
