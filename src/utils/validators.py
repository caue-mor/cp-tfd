"""
Input Validators for Cupido
Phone validation and normalization utilities
"""
import re


def validate_phone(phone: str) -> bool:
    """Validate phone number format (10-15 digits)."""
    if not phone:
        return False
    phone_clean = phone.replace("@s.whatsapp.net", "").replace("@c.us", "")
    phone_clean = re.sub(r"[^\d]", "", phone_clean)
    return 10 <= len(phone_clean) <= 15


def normalize_phone(phone: str) -> str:
    """Normalize phone to WhatsApp format (e.g. 5585999999999@s.whatsapp.net)."""
    if "@" in phone:
        return phone
    phone_clean = re.sub(r"[^\d]", "", phone)
    return f"{phone_clean}@s.whatsapp.net"


def clean_phone_for_whatsapp(phone: str) -> str:
    """Clean phone number for UAZAPI (digits only, no suffix)."""
    phone_clean = phone.replace("@s.whatsapp.net", "").replace("@c.us", "")
    phone_clean = re.sub(r"[^\d]", "", phone_clean)
    # Ensure Brazil country code
    if len(phone_clean) == 11:  # DDD + 9 digits
        phone_clean = f"55{phone_clean}"
    elif len(phone_clean) == 10:  # DDD + 8 digits (landline)
        phone_clean = f"55{phone_clean}"
    return phone_clean
