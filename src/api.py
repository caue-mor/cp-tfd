"""
Cupido API - Anonymous WhatsApp Messages Service
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.services.redis_service import redis_service
from src.services.supabase_service import supabase_service
from src.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting Cupido API...")

    # Connect Supabase
    supabase_service.connect()

    # Connect Redis (optional)
    await redis_service.connect()

    logger.info("Cupido API ready!")
    yield

    # Shutdown
    await redis_service.disconnect()
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

app.include_router(quiz_router)
app.include_router(webhook_router)
app.include_router(form_router)
app.include_router(presentation_router)
app.include_router(fidelidade_router)

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
    checks = {"supabase": False, "redis": False}

    # Check Supabase
    try:
        if supabase_service.client:
            checks["supabase"] = True
    except Exception:
        pass

    # Check Redis
    checks["redis"] = redis_service.available

    all_ok = checks["supabase"]  # Redis is optional
    status_code = 200 if all_ok else 503

    return JSONResponse(
        content={"status": "ready" if all_ok else "not_ready", "checks": checks},
        status_code=status_code,
    )
