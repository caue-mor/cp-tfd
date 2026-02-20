"""
Webhook routes - Receives Lowify payment webhooks
"""
import json
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.services.cupido_service import cupido_service
from src.services.fidelidade_service import fidelidade_service
from src.utils.fancy_logger import log_error, log_lowify_webhook
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/lowify")
async def webhook_lowify(request: Request):
    """Receive Lowify payment webhook and create order."""
    try:
        payload = await request.json()
        log_lowify_webhook(payload)

        event = payload.get("event", "")

        # Only process approved/paid events
        approved_events = [
            "sale.approved",
            "sale.completed",
            "approved",
            "completed",
            "paid",
        ]

        event_lower = event.lower() if event else ""
        is_approved = any(e in event_lower for e in approved_events)

        if not is_approved:
            logger.info(f"Ignoring event: {event}")
            return JSONResponse(
                content={"status": "ignored", "event": event},
                status_code=200,
            )

        order = await cupido_service.create_order_from_webhook(payload)

        if order:
            return JSONResponse(
                content={
                    "status": "ok",
                    "order_id": order["id"],
                    "form_token": order["form_token"],
                },
                status_code=200,
            )

        return JSONResponse(
            content={"status": "error", "message": "Failed to create order"},
            status_code=500,
        )

    except Exception as e:
        log_error("webhook_lowify", e)
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500,
        )


@router.post("/lowify-debug")
async def webhook_lowify_debug(request: Request):
    """Debug endpoint - logs full payload without processing."""
    try:
        payload = await request.json()
        log_lowify_webhook(payload)
        return JSONResponse(
            content={"status": "ok", "payload_received": True},
            status_code=200,
        )
    except Exception as e:
        body = await request.body()
        logger.error(f"Debug webhook error: {e}, body: {body.decode()[:500]}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=400,
        )


# ── Fidelidade Webhooks ───────────────────────────────────────

@router.post("/fidelidade")
async def webhook_fidelidade(request: Request):
    """Receive Lowify payment webhook for Teste de Fidelidade."""
    try:
        payload = await request.json()
        log_lowify_webhook(payload)

        event = payload.get("event", "")
        approved_events = ["sale.approved", "sale.completed", "approved", "completed", "paid"]
        event_lower = event.lower() if event else ""
        is_approved = any(e in event_lower for e in approved_events)

        if not is_approved:
            logger.info(f"Fidelidade webhook: ignoring event: {event}")
            return JSONResponse({"status": "ignored", "event": event}, status_code=200)

        # Extract buyer info
        customer = payload.get("customer", {}) or {}
        email = customer.get("email") or payload.get("customer_email", "")
        sale_id = payload.get("sale_id", "")

        if not email:
            logger.warning("Fidelidade webhook: no email in payload")
            return JSONResponse({"status": "error", "message": "No email"}, status_code=400)

        result = fidelidade_service.activate_test_by_email(email, sale_id)

        if result["success"]:
            return JSONResponse({
                "status": "ok",
                "test_id": result["test_id"],
            }, status_code=200)

        return JSONResponse({
            "status": "error",
            "message": result.get("error", "Failed"),
        }, status_code=400)

    except Exception as e:
        log_error("webhook_fidelidade", e)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@router.post("/uazapi")
async def webhook_uazapi(request: Request):
    """Receive UAZAPI webhook when target replies to the 'woman' number."""
    try:
        payload = await request.json()
        logger.info(f"UAZAPI webhook received: {json.dumps(payload, ensure_ascii=False)[:500]}")

        # UAZAPI sends message data - extract sender and content
        # Common UAZAPI payload structure:
        # {"event": "messages.upsert", "data": {"key": {"remoteJid": "5511...@s.whatsapp.net"}, "message": {"conversation": "text"}}}
        data = payload.get("data", payload)

        # Try to extract from nested structure
        key = data.get("key", {})
        remote_jid = key.get("remoteJid", "")
        from_me = key.get("fromMe", False)

        # Ignore messages sent by us
        if from_me:
            return JSONResponse({"status": "ignored", "reason": "fromMe"}, status_code=200)

        # Extract phone from remoteJid
        sender_phone = remote_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")

        if not sender_phone:
            # Try alternative payload format
            sender_phone = data.get("phone", data.get("from", ""))

        if not sender_phone:
            return JSONResponse({"status": "ignored", "reason": "no_phone"}, status_code=200)

        # Extract message content
        message_obj = data.get("message", {})
        content = (
            message_obj.get("conversation")
            or message_obj.get("extendedTextMessage", {}).get("text")
            or data.get("text", data.get("body", ""))
        )

        if not content:
            return JSONResponse({"status": "ignored", "reason": "no_content"}, status_code=200)

        result = await fidelidade_service.handle_inbound_message(sender_phone, content)

        return JSONResponse({
            "status": "ok" if result["success"] else "no_match",
        }, status_code=200)

    except Exception as e:
        log_error("webhook_uazapi", e)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
