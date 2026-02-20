"""
Supabase Service - Database operations for Cupido
"""
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SupabaseService:
    """Supabase service for Cupido database operations."""

    TABLE_ORDERS = "cupido_orders"
    TABLE_MESSAGES = "cupido_messages"
    TABLE_PRESENTATIONS = "cupido_presentations"
    BUCKET_ASSETS = "cupido-assets"

    def __init__(self):
        self.client: Optional[Client] = None

    def connect(self) -> None:
        """Connect to Supabase."""
        try:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("Supabase connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise

    # ── Orders ────────────────────────────────────────────────────────

    def create_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new Cupido order."""
        try:
            response = self.client.table(self.TABLE_ORDERS).insert(order_data).execute()
            if response.data:
                logger.info(f"Order created: {response.data[0]['id']}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None

    def get_order_by_token(self, form_token: str) -> Optional[Dict[str, Any]]:
        """Get order by form token."""
        try:
            response = (
                self.client.table(self.TABLE_ORDERS)
                .select("*")
                .eq("form_token", form_token)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching order by token: {e}")
            return None

    def get_order_by_sale_id(self, sale_id: str) -> Optional[Dict[str, Any]]:
        """Get order by Lowify sale_id."""
        try:
            response = (
                self.client.table(self.TABLE_ORDERS)
                .select("*")
                .eq("sale_id", sale_id)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching order by sale_id: {e}")
            return None

    def update_order(self, order_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an order."""
        try:
            response = (
                self.client.table(self.TABLE_ORDERS)
                .update(updates)
                .eq("id", order_id)
                .execute()
            )
            if response.data:
                logger.info(f"Order {order_id} updated: {list(updates.keys())}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {e}")
            return None

    # ── Messages ──────────────────────────────────────────────────────

    def create_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a Cupido message."""
        try:
            response = self.client.table(self.TABLE_MESSAGES).insert(message_data).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None

    def get_messages_by_order(self, order_id: str) -> List[Dict[str, Any]]:
        """Get all messages for an order."""
        try:
            response = (
                self.client.table(self.TABLE_MESSAGES)
                .select("*")
                .eq("order_id", order_id)
                .order("message_index")
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching messages for order {order_id}: {e}")
            return []

    # ── Presentations ─────────────────────────────────────────────────

    def create_presentation(self, presentation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a Cupido presentation."""
        try:
            response = self.client.table(self.TABLE_PRESENTATIONS).insert(presentation_data).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creating presentation: {e}")
            return None

    def get_presentation(self, presentation_id: str) -> Optional[Dict[str, Any]]:
        """Get a presentation by ID."""
        try:
            response = (
                self.client.table(self.TABLE_PRESENTATIONS)
                .select("*")
                .eq("id", presentation_id)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching presentation {presentation_id}: {e}")
            return None

    def increment_view_count(self, presentation_id: str) -> None:
        """Increment presentation view count."""
        try:
            presentation = self.get_presentation(presentation_id)
            if presentation:
                new_count = (presentation.get("view_count") or 0) + 1
                self.client.table(self.TABLE_PRESENTATIONS).update(
                    {"view_count": new_count}
                ).eq("id", presentation_id).execute()
        except Exception as e:
            logger.error(f"Error incrementing view count: {e}")

    # ── Storage ───────────────────────────────────────────────────────

    def upload_file(self, file_path: str, file_bytes: bytes, content_type: str = "audio/mpeg") -> Optional[str]:
        """Upload file to Supabase Storage and return public URL."""
        try:
            self.client.storage.from_(self.BUCKET_ASSETS).upload(
                file_path,
                file_bytes,
                {"content-type": content_type},
            )
            public_url = self.client.storage.from_(self.BUCKET_ASSETS).get_public_url(file_path)
            logger.info(f"File uploaded: {file_path}")
            return public_url
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None

    def upload_image(self, file_path: str, file_bytes: bytes, content_type: str = "image/jpeg") -> Optional[str]:
        """Upload image to Supabase Storage and return public URL."""
        return self.upload_file(file_path, file_bytes, content_type)


# Global instance
supabase_service = SupabaseService()
