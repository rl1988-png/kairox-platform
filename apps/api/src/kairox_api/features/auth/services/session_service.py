import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from kairox_api.constants.limits import SESSION_REMEMBER_TTL_SECONDS, SESSION_TTL_SECONDS
from kairox_api.core.password import hash_token
from kairox_api.repositories.session_repository import SessionRepository


class SessionService:
    def __init__(self, session_repo: SessionRepository) -> None:
        self._sessions = session_repo

    async def create_session(
        self,
        user_id: UUID,
        remember_me: bool,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[str, int]:
        raw_token = secrets.token_urlsafe(48)
        ttl = SESSION_REMEMBER_TTL_SECONDS if remember_me else SESSION_TTL_SECONDS
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
        await self._sessions.create(user_id, raw_token, expires_at, ip_address, user_agent)
        return raw_token, ttl

    async def validate(self, raw_token: str) -> UUID | None:
        token_hash = hash_token(raw_token)
        record = await self._sessions.get_by_token_hash(token_hash)
        if record is None:
            return None
        if record.expires_at < datetime.now(UTC):
            await self._sessions.revoke(record.id)
            return None
        return record.user_id

    async def revoke(self, raw_token: str) -> None:
        await self._sessions.revoke_by_token_hash(hash_token(raw_token))

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self._sessions.revoke_all_for_user(user_id)
