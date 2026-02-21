"""
Acesso routes - Buyer logs in with phone to access their orders
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from src.models import OrderStatus, PlanType
from src.plans import get_plan_config, PLANS
from src.services.supabase_service import supabase_service
from src.utils.logger import get_logger
from src.utils.validators import clean_phone_for_whatsapp, validate_phone

logger = get_logger(__name__)
router = APIRouter(tags=["acesso"])
templates = Jinja2Templates(directory="src/templates")


@router.get("/acesso", response_class=HTMLResponse)
async def show_acesso(request: Request):
    """Render the phone login page."""
    return templates.TemplateResponse("acesso.html", {
        "request": request,
    })


@router.post("/acesso")
async def login_acesso(request: Request):
    """Look up orders by buyer phone and return available ones."""
    try:
        data = await request.json()
        phone = data.get("phone", "")

        if not validate_phone(phone):
            return JSONResponse(content={"error": "Telefone invalido"}, status_code=400)

        phone_clean = clean_phone_for_whatsapp(phone)
        orders = supabase_service.get_orders_by_phone(phone_clean)

        if not orders:
            return JSONResponse(content={"error": "Nenhum pedido encontrado para este numero"}, status_code=404)

        # Build list of available orders
        available = []
        for order in orders:
            plan_type = PlanType(order["plan"])
            plan_config = get_plan_config(plan_type)
            messages_sent = order.get("messages_sent", 0) or 0
            remaining = plan_config.max_messages - messages_sent

            # Determine if order is still usable
            is_delivered = order["status"] in [OrderStatus.DELIVERED.value]
            is_premium_submitted = (
                order["status"] == OrderStatus.SUBMITTED.value
                and plan_config.has_presentation
            )
            all_messages_sent = remaining <= 0

            if is_delivered or is_premium_submitted or all_messages_sent:
                status_label = "Entregue"
                usable = False
            elif order["status"] == OrderStatus.APPROVED.value or (
                order["status"] == OrderStatus.SUBMITTED.value and remaining > 0
            ):
                status_label = f"{remaining} msg restante{'s' if remaining != 1 else ''}" if plan_config.max_messages > 1 else "Disponivel"
                usable = True
            else:
                status_label = order["status"]
                usable = False

            available.append({
                "id": order["id"],
                "plan_label": plan_config.label,
                "plan": order["plan"],
                "form_token": order["form_token"],
                "status_label": status_label,
                "usable": usable,
                "created_at": order["created_at"],
            })

        return JSONResponse(content={"orders": available})

    except Exception as e:
        logger.error(f"Error in login_acesso: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
