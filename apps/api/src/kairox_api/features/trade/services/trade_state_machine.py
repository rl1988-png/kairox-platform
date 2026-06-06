from datetime import UTC, datetime
from decimal import Decimal

from kairox_api.constants.enums import ErrorCode, TradeState
from kairox_api.core.errors import AppError
from kairox_api.models.trade import Trade

ACTIVE_STATES = {TradeState.PRE_STARTED, TradeState.RUNNING}


def assert_no_active_trade(active: Trade | None) -> None:
    if active is not None:
        raise AppError(ErrorCode.CONFLICT, "An active trade session already exists", 409)


def apply_pre_started(trade: Trade, expires_at: datetime) -> None:
    if trade.state not in {TradeState.IDLE, TradeState.PRE_STARTED}:
        raise AppError(
            ErrorCode.INVALID_TRADE_STATE,
            f"Cannot pre-start from state {trade.state.value}",
            409,
        )
    trade.state = TradeState.PRE_STARTED
    trade.pre_started_at = datetime.now(UTC)
    trade.expires_at = expires_at


def assert_pre_start_valid(trade: Trade, now: datetime | None = None) -> None:
    current = now or datetime.now(UTC)
    if trade.state != TradeState.PRE_STARTED:
        raise AppError(
            ErrorCode.FORBIDDEN,
            "Trade must be pre-started before start",
            403,
        )
    if trade.expires_at and trade.expires_at <= current:
        raise AppError(ErrorCode.INVALID_TRADE_STATE, "Pre-start session expired", 410)


def apply_running(trade: Trade) -> None:
    assert_pre_start_valid(trade)
    trade.state = TradeState.RUNNING
    trade.started_at = datetime.now(UTC)
    trade.expires_at = None


def assert_can_complete(trade: Trade, now: datetime | None = None) -> None:
    current = now or datetime.now(UTC)
    if trade.state != TradeState.RUNNING:
        raise AppError(
            ErrorCode.INVALID_TRADE_STATE,
            "Trade is not running",
            409,
        )
    if trade.started_at is None or trade.duration_seconds is None:
        raise AppError(ErrorCode.INVALID_TRADE_STATE, "Trade runtime not configured", 409)
    elapsed = (current - trade.started_at).total_seconds()
    if elapsed < trade.duration_seconds:
        raise AppError(
            ErrorCode.INVALID_TRADE_STATE,
            "Trade runtime not finished yet",
            409,
        )


def apply_completed(trade: Trade, profit: Decimal, now: datetime | None = None) -> None:
    assert_can_complete(trade, now)
    trade.state = TradeState.COMPLETED
    trade.profit = profit
    trade.completed_at = now or datetime.now(UTC)


def apply_failed(trade: Trade) -> None:
    trade.state = TradeState.FAILED
    trade.completed_at = datetime.now(UTC)
    if trade.profit is None:
        trade.profit = Decimal("0")
