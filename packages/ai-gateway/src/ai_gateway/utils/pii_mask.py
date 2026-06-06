import re

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}(?!\w)")
TRON_ADDRESS_PATTERN = re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b")

REDACTED = "[REDACTED]"


def mask_email(text: str) -> str:
    return EMAIL_PATTERN.sub(REDACTED, text)


def mask_phone(text: str) -> str:
    return PHONE_PATTERN.sub(REDACTED, text)


def mask_tron_address(text: str) -> str:
    return TRON_ADDRESS_PATTERN.sub(REDACTED, text)


def mask_pii(value: object) -> object:
    """Recursively mask PII in strings, dicts, and lists."""
    if isinstance(value, str):
        masked = mask_email(value)
        masked = mask_phone(masked)
        masked = mask_tron_address(masked)
        return masked
    if isinstance(value, dict):
        return {str(k): mask_pii(v) for k, v in value.items()}
    if isinstance(value, list):
        return [mask_pii(item) for item in value]
    return value
