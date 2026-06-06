from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kairox_api.constants.enums import AuditAction
from kairox_api.models.admin_audit_log import AdminAuditLog
from kairox_api.models.admin_idempotency import AdminIdempotencyKey


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        admin_user_id: UUID,
        action: AuditAction,
        target_type: str,
        target_id: UUID | None = None,
        details: dict[str, object] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AdminAuditLog:
        entry = AdminAuditLog(
            admin_user_id=admin_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_entries(
        self,
        actor_id: UUID | None = None,
        action: AuditAction | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[AdminAuditLog], int]:
        query = select(AdminAuditLog)
        count_query = select(func.count()).select_from(AdminAuditLog)

        if actor_id is not None:
            query = query.where(AdminAuditLog.admin_user_id == actor_id)
            count_query = count_query.where(AdminAuditLog.admin_user_id == actor_id)
        if action is not None:
            query = query.where(AdminAuditLog.action == action)
            count_query = count_query.where(AdminAuditLog.action == action)
        if from_dt is not None:
            query = query.where(AdminAuditLog.created_at >= from_dt)
            count_query = count_query.where(AdminAuditLog.created_at >= from_dt)
        if to_dt is not None:
            query = query.where(AdminAuditLog.created_at <= to_dt)
            count_query = count_query.where(AdminAuditLog.created_at <= to_dt)

        total = int((await self._session.execute(count_query)).scalar_one())
        offset = (page - 1) * limit
        result = await self._session.execute(
            query.order_by(AdminAuditLog.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_idempotency(self, key: str) -> AdminIdempotencyKey | None:
        result = await self._session.execute(
            select(AdminIdempotencyKey).where(AdminIdempotencyKey.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def save_idempotency(
        self,
        key: str,
        admin_user_id: UUID,
        target_user_id: UUID,
        audit_log_id: UUID,
    ) -> AdminIdempotencyKey:
        record = AdminIdempotencyKey(
            idempotency_key=key,
            admin_user_id=admin_user_id,
            target_user_id=target_user_id,
            audit_log_id=audit_log_id,
        )
        self._session.add(record)
        await self._session.flush()
        return record
