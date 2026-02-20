"""
Eleven Labs Service - Text-to-Speech for Cupido audio messages
"""
from typing import Optional

import httpx

from src.config import settings
from src.services.supabase_service import supabase_service
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ElevenLabsService:
    """Text-to-Speech via Eleven Labs API."""

    API_BASE = "https://api.elevenlabs.io/v1"

    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.model_id = settings.ELEVENLABS_MODEL_ID

    async def generate_audio(self, text: str) -> Optional[bytes]:
        """Generate MP3 audio from text using Eleven Labs."""
        if not self.api_key:
            logger.error("ELEVENLABS_API_KEY not configured")
            return None

        try:
            url = f"{self.API_BASE}/text-to-speech/{self.voice_id}"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json",
                        "Accept": "audio/mpeg",
                    },
                    json={
                        "text": text,
                        "model_id": self.model_id,
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75,
                        },
                    },
                )
                response.raise_for_status()
                logger.info(f"Audio generated: {len(response.content)} bytes")
                return response.content

        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return None

    async def generate_and_upload(self, text: str, order_id: str) -> Optional[str]:
        """Generate audio and upload to Supabase Storage. Returns public URL."""
        audio_bytes = await self.generate_audio(text)
        if not audio_bytes:
            return None

        file_path = f"audio/{order_id}.mp3"
        public_url = supabase_service.upload_file(file_path, audio_bytes, "audio/mpeg")

        if public_url:
            logger.info(f"Audio uploaded for order {order_id}: {public_url}")

        return public_url


# Global instance
elevenlabs_service = ElevenLabsService()
