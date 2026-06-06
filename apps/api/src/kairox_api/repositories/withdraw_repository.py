from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kairox_api.constants.enums import WithdrawStatus
from kairox_api.models.withdraw_request import WithdrawRequest

ACTIVE_WITHDRAW_STATUSES = (WithdrawStatus.PENDING, WithdrawStatus.PROCESSING)


class WithdrawRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: UUID,
        amount: Decimal,
        fee_amount: Decimal,
        to_address: str,
    ) -> WithdrawRequest:
        request = WithdrawRequest(
            user_id=user_id,
            amount=amount,
            fee_amount=fee_amount,
            to_address=to_address,
            status=WithdrawStatus.PENDING,
        )
        self._session.add(request)
        await self._session.flush()
        return request

    async def get_by_id(self, request_id: UUID) -> WithdrawRequest | None:
        result = await self._session.execute(
            select(WithdrawRequest).where(WithdrawRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_for_user(self, user_id: UUID) -> WithdrawRequest | None:
        result = await self._session.execute(
            select(WithdrawRequest).where(
                WithdrawRequest.user_id == user_id,
                WithdrawRequest.status.in_(ACTIVE_WITHDRAW_STATUSES),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: UUID, limit: int = 20) -> list[WithdrawRequest]:
        result = await self._session.execute(
            select(WithdrawRequest)
            .where(WithdrawRequest.user_id == user_id)
            .order_by(WithdrawRequest.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_status(
        self, status: WithdrawStatus | None = None, limit: int = 50
    ) -> list[WithdrawRequest]:
        query = select(WithdrawRequest).order_by(WithdrawRequest.created_at.asc()).limit(limit)
        if status is not None:
            query = query.where(WithdrawRequest.status == status)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_pending(self, limit: int = 50) -> list[WithdrawRequest]:
        return await self.list_by_status(WithdrawStatus.PENDING, limit)

    async def save(self, request: WithdrawRequest) -> WithdrawRequest:
        await self._session.flush()
        return request

    async def sum_pending_amount(self) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(WithdrawRequest.amount), 0)).where(
                WithdrawRequest.status.in_(ACTIVE_WITHDRAW_STATUSES)
            )
        )
        return Decimal(str(result.scalar_one()))

    async def count_pending(self) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(WithdrawRequest)
            .where(WithdrawRequest.status.in_(ACTIVE_WITHDRAW_STATUSES))
        )
        return int(result.scalar_one())
