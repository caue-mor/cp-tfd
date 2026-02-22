"""
Fidelidade Service - Business logic for Teste de Fidelidade
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import bcrypt
import jwt

from src.config import settings
from src.services.supabase_service import supabase_service
from src.services.uazapi_service import uazapi_service
from src.utils.logger import get_logger
from src.utils.validators import clean_phone_for_whatsapp

logger = get_logger(__name__)

JWT_SECRET = settings.FIDELIDADE_JWT_SECRET or settings.SUPABASE_KEY
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7
ACCESS_DURATION_HOURS = 48


class FidelidadeService:
    """Core service for Teste de Fidelidade."""

    # ── Auth ───────────────────────────────────────────────────────

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def create_token(self, user_id: str) -> str:
        payload = {
            "user_id": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def verify_token(self, token: str) -> Optional[str]:
        """Decode JWT and return user_id, or None if invalid."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload.get("user_id")
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    # ── Users ──────────────────────────────────────────────────────

    def register_user(self, nome: str, email: str, telefone: str, senha: str) -> Dict[str, Any]:
        """Register a new fidelidade user."""
        try:
            # Check if email already exists
            existing = (
                supabase_service.client.table("fidelidade_users")
                .select("id")
                .eq("email", email.lower())
                .limit(1)
                .execute()
            )
            if existing.data:
                return {"success": False, "error": "Email ja cadastrado"}

            telefone_clean = clean_phone_for_whatsapp(telefone)
            senha_hash = self.hash_password(senha)

            response = (
                supabase_service.client.table("fidelidade_users")
                .insert({
                    "nome": nome.strip(),
                    "email": email.lower().strip(),
                    "telefone": telefone_clean,
                    "senha_hash": senha_hash,
                })
                .execute()
            )

            if response.data:
                user = response.data[0]
                token = self.create_token(user["id"])
                logger.info(f"Fidelidade user registered: {email}")
                return {"success": True, "token": token, "user_id": user["id"]}

            return {"success": False, "error": "Erro ao criar conta"}

        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return {"success": False, "error": "Erro interno"}

    def login_user(self, email: str, senha: str) -> Dict[str, Any]:
        """Login fidelidade user."""
        try:
            response = (
                supabase_service.client.table("fidelidade_users")
                .select("*")
                .eq("email", email.lower().strip())
                .limit(1)
                .execute()
            )

            if not response.data:
                return {"success": False, "error": "Email ou senha incorretos"}

            user = response.data[0]

            if not self.verify_password(senha, user["senha_hash"]):
                return {"success": False, "error": "Email ou senha incorretos"}

            token = self.create_token(user["id"])
            logger.info(f"Fidelidade user logged in: {email}")
            return {"success": True, "token": token, "user_id": user["id"]}

        except Exception as e:
            logger.error(f"Error logging in: {e}")
            return {"success": False, "error": "Erro interno"}

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            response = (
                supabase_service.client.table("fidelidade_users")
                .select("id, nome, email, telefone, created_at")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    # ── Tests ──────────────────────────────────────────────────────

    async def create_test(self, user_id: str, target_phone: str, first_message: str) -> Dict[str, Any]:
        """Create a fidelidade test and send the first message."""
        try:
            target_clean = clean_phone_for_whatsapp(target_phone)

            # Create test record
            response = (
                supabase_service.client.table("fidelidade_tests")
                .insert({
                    "user_id": user_id,
                    "target_phone": target_clean,
                    "first_message": first_message,
                    "status": "pending",
                })
                .execute()
            )

            if not response.data:
                return {"success": False, "error": "Erro ao criar teste"}

            test = response.data[0]
            test_id = test["id"]

            # Send first message via UAZAPI (from the "woman" number)
            result = await uazapi_service.send_text(
                target_clean,
                first_message,
                token=settings.FIDELIDADE_UAZAPI_TOKEN,
            )

            if not result.get("success"):
                logger.error(f"Failed to send first message for test {test_id}")

            # Save message record
            supabase_service.client.table("fidelidade_messages").insert({
                "test_id": test_id,
                "direction": "outbound",
                "content": first_message,
            }).execute()

            logger.info(f"Fidelidade test created: {test_id}")
            return {"success": True, "test_id": test_id}

        except Exception as e:
            logger.error(f"Error creating test: {e}")
            return {"success": False, "error": "Erro interno"}

    def get_user_tests(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tests for a user."""
        try:
            response = (
                supabase_service.client.table("fidelidade_tests")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            tests = response.data or []
            # Update expired tests
            now = datetime.now(timezone.utc)
            for test in tests:
                if test["status"] == "active" and test.get("expires_at"):
                    expires = datetime.fromisoformat(test["expires_at"].replace("Z", "+00:00"))
                    if now > expires:
                        self._expire_test(test["id"])
                        test["status"] = "expired"
            return tests
        except Exception as e:
            logger.error(f"Error getting tests: {e}")
            return []

    def get_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get a single test by ID."""
        try:
            response = (
                supabase_service.client.table("fidelidade_tests")
                .select("*")
                .eq("id", test_id)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting test: {e}")
            return None

    def is_test_active(self, test: Dict[str, Any]) -> bool:
        """Check if test is paid and not expired."""
        if test.get("status") != "active":
            return False
        if not test.get("expires_at"):
            return False
        expires = datetime.fromisoformat(test["expires_at"].replace("Z", "+00:00"))
        return datetime.now(timezone.utc) < expires

    # ── Messages ───────────────────────────────────────────────────

    def get_messages(self, test_id: str, user_id: str) -> Dict[str, Any]:
        """Get messages for a test. Blur if not paid/expired."""
        test = self.get_test(test_id)
        if not test:
            return {"success": False, "error": "Teste nao encontrado"}

        if test["user_id"] != user_id:
            return {"success": False, "error": "Acesso negado"}

        # Check expiration
        active = self.is_test_active(test)
        if test["status"] == "active" and not active:
            self._expire_test(test_id)
            test["status"] = "expired"

        try:
            response = (
                supabase_service.client.table("fidelidade_messages")
                .select("*")
                .eq("test_id", test_id)
                .order("created_at")
                .execute()
            )
            messages = response.data or []
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            messages = []

        blurred = not active

        if blurred:
            # Return messages with content hidden
            for msg in messages:
                msg["blurred"] = True
                # Keep first 3 chars visible + blur rest
                content = msg["content"]
                if len(content) > 3:
                    msg["content"] = content[:3] + "█" * min(len(content) - 3, 30)
                else:
                    msg["content"] = "█" * 10
        else:
            for msg in messages:
                msg["blurred"] = False

        return {
            "success": True,
            "messages": messages,
            "blurred": blurred,
            "test_status": test["status"],
            "expires_at": test.get("expires_at"),
        }

    async def send_message(self, test_id: str, user_id: str, content: str) -> Dict[str, Any]:
        """Send a message in an active test (user acting as the 'woman')."""
        test = self.get_test(test_id)
        if not test:
            return {"success": False, "error": "Teste nao encontrado"}

        if test["user_id"] != user_id:
            return {"success": False, "error": "Acesso negado"}

        if not self.is_test_active(test):
            return {"success": False, "error": "Teste nao esta ativo ou expirou"}

        try:
            # Send via UAZAPI
            result = await uazapi_service.send_text(
                test["target_phone"],
                content,
                token=settings.FIDELIDADE_UAZAPI_TOKEN,
            )

            if not result.get("success"):
                return {"success": False, "error": "Falha ao enviar mensagem"}

            # Save message
            supabase_service.client.table("fidelidade_messages").insert({
                "test_id": test_id,
                "direction": "outbound",
                "content": content,
            }).execute()

            logger.info(f"Fidelidade message sent for test {test_id}")
            return {"success": True}

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"success": False, "error": "Erro interno"}

    # ── Quick Test (quiz direto) ─────────────────────────────────

    def quick_create_user_or_find(self, nome: str, phone: str) -> Dict[str, Any]:
        """Find existing user by phone, or create one with synthetic email."""
        try:
            phone_clean = clean_phone_for_whatsapp(phone)

            # Busca por telefone
            existing = (
                supabase_service.client.table("fidelidade_users")
                .select("id")
                .eq("telefone", phone_clean)
                .limit(1)
                .execute()
            )
            if existing.data:
                user_id = existing.data[0]["id"]
                token = self.create_token(user_id)
                logger.info(f"Quick test: reusing user {user_id} for phone {phone_clean[:7]}...")
                return {"success": True, "user_id": user_id, "token": token}

            # Cria com email sintetico e senha random
            synthetic_email = f"{phone_clean}@fidelidade.local"
            random_password = secrets.token_urlsafe(16)
            senha_hash = self.hash_password(random_password)

            response = (
                supabase_service.client.table("fidelidade_users")
                .insert({
                    "nome": nome.strip(),
                    "email": synthetic_email,
                    "telefone": phone_clean,
                    "senha_hash": senha_hash,
                })
                .execute()
            )

            if response.data:
                user = response.data[0]
                token = self.create_token(user["id"])
                logger.info(f"Quick test: created user {user['id']} for phone {phone_clean[:7]}...")
                return {"success": True, "user_id": user["id"], "token": token}

            return {"success": False, "error": "Erro ao criar conta"}

        except Exception as e:
            logger.error(f"Error in quick_create_user_or_find: {e}")
            return {"success": False, "error": "Erro interno"}

    async def quick_create_test(
        self, nome: str, buyer_phone: str, target_phone: str, first_message: str
    ) -> Dict[str, Any]:
        """Full quiz flow: create user (or find), create test, send 1st msg, schedule followups."""
        try:
            buyer_clean = clean_phone_for_whatsapp(buyer_phone)
            target_clean = clean_phone_for_whatsapp(target_phone)

            # Buyer != target
            if buyer_clean == target_clean:
                return {"success": False, "error": "O WhatsApp dele precisa ser diferente do seu"}

            # Create/find user
            user_result = self.quick_create_user_or_find(nome, buyer_phone)
            if not user_result["success"]:
                return user_result

            user_id = user_result["user_id"]
            token = user_result["token"]

            # Check duplicata (mesmo user + mesmo target com teste pending/active)
            dup = (
                supabase_service.client.table("fidelidade_tests")
                .select("id")
                .eq("user_id", user_id)
                .eq("target_phone", target_clean)
                .in_("status", ["pending", "active"])
                .limit(1)
                .execute()
            )
            if dup.data:
                # Reutiliza o teste existente
                existing_test_id = dup.data[0]["id"]
                logger.info(f"Quick test: reusing existing test {existing_test_id}")
                return {"success": True, "token": token, "test_id": existing_test_id}

            # Cria teste e envia 1a mensagem (usa metodo existente)
            test_result = await self.create_test(user_id, target_phone, first_message)
            if not test_result["success"]:
                return test_result

            test_id = test_result["test_id"]

            # Agenda mensagens de followup para a compradora
            self._schedule_followup_messages(buyer_clean, test_id)

            return {"success": True, "token": token, "test_id": test_id}

        except Exception as e:
            logger.error(f"Error in quick_create_test: {e}")
            return {"success": False, "error": "Erro interno"}

    def _schedule_followup_messages(self, buyer_phone: str, test_id: str) -> None:
        """Schedule 3 follow-up messages to the buyer after ~10 minutes."""
        try:
            # Lazy import to avoid circular import (scheduler lives in api.py)
            from src.api import scheduler

            now = datetime.now(timezone.utc)
            base_delay = timedelta(minutes=10)

            checkout_url = settings.FIDELIDADE_CHECKOUT_URL

            messages = [
                (base_delay, "Oi amiga, ele respondeu"),
                (base_delay + timedelta(seconds=10), "Nao sei se vc vai querer tirar essa duvida"),
                (
                    base_delay + timedelta(seconds=15),
                    f"se for querer tu so precisa mandar o valor por esse link colocando o mesmo numero do seu zap e mandar o comprovante aqui, esse e um numero que usamos para nao desconfiarem\n\n{checkout_url}",
                ),
            ]

            for i, (delay, text) in enumerate(messages):
                run_at = now + delay
                job_id = f"fidelidade_followup_{test_id}_{i}"
                scheduler.add_job(
                    self._send_followup_message,
                    "date",
                    run_date=run_at,
                    args=[buyer_phone, text],
                    id=job_id,
                    replace_existing=True,
                )

            logger.info(f"Scheduled 3 followup messages for test {test_id}")

        except Exception as e:
            logger.error(f"Error scheduling followup messages: {e}")

    async def _send_followup_message(self, buyer_phone: str, text: str) -> None:
        """Send a single follow-up message to the buyer's WhatsApp."""
        try:
            result = await uazapi_service.send_text(
                buyer_phone,
                text,
                token=settings.FIDELIDADE_UAZAPI_TOKEN,
            )
            if result.get("success"):
                logger.info(f"Followup sent to {buyer_phone[:7]}...")
            else:
                logger.error(f"Followup failed for {buyer_phone[:7]}...")
        except Exception as e:
            logger.error(f"Error sending followup: {e}")

    # ── Payment ────────────────────────────────────────────────────

    def activate_test_by_email(self, email: str, sale_id: str) -> Dict[str, Any]:
        """Activate a pending test when payment is confirmed."""
        try:
            # Find user by email
            user_resp = (
                supabase_service.client.table("fidelidade_users")
                .select("id")
                .eq("email", email.lower().strip())
                .limit(1)
                .execute()
            )

            if not user_resp.data:
                logger.warning(f"Fidelidade payment: user not found for {email}")
                return {"success": False, "error": "Usuario nao encontrado"}

            user_id = user_resp.data[0]["id"]

            # Find most recent pending test
            test_resp = (
                supabase_service.client.table("fidelidade_tests")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "pending")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if not test_resp.data:
                logger.warning(f"Fidelidade payment: no pending test for user {user_id}")
                return {"success": False, "error": "Nenhum teste pendente"}

            test = test_resp.data[0]
            now = datetime.now(timezone.utc).isoformat()
            expires = (datetime.now(timezone.utc) + timedelta(hours=ACCESS_DURATION_HOURS)).isoformat()

            supabase_service.client.table("fidelidade_tests").update({
                "status": "active",
                "sale_id": sale_id,
                "paid_at": now,
                "expires_at": expires,
            }).eq("id", test["id"]).execute()

            logger.info(f"Fidelidade test activated: {test['id']} (sale: {sale_id})")
            return {"success": True, "test_id": test["id"]}

        except Exception as e:
            logger.error(f"Error activating test: {e}")
            return {"success": False, "error": "Erro interno"}

    def activate_test_by_phone(self, phone: str, sale_id: str) -> Dict[str, Any]:
        """Fallback: activate a pending test by buyer phone number."""
        try:
            phone_clean = clean_phone_for_whatsapp(phone)

            user_resp = (
                supabase_service.client.table("fidelidade_users")
                .select("id")
                .eq("telefone", phone_clean)
                .limit(1)
                .execute()
            )

            if not user_resp.data:
                logger.warning(f"Fidelidade payment by phone: user not found for {phone_clean[:7]}...")
                return {"success": False, "error": "Usuario nao encontrado"}

            user_id = user_resp.data[0]["id"]

            test_resp = (
                supabase_service.client.table("fidelidade_tests")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "pending")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if not test_resp.data:
                logger.warning(f"Fidelidade payment by phone: no pending test for user {user_id}")
                return {"success": False, "error": "Nenhum teste pendente"}

            test = test_resp.data[0]
            now = datetime.now(timezone.utc).isoformat()
            expires = (datetime.now(timezone.utc) + timedelta(hours=ACCESS_DURATION_HOURS)).isoformat()

            supabase_service.client.table("fidelidade_tests").update({
                "status": "active",
                "sale_id": sale_id,
                "paid_at": now,
                "expires_at": expires,
            }).eq("id", test["id"]).execute()

            logger.info(f"Fidelidade test activated by phone: {test['id']} (sale: {sale_id})")
            return {"success": True, "test_id": test["id"]}

        except Exception as e:
            logger.error(f"Error activating test by phone: {e}")
            return {"success": False, "error": "Erro interno"}

    # ── Inbound messages (from target) ─────────────────────────────

    async def handle_inbound_message(self, sender_phone: str, content: str) -> Dict[str, Any]:
        """Handle incoming message from target (alvo responding to the 'woman')."""
        try:
            sender_clean = clean_phone_for_whatsapp(sender_phone)

            # Find active/pending test where target_phone matches
            response = (
                supabase_service.client.table("fidelidade_tests")
                .select("*")
                .eq("target_phone", sender_clean)
                .in_("status", ["pending", "active"])
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if not response.data:
                logger.info(f"No fidelidade test found for phone {sender_clean[:7]}...")
                return {"success": False, "error": "Nenhum teste encontrado"}

            test = response.data[0]

            # Save inbound message
            supabase_service.client.table("fidelidade_messages").insert({
                "test_id": test["id"],
                "direction": "inbound",
                "content": content,
            }).execute()

            # Notify the test owner via WhatsApp
            await self._notify_owner(test, content)

            logger.info(f"Inbound message saved for test {test['id']}")
            return {"success": True, "test_id": test["id"]}

        except Exception as e:
            logger.error(f"Error handling inbound message: {e}")
            return {"success": False, "error": "Erro interno"}

    # ── Helpers ─────────────────────────────────────────────────────

    async def _notify_owner(self, test: Dict[str, Any], message_content: str) -> None:
        """Send WhatsApp notification to test owner when target replies."""
        try:
            # Get owner user
            user = self.get_user(test["user_id"])
            if not user:
                return

            phone_alvo = test["target_phone"]
            masked = phone_alvo[:4] + "****" + phone_alvo[-4:]

            chat_url = f"{settings.APP_BASE_URL}/fidelidade/chat/{test['id']}"

            # Preview of the message (first 50 chars)
            preview = message_content[:50]
            if len(message_content) > 50:
                preview += "..."

            notification = (
                f"🔔 *Teste de Fidelidade*\n\n"
                f"O numero {masked} respondeu!\n\n"
                f"💬 _{preview}_\n\n"
                f"Acesse o chat para ver:\n"
                f"👉 {chat_url}"
            )

            # Send via Cupido number (main UAZAPI), not the "woman" number
            await uazapi_service.send_text(user["telefone"], notification)
            logger.info(f"Owner notified: {user['telefone'][:7]}...")

        except Exception as e:
            logger.error(f"Error notifying owner: {e}")

    def _expire_test(self, test_id: str) -> None:
        """Mark a test as expired."""
        try:
            supabase_service.client.table("fidelidade_tests").update({
                "status": "expired",
            }).eq("id", test_id).execute()
            logger.info(f"Test {test_id} expired")
        except Exception as e:
            logger.error(f"Error expiring test: {e}")


# Global instance
fidelidade_service = FidelidadeService()
