"""
Cupido Service - Core business logic for anonymous message delivery
"""
from typing import Any, Dict, Optional

from src.config import settings
from src.models import OrderStatus, PlanType
from src.plans import get_plan_config, resolve_plan
from src.services.elevenlabs_service import elevenlabs_service
from src.services.supabase_service import supabase_service
from src.services.uazapi_service import uazapi_service
from src.utils.fancy_logger import (
    log_audio_generated,
    log_error,
    log_message_sent,
    log_order_created,
    log_presentation_created,
)
from src.utils.logger import get_logger
from src.utils.validators import clean_phone_for_whatsapp

logger = get_logger(__name__)


class CupidoService:
    """Core service for Cupido anonymous messages."""

    async def create_order_from_webhook(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create order from Lowify webhook and send form link to buyer.
        Returns the created order or None.
        """
        # Extract customer/product info (handles both nested and flat formats)
        customer = payload.get("customer", {}) or {}
        product = payload.get("product", {}) or {}

        buyer_name = customer.get("name") or payload.get("customer_name", "")
        buyer_phone = customer.get("phone") or payload.get("customer_phone", "")
        buyer_email = customer.get("email") or payload.get("customer_email", "")
        product_id = product.get("id") or payload.get("product_id", "")
        product_name = product.get("name") or payload.get("product_name", "")
        sale_id = payload.get("sale_id", "")
        event = payload.get("event", "")

        if not buyer_phone:
            logger.warning("Webhook without buyer phone - skipping")
            return None

        # Check if order already exists for this sale
        if sale_id:
            existing = supabase_service.get_order_by_sale_id(sale_id)
            if existing:
                logger.info(f"Order already exists for sale {sale_id}")
                return existing

        # Resolve plan from product info
        plan_type = resolve_plan(str(product_id) if product_id else None, product_name)
        plan_config = get_plan_config(plan_type)

        # Determine if this is a test
        is_test = "test" in event.lower() if event else False

        # Create order in database
        order_data = {
            "sale_id": sale_id or None,
            "plan": plan_type.value,
            "status": OrderStatus.APPROVED.value,
            "buyer_name": buyer_name,
            "buyer_phone": clean_phone_for_whatsapp(buyer_phone),
            "buyer_email": buyer_email,
            "product_name": product_name,
            "is_test": is_test,
        }

        order = supabase_service.create_order(order_data)
        if not order:
            logger.error("Failed to create order in database")
            return None

        log_order_created(order["id"], plan_type.value, order["buyer_phone"])

        # Send form link to buyer via WhatsApp (2 messages: text + link)
        base = settings.APP_BASE_URL.strip().rstrip("/")
        form_url = f"{base}/form/{order['form_token']}"

        msg1 = (
            f"*Cupido - Mensagem Anonima*\n\n"
            f"Oi, {buyer_name or 'voce'}! Seu pedido *{plan_config.label}* foi aprovado!\n\n"
            f"Clique no link abaixo para preencher sua mensagem anonima:"
        )

        await uazapi_service.send_text(order["buyer_phone"], msg1)
        await uazapi_service.send_text(order["buyer_phone"], form_url)

        return order

    async def deliver_basico(self, order: Dict[str, Any], message_text: str, sender_nickname: str) -> bool:
        """Deliver basic plan: single anonymous text message."""
        recipient = order.get("recipient_phone")
        if not recipient:
            return False

        text = (
            f"💘 *Mensagem Anonima do Cupido*\n\n"
            f"Alguem especial te enviou uma mensagem:\n\n"
            f"_{message_text}_\n\n"
            f"— {sender_nickname}"
        )

        result = await uazapi_service.send_text(recipient, text)

        if result.get("success"):
            supabase_service.update_order(order["id"], {
                "status": OrderStatus.DELIVERED.value,
                "delivered_at": "now()",
            })
            log_message_sent(recipient, "basico")
            return True

        return False

    async def deliver_com_audio(self, order: Dict[str, Any], message_text: str, sender_nickname: str) -> bool:
        """Deliver audio plan: text message + generated audio."""
        recipient = order.get("recipient_phone")
        if not recipient:
            return False

        # Send text first
        text = (
            f"💘 *Mensagem Anonima do Cupido*\n\n"
            f"Alguem especial te enviou uma mensagem com audio:\n\n"
            f"_{message_text}_\n\n"
            f"— {sender_nickname}"
        )

        await uazapi_service.send_text(recipient, text)

        # Generate and send audio
        audio_url = await elevenlabs_service.generate_and_upload(message_text, order["id"])
        if audio_url:
            log_audio_generated(order["id"], audio_url)
            await uazapi_service.send_audio(recipient, audio_url)

            # Save audio URL to message
            messages = supabase_service.get_messages_by_order(order["id"])
            if messages:
                # Update first message with audio URL
                from src.services.supabase_service import supabase_service as supa
                supa.client.table(supa.TABLE_MESSAGES).update(
                    {"audio_url": audio_url}
                ).eq("id", messages[0]["id"]).execute()

        supabase_service.update_order(order["id"], {
            "status": OrderStatus.DELIVERED.value,
            "delivered_at": "now()",
        })
        log_message_sent(recipient, "com_audio", has_audio=True)
        return True

    async def deliver_multi(self, order: Dict[str, Any], messages_data: list) -> bool:
        """Deliver multi-message plan: multiple sequential text messages."""
        recipient = order.get("recipient_phone")
        if not recipient:
            return False

        # First message is the intro
        intro = (
            f"💘 *Mensagem Anonima do Cupido*\n\n"
            f"Alguem especial te enviou varias mensagens! 💌"
        )

        texts = [intro] + [m.get("content", "") for m in messages_data if m.get("content")]

        await uazapi_service.send_multiple_messages(recipient, texts, typing_duration_ms=2500)

        supabase_service.update_order(order["id"], {
            "status": OrderStatus.DELIVERED.value,
            "delivered_at": "now()",
        })
        log_message_sent(recipient, "multi_mensagem")
        return True

    async def deliver_premium(self, order: Dict[str, Any], presentation_id: str) -> bool:
        """Deliver premium plan: send link to slideshow presentation."""
        recipient = order.get("recipient_phone")
        if not recipient:
            return False

        presentation_url = f"{settings.APP_BASE_URL}/p/{presentation_id}"

        text = (
            f"💘 *Mensagem Anonima do Cupido*\n\n"
            f"Alguem especial preparou algo muito especial pra voce!\n\n"
            f"Abra o link abaixo para ver:\n\n"
            f"👉 {presentation_url}\n\n"
            f"💌 Feito com amor!"
        )

        result = await uazapi_service.send_text(recipient, text)

        if result.get("success"):
            supabase_service.update_order(order["id"], {
                "status": OrderStatus.DELIVERED.value,
                "delivered_at": "now()",
            })
            log_message_sent(recipient, "premium_historia")
            return True

        return False

    async def deliver_order(self, order: Dict[str, Any]) -> bool:
        """Deliver an order based on its plan type."""
        plan = order.get("plan")
        order_id = order.get("id")

        messages = supabase_service.get_messages_by_order(order_id)
        if not messages:
            logger.error(f"No messages found for order {order_id}")
            return False

        first_message = messages[0]
        sender_nickname = first_message.get("sender_nickname", "Alguem especial")

        if plan == PlanType.BASICO.value:
            return await self.deliver_basico(order, first_message["content"], sender_nickname)

        elif plan == PlanType.COM_AUDIO.value:
            return await self.deliver_com_audio(order, first_message["content"], sender_nickname)

        elif plan == PlanType.MULTI_MENSAGEM.value:
            return await self.deliver_multi(order, messages)

        elif plan == PlanType.PREMIUM_HISTORIA.value:
            # For premium, check if presentation exists
            presentations = supabase_service.client.table(
                supabase_service.TABLE_PRESENTATIONS
            ).select("id").eq("order_id", order_id).limit(1).execute()

            if presentations.data:
                return await self.deliver_premium(order, presentations.data[0]["id"])
            else:
                logger.error(f"No presentation found for premium order {order_id}")
                return False

        else:
            logger.error(f"Unknown plan type: {plan}")
            return False


# Global instance
cupido_service = CupidoService()
