"""
Plan configuration for Cupido
Maps Lowify products to plan types and defines plan capabilities.
"""
from dataclasses import dataclass
from typing import Optional

from src.models import PlanType


@dataclass
class PlanConfig:
    plan_type: PlanType
    max_messages: int
    has_audio: bool
    has_images: bool
    has_presentation: bool
    label: str
    price: int = 0


PLANS: dict[PlanType, PlanConfig] = {
    PlanType.BASICO: PlanConfig(
        plan_type=PlanType.BASICO,
        max_messages=1,
        has_audio=False,
        has_images=False,
        has_presentation=False,
        label="Mensagem Anônima",
        price=6,
    ),
    PlanType.COM_AUDIO: PlanConfig(
        plan_type=PlanType.COM_AUDIO,
        max_messages=1,
        has_audio=True,
        has_images=False,
        has_presentation=False,
        label="Mensagem + Áudio",
        price=14,
    ),
    PlanType.MULTI_MENSAGEM: PlanConfig(
        plan_type=PlanType.MULTI_MENSAGEM,
        max_messages=5,
        has_audio=True,
        has_images=False,
        has_presentation=False,
        label="Múltiplas Mensagens",
        price=15,
    ),
    PlanType.PREMIUM_HISTORIA: PlanConfig(
        plan_type=PlanType.PREMIUM_HISTORIA,
        max_messages=1,
        has_audio=True,
        has_images=True,
        has_presentation=True,
        label="História Premium",
        price=25,
    ),
}

# Mapeamento Lowify product_id -> PlanType
# Atualizar com os IDs reais dos produtos na Lowify
PRODUCT_ID_MAP: dict[str, PlanType] = {
    # "lowify_product_id_basico": PlanType.BASICO,
    # "lowify_product_id_audio": PlanType.COM_AUDIO,
    # "lowify_product_id_multi": PlanType.MULTI_MENSAGEM,
    # "lowify_product_id_premium": PlanType.PREMIUM_HISTORIA,
}

# Mapeamento por nome do produto (fallback)
PRODUCT_NAME_MAP: dict[str, PlanType] = {
    "cupido basico": PlanType.BASICO,
    "cupido com audio": PlanType.COM_AUDIO,
    "cupido audio": PlanType.COM_AUDIO,
    "cupido multi": PlanType.MULTI_MENSAGEM,
    "cupido multiplas": PlanType.MULTI_MENSAGEM,
    "cupido premium": PlanType.PREMIUM_HISTORIA,
    "cupido historia": PlanType.PREMIUM_HISTORIA,
}


def resolve_plan(product_id: Optional[str] = None, product_name: Optional[str] = None) -> PlanType:
    """Determine plan type from Lowify product info."""
    if product_id and product_id in PRODUCT_ID_MAP:
        return PRODUCT_ID_MAP[product_id]

    if product_name:
        name_lower = product_name.lower().strip()
        for keyword, plan in PRODUCT_NAME_MAP.items():
            if keyword in name_lower:
                return plan

    # Default: basico
    return PlanType.BASICO


def get_plan_config(plan_type: PlanType) -> PlanConfig:
    """Get configuration for a plan type."""
    return PLANS[plan_type]
