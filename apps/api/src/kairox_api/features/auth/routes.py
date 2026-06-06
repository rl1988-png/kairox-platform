from fastapi import APIRouter, Depends, Request, Response

from kairox_api.constants.limits import SESSION_TTL_SECONDS
from kairox_api.core.auth_rate_limit import enforce_login_rate_limit, enforce_register_rate_limit
from kairox_api.core.cookies import (
    clear_auth_cookies,
    get_session_token,
    set_csrf_cookie,
    set_session_cookie,
    validate_csrf,
)
from kairox_api.dependencies.container import (
    ServiceContainer,
    get_client_ip,
    get_container,
    get_current_user,
    get_session_user,
)
from kairox_api.features.auth.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordConfirm,
    ResetPasswordRequest,
)
from kairox_api.features.auth.services.auth_service import AuthResult
from kairox_api.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _apply_auth_cookies(response: Response, result: AuthResult) -> None:
    set_session_cookie(response, result.session_token, result.session_max_age)
    set_csrf_cookie(response, result.response.csrf_token, result.session_max_age)


@router.post("/register", response_model=AuthResponse)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    container: ServiceContainer = Depends(get_container),
) -> AuthResponse:
    await enforce_register_rate_limit(get_client_ip(request))
    result = await container.auth.register(
        body.username,
        body.email,
        body.password,
        body.invite_code,
        get_client_ip(request),
        request.headers.get("user-agent"),
    )
    _apply_auth_cookies(response, result)
    return result.response


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    container: ServiceContainer = Depends(get_container),
) -> AuthResponse:
    await enforce_login_rate_limit(get_client_ip(request))
    result = await container.auth.login(
        body.username,
        body.password,
        body.remember_me,
        get_client_ip(request),
        request.headers.get("user-agent"),
    )
    _apply_auth_cookies(response, result)
    return result.response


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    container: ServiceContainer = Depends(get_container),
) -> MessageResponse:
    validate_csrf(request)
    await container.auth.logout(get_session_token(request))
    clear_auth_cookies(response)
    return MessageResponse(message="Logged out")


@router.post("/reset-password/request", response_model=MessageResponse)
async def reset_password_request(
    body: ResetPasswordRequest,
    container: ServiceContainer = Depends(get_container),
) -> MessageResponse:
    message = await container.auth.request_password_reset(body.email)
    return MessageResponse(message=message)


@router.post("/reset-password/confirm", response_model=MessageResponse)
async def reset_password_confirm(
    body: ResetPasswordConfirm,
    container: ServiceContainer = Depends(get_container),
) -> MessageResponse:
    await container.auth.confirm_password_reset(body.token, body.password)
    return MessageResponse(message="Password updated successfully")


@router.get("/me", response_model=AuthResponse)
async def me(
    response: Response,
    user: User = Depends(get_session_user),
    container: ServiceContainer = Depends(get_container),
) -> AuthResponse:
    auth_response = await container.auth.build_me_response(user)
    # /me only refreshes the short-lived CSRF token.
    # Session cookie TTL is set at login/register and must not be silently extended here.
    set_csrf_cookie(response, auth_response.csrf_token, SESSION_TTL_SECONDS)
    return auth_response
