from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kairox_api.core.password import hash_token
from kairox_api.models.user import UserSession


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: UUID,
        raw_token: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserSession:
        record = UserSession(
            user_id=user_id,
            refresh_token_hash=hash_token(raw_token),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_token_hash(self, token_hash: str) -> UserSession | None:
        result = await self._session.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.revoked_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, session_id: UUID) -> None:
        result = await self._session.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        record = result.scalar_one_or_none()
        if record is not None:
            record.revoked_at = datetime.now(UTC)
            await self._session.flush()

    async def revoke_by_token_hash(self, token_hash: str) -> None:
        result = await self._session.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.revoked_at.is_(None),
            )
        )
        record = result.scalar_one_or_none()
        if record is not None:
            record.revoked_at = datetime.now(UTC)
            await self._session.flush()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        result = await self._session.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
        )
        now = datetime.now(UTC)
        for record in result.scalars().all():
            record.revoked_at = now
        await self._session.flush()
