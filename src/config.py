"""
Configuration Management
Centralized settings for Cupido - Anonymous WhatsApp Messages
"""
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application Settings with environment variable support."""

    # Environment
    ENVIRONMENT: str = "production"
    PORT: int = 8000

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: Optional[str] = None

    # UAZAPI (WhatsApp)
    UAZAPI_BASE_URL: str = "https://n8nvortexx.uazapi.com"
    UAZAPI_TOKEN: str  # Token fixo do numero Cupido

    # Eleven Labs (Text-to-Speech)
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "pNInz6obpgDQGcFmaJgB"
    ELEVENLABS_MODEL_ID: str = "eleven_multilingual_v2"

    # App
    APP_BASE_URL: str = "http://localhost:8000"
    CUPIDO_PHONE: str = ""

    # Quiz / Funnel
    CHECKOUT_URL: str = "https://pay.stitchdoamor.shop/checkout-white-6829/?add-to-cart=6829"
    QUIZ_VIDEO_URL: str = "https://stitchdoamor.shop/wp-content/uploads/2025/05/AD-STITCH-CLARA.mp4"

    # Redis (optional)
    REDIS_URL: Optional[str] = None

    # Fidelidade (Teste de Fidelidade)
    FIDELIDADE_UAZAPI_TOKEN: str = ""
    FIDELIDADE_CHECKOUT_URL: str = ""
    FIDELIDADE_JWT_SECRET: str = ""

    # CORS
    ALLOWED_ORIGINS: str = "*"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
