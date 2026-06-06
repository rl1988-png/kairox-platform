import secrets

from fastapi import Request, Response

from kairox_api.config.settings import settings
from kairox_api.constants.enums import ErrorCode
from kairox_api.constants.limits import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    SESSION_COOKIE_NAME,
)
from kairox_api.core.errors import AppError


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def _cookie_kwargs(max_age: int) -> dict[str, object]:
    return {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": "strict",
        "max_age": max_age,
        "path": "/",
    }


def set_session_cookie(response: Response, session_token: str, max_age: int) -> None:
    response.set_cookie(key=SESSION_COOKIE_NAME, value=session_token, **_cookie_kwargs(max_age))


def set_csrf_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=max_age,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")


def get_session_token(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE_NAME)


def validate_csrf(request: Request) -> None:
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)

    if not cookie_token or not header_token or cookie_token != header_token:
        raise AppError(ErrorCode.FORBIDDEN, "CSRF validation failed", 403)
