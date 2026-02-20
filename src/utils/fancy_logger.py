"""
Fancy Logger - Logs formatados para Cupido
"""
import json
from typing import Any, Dict, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

SEP = "=" * 80


def log_lowify_webhook(payload: Dict[str, Any]) -> None:
    """Log webhook Lowify recebido"""
    logger.info(f"\n{SEP}")
    logger.info("📥 WEBHOOK LOWIFY RECEBIDO")
    logger.info(SEP)

    event = payload.get("event", "unknown")
    sale_id = payload.get("sale_id", "N/A")
    customer = payload.get("customer", {})
    product = payload.get("product", {})

    logger.info(f"🔷 Evento: {event}")
    logger.info(f"🔷 Sale ID: {sale_id}")
    logger.info(f"👤 Cliente: {customer.get('name', 'N/A')} ({customer.get('phone', 'N/A')})")
    logger.info(f"📦 Produto: {product.get('name', 'N/A')}")

    try:
        logger.info(f"🔍 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    except Exception:
        logger.info(f"🔍 Payload: {payload}")

    logger.info(f"{SEP}\n")


def log_order_created(order_id: str, plan: str, buyer_phone: str) -> None:
    """Log pedido criado"""
    logger.info(f"\n{SEP}")
    logger.info("🎯 PEDIDO CUPIDO CRIADO")
    logger.info(SEP)
    logger.info(f"🆔 Order ID: {order_id}")
    logger.info(f"📋 Plano: {plan}")
    logger.info(f"📱 Comprador: {buyer_phone}")
    logger.info(f"{SEP}\n")


def log_form_submitted(order_id: str, plan: str, recipient_phone: str) -> None:
    """Log formulario submetido"""
    logger.info(f"\n{SEP}")
    logger.info("📝 FORMULARIO SUBMETIDO")
    logger.info(SEP)
    logger.info(f"🆔 Order ID: {order_id}")
    logger.info(f"📋 Plano: {plan}")
    logger.info(f"📱 Destinatario: {recipient_phone}")
    logger.info(f"{SEP}\n")


def log_message_sent(recipient_phone: str, plan: str, has_audio: bool = False) -> None:
    """Log mensagem enviada ao destinatario"""
    logger.info(f"\n{SEP}")
    logger.info("💘 MENSAGEM CUPIDO ENVIADA")
    logger.info(SEP)
    logger.info(f"📱 Destinatario: {recipient_phone}")
    logger.info(f"📋 Plano: {plan}")
    logger.info(f"🔊 Audio: {'Sim' if has_audio else 'Nao'}")
    logger.info(f"{SEP}\n")


def log_audio_generated(order_id: str, audio_url: str) -> None:
    """Log audio gerado pelo Eleven Labs"""
    logger.info(f"\n{SEP}")
    logger.info("🔊 AUDIO GERADO")
    logger.info(SEP)
    logger.info(f"🆔 Order ID: {order_id}")
    logger.info(f"🔗 URL: {audio_url}")
    logger.info(f"{SEP}\n")


def log_presentation_created(presentation_id: str, slide_count: int) -> None:
    """Log apresentacao criada"""
    logger.info(f"\n{SEP}")
    logger.info("🎬 APRESENTACAO CRIADA")
    logger.info(SEP)
    logger.info(f"🆔 Presentation ID: {presentation_id}")
    logger.info(f"📸 Slides: {slide_count}")
    logger.info(f"{SEP}\n")


def log_error(context: str, error: Exception, extra: Optional[Dict] = None) -> None:
    """Log erro formatado"""
    logger.error(f"\n{SEP}")
    logger.error(f"❌ ERRO: {context}")
    logger.error(SEP)
    logger.error(f"🐛 Tipo: {type(error).__name__}")
    logger.error(f"📝 Mensagem: {str(error)}")
    if extra:
        for key, value in extra.items():
            logger.error(f"   {key}: {value}")
    logger.error(f"{SEP}\n")


def log_success(context: str, details: Optional[Dict] = None) -> None:
    """Log sucesso formatado"""
    logger.info(f"\n{SEP}")
    logger.info(f"✅ SUCESSO: {context}")
    logger.info(SEP)
    if details:
        for key, value in details.items():
            logger.info(f"   {key}: {value}")
    logger.info(f"{SEP}\n")
