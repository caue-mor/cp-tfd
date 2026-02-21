"""
Cupido API - Anonymous WhatsApp Messages Service
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.models import OrderStatus
from src.services.supabase_service import supabase_service
from src.utils.logger import get_logger

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


async def process_scheduled_messages():
    """Check for scheduled messages whose time has passed and deliver them."""
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        messages = supabase_service.get_pending_scheduled_messages(now_iso)

        if not messages:
            return

        logger.info(f"Processing {len(messages)} scheduled messages")

        # Import here to avoid circular imports
        from src.services.cupido_service import cupido_service
        from src.plans import get_plan_config
        from src.models import PlanType

        for msg in messages:
            try:
                order_data = msg.get("cupido_orders")
                if not order_data:
                    logger.warning(f"No order data for scheduled message {msg['id']}")
                    continue

                # Build order dict for deliver_single_message
                order = {
                    "id": order_data["id"],
                    "plan": order_data["plan"],
                    "recipient_phone": order_data["recipient_phone"],
                    "buyer_phone": order_data.get("buyer_phone"),
                    "messages_sent": order_data.get("messages_sent", 0),
                    "status": order_data.get("status"),
                }

                success = await cupido_service.deliver_single_message(order, msg)

                if success:
                    logger.info(f"Scheduled message {msg['id']} delivered")

                    # Check if all messages for this order are now delivered
                    plan_config = get_plan_config(PlanType(order["plan"]))
                    messages_sent = order.get("messages_sent", 0) or 0

                    # Count undelivered messages
                    all_msgs = supabase_service.get_messages_by_order(order["id"])
                    undelivered = [m for m in all_msgs if not m.get("delivered")]
                    if not undelivered:
                        supabase_service.update_order(order["id"], {
                            "status": OrderStatus.DELIVERED.value,
                            "delivered_at": "now()",
                        })
                        logger.info(f"Order {order['id']} fully delivered")
                else:
                    logger.error(f"Failed to deliver scheduled message {msg['id']}")

            except Exception as e:
                logger.error(f"Error processing scheduled message {msg['id']}: {e}")

    except Exception as e:
        logger.error(f"Error in process_scheduled_messages: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting Cupido API...")

    # Connect Supabase
    supabase_service.connect()

    # Start scheduler for scheduled messages
    scheduler.add_job(process_scheduled_messages, "interval", minutes=1)
    scheduler.start()
    logger.info("Scheduler started (checking every 1 minute)")

    logger.info("Cupido API ready!")
    yield

    scheduler.shutdown()
    logger.info("Cupido API stopped.")


app = FastAPI(
    title="Cupido",
    description="Anonymous WhatsApp messages service",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
from src.routes.quiz import router as quiz_router
from src.routes.webhook import router as webhook_router
from src.routes.form import router as form_router
from src.routes.presentation import router as presentation_router
from src.routes.fidelidade import router as fidelidade_router
from src.routes.acesso import router as acesso_router

app.include_router(quiz_router)
app.include_router(webhook_router)
app.include_router(form_router)
app.include_router(presentation_router)
app.include_router(fidelidade_router)
app.include_router(acesso_router)

# Static files (mount after routes so routes take priority)
app.mount("/static", StaticFiles(directory="src/static"), name="static")


# ── Health checks ────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "cupido"}


@app.get("/live")
async def liveness():
    return {"status": "alive"}


@app.get("/ready")
async def readiness():
    checks = {"supabase": False}

    try:
        if supabase_service.client:
            checks["supabase"] = True
    except Exception:
        pass

    all_ok = checks["supabase"]
    status_code = 200 if all_ok else 503

    return JSONResponse(
        content={"status": "ready" if all_ok else "not_ready", "checks": checks},
        status_code=status_code,
    )
