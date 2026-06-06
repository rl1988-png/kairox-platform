from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kairox_api.constants.enums import RechargeStatus, TradeState
from kairox_api.models.recharge_order import RechargeOrder
from kairox_api.models.trade import Trade


class TradeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_for_user(
        self, user_id: UUID, active_states: set[TradeState] | None = None
    ) -> Trade | None:
        states = list(
            active_states
            or {
                TradeState.PENDING_FUNDS,
                TradeState.READY,
                TradeState.RUNNING,
                TradeState.SETTLING,
                TradeState.PRE_STARTED,
            }
        )
        result = await self._session.execute(
            select(Trade)
            .where(Trade.user_id == user_id, Trade.state.in_(states))
            .order_by(Trade.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_pre_start(
        self,
        user_id: UUID,
        vip_level: int,
        amount: Decimal,
        duration_seconds: int,
        expires_at: datetime,
    ) -> Trade:
        trade = Trade(
            user_id=user_id,
            vip_level=vip_level,
            amount=amount,
            duration_seconds=duration_seconds,
            expires_at=expires_at,
            state=TradeState.IDLE,
        )
        self._session.add(trade)
        await self._session.flush()
        return trade

    async def create(self, user_id: UUID, amount: Decimal) -> Trade:
        trade = Trade(user_id=user_id, amount=amount, state=TradeState.PENDING_FUNDS)
        self._session.add(trade)
        await self._session.flush()
        return trade

    async def get_by_id(self, trade_id: UUID) -> Trade | None:
        result = await self._session.execute(select(Trade).where(Trade.id == trade_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, trade_id: UUID, user_id: UUID) -> Trade | None:
        result = await self._session.execute(
            select(Trade).where(Trade.id == trade_id, Trade.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def count_completed_today(self, user_id: UUID) -> int:
        start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self._session.execute(
            select(Trade.id).where(
                Trade.user_id == user_id,
                Trade.state == TradeState.COMPLETED,
                Trade.completed_at >= start_of_day,
            )
        )
        return len(list(result.scalars().all()))

    async def get_last_completed_at(self, user_id: UUID) -> datetime | None:
        result = await self._session.execute(
            select(Trade)
            .where(Trade.user_id == user_id, Trade.state == TradeState.COMPLETED)
            .order_by(Trade.completed_at.desc())
            .limit(1)
        )
        trade = result.scalar_one_or_none()
        return trade.completed_at if trade else None

    async def save(self, trade: Trade) -> Trade:
        await self._session.flush()
        return trade

    async def count_today(self) -> int:
        start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self._session.execute(
            select(func.count()).select_from(Trade).where(Trade.created_at >= start_of_day)
        )
        return int(result.scalar_one())

    async def list_recent(self, limit: int = 50) -> list[Trade]:
        result = await self._session.execute(
            select(Trade).order_by(Trade.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())


class RechargeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_tx_hash(self, tx_hash: str) -> RechargeOrder | None:
        result = await self._session.execute(
            select(RechargeOrder).where(RechargeOrder.tx_hash == tx_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, order_id: UUID, user_id: UUID) -> RechargeOrder | None:
        result = await self._session.execute(
            select(RechargeOrder).where(
                RechargeOrder.id == order_id,
                RechargeOrder.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_order(
        self,
        user_id: UUID,
        expected_amount: Decimal,
        deposit_address: str,
        expires_at: datetime,
    ) -> RechargeOrder:
        order = RechargeOrder(
            user_id=user_id,
            expected_amount=expected_amount,
            amount=expected_amount,
            deposit_address=deposit_address,
            expires_at=expires_at,
            status=RechargeStatus.PENDING,
            tx_hash=None,
        )
        self._session.add(order)
        await self._session.flush()
        return order

    async def list_pending_active(self, limit: int = 100) -> list[RechargeOrder]:
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(RechargeOrder)
            .where(
                RechargeOrder.status == RechargeStatus.PENDING,
                RechargeOrder.expires_at.is_not(None),
                RechargeOrder.expires_at > now,
            )
            .order_by(RechargeOrder.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_confirming(self, limit: int = 100) -> list[RechargeOrder]:
        result = await self._session.execute(
            select(RechargeOrder)
            .where(RechargeOrder.status == RechargeStatus.CONFIRMING)
            .order_by(RechargeOrder.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_expirable(self, now: datetime, limit: int = 100) -> list[RechargeOrder]:
        result = await self._session.execute(
            select(RechargeOrder)
            .where(
                RechargeOrder.status == RechargeStatus.PENDING,
                RechargeOrder.expires_at.is_not(None),
                RechargeOrder.expires_at <= now,
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_for_user(self, user_id: UUID, limit: int = 20) -> list[RechargeOrder]:
        result = await self._session.execute(
            select(RechargeOrder)
            .where(RechargeOrder.user_id == user_id)
            .order_by(RechargeOrder.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_pending(self) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(RechargeOrder)
            .where(RechargeOrder.status == RechargeStatus.PENDING)
        )
        return int(result.scalar_one())

    async def sum_paid_today(self) -> Decimal:
        start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self._session.execute(
            select(func.coalesce(func.sum(RechargeOrder.amount), 0)).where(
                RechargeOrder.status.in_([RechargeStatus.PAID, RechargeStatus.CONFIRMED]),
                RechargeOrder.updated_at >= start_of_day,
            )
        )
        return Decimal(str(result.scalar_one()))
