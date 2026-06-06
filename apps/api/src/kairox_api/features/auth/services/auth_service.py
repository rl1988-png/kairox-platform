import secrets
from dataclasses import dataclass
from uuid import UUID

from kairox_api.config.settings import settings
from kairox_api.constants.enums import ErrorCode
from kairox_api.constants.limits import (
    GENERIC_RESET_MESSAGE,
    INVALID_CREDENTIALS_MESSAGE,
    PASSWORD_RESET_TTL_SECONDS,
)
from kairox_api.core.cookies import generate_csrf_token
from kairox_api.core.errors import AppError
from kairox_api.core.password import hash_password, verify_password
from kairox_api.core.redis_client import get_redis
from kairox_api.core.security import create_access_token, subject_from_token
from kairox_api.features.auth.schemas.auth import AuthResponse, UserPublic
from kairox_api.features.auth.services.session_service import SessionService
from kairox_api.models.user import User
from kairox_api.repositories.team_repository import TeamRepository
from kairox_api.repositories.user_repository import UserRepository
from kairox_api.services.registration_bonus_service import RegistrationBonusService


@dataclass
class AuthResult:
    response: AuthResponse
    session_token: str
    session_max_age: int


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        team_repo: TeamRepository,
        session_service: SessionService,
        registration_bonus: RegistrationBonusService | None = None,
    ) -> None:
        self._users = user_repo
        self._teams = team_repo
        self._sessions = session_service
        self._registration_bonus = registration_bonus

    async def register(
        self,
        username: str,
        email: str,
        password: str,
        invite_code: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> AuthResult:
        if await self._users.get_by_username(username):
            raise AppError(ErrorCode.CONFLICT, "Registration failed", 409)
        if await self._users.get_by_email(email):
            raise AppError(ErrorCode.CONFLICT, "Registration failed", 409)

        referrer = await self._users.get_by_invite_code(invite_code.upper())
        team_id = None
        referrer_id = None
        if referrer is not None:
            referrer_id = referrer.id
            team_id = referrer.team_id
        else:
            team = await self._teams.get_by_invite_code(invite_code)
            if team is None:
                raise AppError(ErrorCode.CONFLICT, "Registration failed", 409)
            team_id = team.id

        user_invite = secrets.token_hex(4).upper()
        user = await self._users.create(
            username=username,
            email=email,
            password_hash=hash_password(password),
            team_id=team_id,
            deposit_address=settings.tron_deposit_address or None,
            referrer_id=referrer_id,
            invite_code=user_invite,
        )
        if self._registration_bonus is not None:
            await self._registration_bonus.grant_if_eligible(user.id)
        return await self._issue_auth(
            user, remember_me=False, ip_address=ip_address, user_agent=user_agent
        )

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        ip_address: str | None,
        user_agent: str | None,
    ) -> AuthResult:
        user = await self._users.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise AppError(ErrorCode.UNAUTHORIZED, INVALID_CREDENTIALS_MESSAGE, 401)
        if not user.is_active:
            raise AppError(ErrorCode.UNAUTHORIZED, INVALID_CREDENTIALS_MESSAGE, 401)
        return await self._issue_auth(user, remember_me, ip_address, user_agent)

    async def logout(self, session_token: str | None) -> None:
        if session_token:
            await self._sessions.revoke(session_token)

    async def get_user(self, user_id: UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AppError(ErrorCode.NOT_FOUND, "User not found", 404)
        return user

    async def authenticate(self, authorization: str | None, session_token: str | None) -> User:
        if authorization and authorization.startswith("Bearer "):
            token = authorization.removeprefix("Bearer ").strip()
            user_id = subject_from_token(token, "access")
            return await self.get_user(user_id)

        if session_token:
            user_id = await self._sessions.validate(session_token)
            if user_id is not None:
                return await self.get_user(user_id)

        raise AppError(ErrorCode.UNAUTHORIZED, "Authentication required", 401)

    async def build_me_response(self, user: User) -> AuthResponse:
        """Issue fresh access + CSRF tokens without touching the session cookie.

        /me is a token-refresh endpoint. Session TTL is set once at login/register
        and must not be silently extended here.
        """
        access_token, expires_in = create_access_token(
            str(user.id), extra={"role": user.role.value}
        )
        return AuthResponse(
            user=UserPublic.model_validate(user),
            access_token=access_token,
            expires_in=expires_in,
            csrf_token=generate_csrf_token(),
        )

    async def request_password_reset(self, email: str) -> str:
        user = await self._users.get_by_email(email)
        if user is not None:
            token = secrets.token_urlsafe(32)
            redis = await get_redis()
            await redis.setex(f"pwdreset:{token}", PASSWORD_RESET_TTL_SECONDS, str(user.id))
        return GENERIC_RESET_MESSAGE

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        redis = await get_redis()
        user_id_raw = await redis.get(f"pwdreset:{token}")
        if not user_id_raw:
            raise AppError(ErrorCode.NOT_FOUND, "Invalid or expired reset token", 404)

        user = await self.get_user(UUID(str(user_id_raw)))
        user.password_hash = hash_password(new_password)
        await redis.delete(f"pwdreset:{token}")
        # Revoke all active sessions so stolen-session attacks after account compromise
        # cannot persist across a password reset.
        await self._sessions.revoke_all_for_user(user.id)

    async def _issue_auth(
        self,
        user: User,
        remember_me: bool,
        ip_address: str | None,
        user_agent: str | None,
    ) -> AuthResult:
        access_token, expires_in = create_access_token(
            str(user.id), extra={"role": user.role.value}
        )
        session_token, max_age = await self._sessions.create_session(
            user.id, remember_me, ip_address, user_agent
        )
        response = AuthResponse(
            user=UserPublic.model_validate(user),
            access_token=access_token,
            expires_in=expires_in,
            csrf_token=generate_csrf_token(),
        )
        return AuthResult(response=response, session_token=session_token, session_max_age=max_age)
