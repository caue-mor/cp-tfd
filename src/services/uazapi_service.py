"""
UAZAPI Service - WhatsApp messaging for Cupido
"""
import asyncio
from typing import Any, Dict, List

import httpx

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UAZAPIService:
    """UAZAPI service for WhatsApp integration."""

    def __init__(self):
        self.base_url = settings.UAZAPI_BASE_URL
        self.token = settings.UAZAPI_TOKEN

    async def send_text(self, phone: str, text: str, token: str = None) -> Dict[str, Any]:
        """Send text message via WhatsApp."""
        try:
            phone_clean = phone.replace("@s.whatsapp.net", "").replace("@c.us", "")
            token = token or self.token

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/send/text",
                    headers={"token": token, "Content-Type": "application/json"},
                    json={
                        "number": phone_clean,
                        "text": text,
                        "track_source": "cupido",
                    },
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Text sent to {phone_clean[:10]}...")
                return {"success": True, "data": data}

        except Exception as e:
            logger.error(f"Error sending text: {e}")
            return {"success": False, "error": str(e)}

    async def send_audio(self, phone: str, audio_url: str, token: str = None) -> Dict[str, Any]:
        """Send audio message via WhatsApp."""
        try:
            phone_clean = phone.replace("@s.whatsapp.net", "").replace("@c.us", "")
            token = token or self.token

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/send/media",
                    headers={"token": token, "Content-Type": "application/json"},
                    json={
                        "number": phone_clean,
                        "media_url": audio_url,
                        "media_type": "audio",
                        "track_source": "cupido",
                    },
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Audio sent to {phone_clean[:10]}...")
                return {"success": True, "data": data}

        except Exception as e:
            logger.error(f"Error sending audio: {e}")
            return {"success": False, "error": str(e)}

    async def send_multiple_messages(
        self,
        phone: str,
        messages: List[str],
        token: str = None,
        delay_ms: int = 150,
        typing_duration_ms: int = 2000,
    ) -> List[Dict[str, Any]]:
        """Send multiple messages with typing indicator between them."""
        results = []
        for i, text in enumerate(messages):
            await self.send_presence(phone, token, "composing", delay_ms=typing_duration_ms)
            await asyncio.sleep(typing_duration_ms / 1000.0)
            result = await self.send_text(phone, text, token)
            results.append(result)
            if i < len(messages) - 1:
                await asyncio.sleep(delay_ms / 1000.0)
        return results

    async def send_presence(
        self, phone: str, token: str = None, presence_type: str = "composing", delay_ms: int = 3000
    ) -> Dict[str, Any]:
        """Send presence indicator (composing/recording/paused)."""
        try:
            phone_clean = phone.replace("@s.whatsapp.net", "").replace("@c.us", "")
            token = token or self.token

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/message/presence",
                    headers={"token": token, "Content-Type": "application/json"},
                    json={
                        "number": phone_clean,
                        "presence": presence_type,
                        "delay": delay_ms,
                    },
                )
                response.raise_for_status()
                return {"success": True}

        except Exception as e:
            logger.error(f"Error sending presence: {e}")
            return {"success": False, "error": str(e)}


# Global instance
uazapi_service = UAZAPIService()
