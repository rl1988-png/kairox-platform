from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt

from kairox_api.config.settings import settings
from kairox_api.constants.enums import ErrorCode
from kairox_api.core.errors import AppError

ALGORITHM = "HS256"


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> tuple[str, int]:
    expires_delta = timedelta(minutes=settings.jwt_access_ttl_minutes)
    expire = datetime.now(UTC) + expires_delta
    payload: dict[str, Any] = {"sub": subject, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
    return token, int(expires_delta.total_seconds())


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid or expired token", 401) from exc

    if payload.get("type") != expected_type:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid token type", 401)
    return payload


def subject_from_token(token: str, expected_type: str) -> UUID:
    payload = decode_token(token, expected_type)
    sub = payload.get("sub")
    if not sub:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid token subject", 401)
    return UUID(str(sub))
