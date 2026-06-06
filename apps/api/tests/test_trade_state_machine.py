from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from kairox_api.constants.enums import TradeState
from kairox_api.core.errors import AppError
from kairox_api.features.trade.services.trade_state_machine import (
    apply_completed,
    apply_failed,
    apply_pre_started,
    apply_running,
    assert_no_active_trade,
    assert_pre_start_valid,
)


class FakeTrade:
    def __init__(self, state=TradeState.IDLE):
        self.state = state
        self.pre_started_at = None
        self.expires_at = None
        self.started_at = None
        self.completed_at = None
        self.duration_seconds = 120
        self.profit = None


def test_assert_no_active_trade_raises() -> None:
    active = FakeTrade(TradeState.RUNNING)
    with pytest.raises(AppError):
        assert_no_active_trade(active)  # type: ignore[arg-type]


def test_apply_pre_started_sets_state() -> None:
    trade = FakeTrade()
    expires = datetime.now(UTC) + timedelta(seconds=60)
    apply_pre_started(trade, expires)  # type: ignore[arg-type]
    assert trade.state == TradeState.PRE_STARTED
    assert trade.expires_at == expires


def test_assert_pre_start_valid_rejects_wrong_state() -> None:
    trade = FakeTrade(TradeState.RUNNING)
    with pytest.raises(AppError) as exc:
        assert_pre_start_valid(trade)  # type: ignore[arg-type]
    assert exc.value.status_code == 403


def test_assert_pre_start_valid_rejects_expired() -> None:
    trade = FakeTrade(TradeState.PRE_STARTED)
    trade.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(AppError) as exc:
        assert_pre_start_valid(trade)  # type: ignore[arg-type]
    assert exc.value.status_code == 410


def test_apply_running_from_pre_started() -> None:
    trade = FakeTrade(TradeState.PRE_STARTED)
    trade.expires_at = datetime.now(UTC) + timedelta(seconds=30)
    apply_running(trade)  # type: ignore[arg-type]
    assert trade.state == TradeState.RUNNING
    assert trade.started_at is not None


def test_apply_completed_requires_runtime() -> None:
    trade = FakeTrade(TradeState.RUNNING)
    trade.started_at = datetime.now(UTC)
    trade.duration_seconds = 120
    with pytest.raises(AppError):
        apply_completed(trade, Decimal("0.15"))  # type: ignore[arg-type]


def test_apply_completed_after_runtime() -> None:
    trade = FakeTrade(TradeState.RUNNING)
    trade.started_at = datetime.now(UTC) - timedelta(seconds=130)
    trade.duration_seconds = 120
    now = datetime.now(UTC)
    apply_completed(trade, Decimal("0.15"), now=now)  # type: ignore[arg-type]
    assert trade.state == TradeState.COMPLETED
    assert trade.profit == Decimal("0.15")


def test_apply_failed() -> None:
    trade = FakeTrade(TradeState.PRE_STARTED)
    apply_failed(trade)  # type: ignore[arg-type]
    assert trade.state == TradeState.FAILED
