"""
Data models for Cupido
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────

class PlanType(str, Enum):
    BASICO = "basico"
    COM_AUDIO = "com_audio"
    MULTI_MENSAGEM = "multi_mensagem"
    PREMIUM_HISTORIA = "premium_historia"


class OrderStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    DELIVERED = "delivered"
    REFUNDED = "refunded"
    CANCELED = "canceled"


# ── Lowify Webhook ─────────────────────────────────────────────────────

class LowifyCustomer(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    doc: Optional[str] = None


class LowifyProduct(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None


class LowifyWebhookPayload(BaseModel):
    event: Optional[str] = None
    sale_id: Optional[str] = None
    customer: Optional[LowifyCustomer] = None
    product: Optional[LowifyProduct] = None
    # Campos alternativos (formato flat)
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None


# ── Form Submissions ──────────────────────────────────────────────────

class MessageFormSubmission(BaseModel):
    recipient_phone: str
    message: str
    sender_nickname: Optional[str] = "Alguem especial"
    audio_text: Optional[str] = None
    scheduled_at: Optional[str] = None
    # Para multi_mensagem (legacy, kept for compatibility)
    extra_messages: Optional[List[str]] = None


class SlideData(BaseModel):
    image_url: str
    caption: Optional[str] = ""


class PremiumFormSubmission(BaseModel):
    recipient_phone: str
    title: str = "Uma historia para voce"
    slides: List[SlideData] = Field(default_factory=list)
    sender_nickname: Optional[str] = "Alguem especial"
