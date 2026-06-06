from datetime import UTC, datetime, timedelta
from uuid import UUID

from kairox_api.config.trade_levels import (
    MAX_TRADES_PER_DAY,
    PRE_START_TTL_SECONDS,
    TRADE_COOLDOWN_SECONDS,
    TRADE_LEVELS,
    calculate_profit,
    get_level,
)
from kairox_api.constants.enums import ErrorCode, LedgerEntryType, TradeState
from kairox_api.core.errors import AppError
from kairox_api.features.trade.services.trade_state_machine import (
    ACTIVE_STATES,
    apply_completed,
    apply_failed,
    apply_pre_started,
    apply_running,
    assert_no_active_trade,
    assert_pre_start_valid,
)
from kairox_api.models.trade import Trade
from kairox_api.repositories.exceptions import InsufficientBalanceError
from kairox_api.repositories.ledger_repository import LedgerRepository
from kairox_api.repositories.order_repository import TradeRepository
from kairox_api.repositories.user_repository import UserRepository
from kairox_api.services.team_commission_service import TeamCommissionService
from kairox_api.services.trial_service import TrialService


class TradeService:
    def __init__(
        self,
        trade_repo: TradeRepository,
        ledger_repo: LedgerRepository,
        user_repo: UserRepository | None = None,
        team_commission_service: TeamCommissionService | None = None,
    ) -> None:
        self._trade_repo = trade_repo
        self._ledger_repo = ledger_repo
        self._user_repo = user_repo
        self._team_commission = team_commission_service

    async def list_levels(self, user_id: UUID) -> list[dict[str, object]]:
        balance = await self._ledger_repo.get_balance(user_id)
        levels: list[dict[str, object]] = []
        for level in TRADE_LEVELS.values():
            levels.append(
                {
                    "level": level.level,
                    "name": level.name,
                    "trade_amount": str(level.trade_amount),
                    "min_balance": str(level.min_balance),
                    "profit_rate": str(level.profit_rate),
                    "duration_seconds": level.duration_seconds,
                    "available": balance.available >= level.min_balance,
                }
            )
        return levels

    async def get_active(self, user_id: UUID) -> Trade | None:
        return await self._trade_repo.get_active_for_user(user_id, ACTIVE_STATES)

    async def pre_start(self, user_id: UUID, vip_level: int) -> Trade:
        level = get_level(vip_level)
        if level is None:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Invalid VIP level", 422)

        if self._user_repo is not None:
            trader = await self._user_repo.get_by_id(user_id)
            if trader is not None:
                TrialService.assert_trial_active(trader)

        await self._enforce_daily_limit(user_id)
        await self._enforce_cooldown(user_id)

        active = await self.get_active(user_id)
        assert_no_active_trade(active)

        balance = await self._ledger_repo.get_balance(user_id)
        if balance.available < level.min_balance:
            raise AppError(
                ErrorCode.INSUFFICIENT_FUNDS,
                f"Minimum balance for {level.name} is {level.min_balance} USDT",
            )

        expires_at = datetime.now(UTC) + timedelta(seconds=PRE_START_TTL_SECONDS)
        trade = await self._trade_repo.create_pre_start(
            user_id=user_id,
            vip_level=level.level,
            amount=level.trade_amount,
            duration_seconds=level.duration_seconds,
            expires_at=expires_at,
        )
        apply_pre_started(trade, expires_at)
        return await self._trade_repo.save(trade)

    async def start(self, user_id: UUID, trade_id: UUID) -> Trade:
        trade = await self._trade_repo.get_by_id_for_user(trade_id, user_id)
        if trade is None:
            raise AppError(ErrorCode.NOT_FOUND, "Trade session not found", 404)

        if trade.state == TradeState.RUNNING:
            raise AppError(ErrorCode.CONFLICT, "Trade already started", 409)

        assert_pre_start_valid(trade)

        other_active = await self.get_active(user_id)
        if other_active is not None and other_active.id != trade.id:
            raise AppError(ErrorCode.CONFLICT, "Another trade session is already active", 409)

        try:
            await self._ledger_repo.lock(
                user_id,
                trade.amount,
                LedgerEntryType.TRADE_LOCK,
                trade.id,
                "trade",
            )
        except InsufficientBalanceError as exc:
            apply_failed(trade)
            await self._trade_repo.save(trade)
            raise AppError(ErrorCode.INSUFFICIENT_FUNDS, exc.message) from exc

        apply_running(trade)
        return await self._trade_repo.save(trade)

    async def complete(self, user_id: UUID, trade_id: UUID) -> Trade:
        trade = await self._trade_repo.get_by_id_for_user(trade_id, user_id)
        if trade is None:
            raise AppError(ErrorCode.NOT_FOUND, "Trade session not found", 404)

        level = get_level(trade.vip_level or 1)
        if level is None:
            raise AppError(ErrorCode.INTERNAL_ERROR, "Trade level configuration missing", 500)

        profit = calculate_profit(level, trade.amount)
        apply_completed(trade, profit)

        try:
            entry_type = LedgerEntryType.TRADE_PROFIT if profit >= 0 else LedgerEntryType.TRADE_LOSS
            await self._ledger_repo.release_locked_and_credit(
                user_id,
                trade.amount,
                profit,
                entry_type,
                trade.id,
                "trade",
            )
        except InsufficientBalanceError as exc:
            raise AppError(ErrorCode.INSUFFICIENT_FUNDS, exc.message) from exc

        saved = await self._trade_repo.save(trade)
        if self._team_commission is not None and self._user_repo is not None:
            trader = await self._user_repo.get_by_id(user_id)
            if trader is not None:
                await self._team_commission.distribute_trade_commission(trader, saved, profit)

        return saved

    async def _enforce_daily_limit(self, user_id: UUID) -> None:
        count = await self._trade_repo.count_completed_today(user_id)
        if count >= MAX_TRADES_PER_DAY:
            raise AppError(
                ErrorCode.FORBIDDEN,
                f"Daily trade limit reached ({MAX_TRADES_PER_DAY} per day)",
                403,
            )

    async def _enforce_cooldown(self, user_id: UUID) -> None:
        last_completed = await self._trade_repo.get_last_completed_at(user_id)
        if last_completed is None:
            return
        elapsed = (datetime.now(UTC) - last_completed).total_seconds()
        if elapsed < TRADE_COOLDOWN_SECONDS:
            raise AppError(
                ErrorCode.FORBIDDEN,
                "Trade cooldown active — too fast",
                403,
            )

    @staticmethod
    def parse_vip_level(raw: int) -> int:
        if raw < 1:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Invalid VIP level", 422)
        return raw
