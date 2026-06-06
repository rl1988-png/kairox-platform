from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from kairox_api.constants.enums import TradeState
from kairox_api.core.errors import AppError
from kairox_api.features.trade.service import TradeService


class FakeTradeRepo:
    def __init__(self) -> None:
        self.trades: list = []
        self.completed_today = 0
        self.last_completed_at: datetime | None = None

    async def get_active_for_user(self, user_id, active_states=None):
        for trade in self.trades:
            if trade.user_id == user_id and trade.state in (active_states or set()):
                return trade
        return None

    async def create_pre_start(self, user_id, vip_level, amount, duration_seconds, expires_at):
        trade = type(
            "Trade",
            (),
            {
                "id": uuid4(),
                "user_id": user_id,
                "vip_level": vip_level,
                "amount": amount,
                "duration_seconds": duration_seconds,
                "expires_at": expires_at,
                "state": TradeState.IDLE,
                "profit": None,
                "pre_started_at": None,
                "started_at": None,
                "completed_at": None,
            },
        )()
        self.trades.append(trade)
        return trade

    async def get_by_id_for_user(self, trade_id, user_id):
        for trade in self.trades:
            if trade.id == trade_id and trade.user_id == user_id:
                return trade
        return None

    async def count_completed_today(self, user_id):
        return self.completed_today

    async def get_last_completed_at(self, user_id):
        return self.last_completed_at

    async def save(self, trade):
        if trade.state == TradeState.COMPLETED:
            self.completed_today += 1
            self.last_completed_at = trade.completed_at or datetime.now(UTC)
        return trade


class FakeLedgerRepo:
    def __init__(self) -> None:
        self.available = Decimal("1000")
        self.locked = Decimal("0")
        self.credited_profit: Decimal | None = None

    async def get_balance(self, user_id):
        return type("Bal", (), {"available": self.available, "locked": self.locked})()

    async def lock(self, user_id, amount, entry_type, reference_id=None, reference_type=None):
        self.available -= amount
        self.locked += amount

    async def release_locked_and_credit(
        self, user_id, locked_amount, profit, entry_type, reference_id=None, reference_type=None
    ):
        self.locked -= locked_amount
        self.available += locked_amount + profit
        self.credited_profit = profit


@pytest.mark.asyncio
async def test_pre_start_and_start_flow() -> None:
    repo = FakeTradeRepo()
    ledger = FakeLedgerRepo()
    service = TradeService(repo, ledger)  # type: ignore[arg-type]
    user_id = uuid4()

    trade = await service.pre_start(user_id, 1)
    assert trade.state == TradeState.PRE_STARTED
    assert trade.expires_at is not None

    running = await service.start(user_id, trade.id)
    assert running.state == TradeState.RUNNING
    assert ledger.locked == trade.amount


@pytest.mark.asyncio
async def test_start_without_pre_start_forbidden() -> None:
    repo = FakeTradeRepo()
    service = TradeService(repo, FakeLedgerRepo())  # type: ignore[arg-type]
    user_id = uuid4()
    trade = await repo.create_pre_start(
        user_id, 1, Decimal("50"), 120, datetime.now(UTC) + timedelta(seconds=60)
    )
    with pytest.raises(AppError) as exc:
        await service.start(user_id, trade.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_expired_pre_start_returns_410() -> None:
    repo = FakeTradeRepo()
    service = TradeService(repo, FakeLedgerRepo())  # type: ignore[arg-type]
    user_id = uuid4()
    trade = await service.pre_start(user_id, 1)
    trade.state = TradeState.PRE_STARTED
    trade.expires_at = datetime.now(UTC) - timedelta(seconds=1)

    with pytest.raises(AppError) as exc:
        await service.start(user_id, trade.id)
    assert exc.value.status_code == 410


@pytest.mark.asyncio
async def test_double_start_conflict() -> None:
    repo = FakeTradeRepo()
    ledger = FakeLedgerRepo()
    service = TradeService(repo, ledger)  # type: ignore[arg-type]
    user_id = uuid4()
    trade = await service.pre_start(user_id, 1)
    await service.start(user_id, trade.id)

    with pytest.raises(AppError) as exc:
        await service.start(user_id, trade.id)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_daily_limit_third_trade_rejected() -> None:
    repo = FakeTradeRepo()
    repo.completed_today = 2
    service = TradeService(repo, FakeLedgerRepo())  # type: ignore[arg-type]
    with pytest.raises(AppError) as exc:
        await service.pre_start(uuid4(), 1)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_profit_calculated_server_side() -> None:
    repo = FakeTradeRepo()
    ledger = FakeLedgerRepo()
    service = TradeService(repo, ledger)  # type: ignore[arg-type]
    user_id = uuid4()

    trade = await service.pre_start(user_id, 1)
    await service.start(user_id, trade.id)
    trade.started_at = datetime.now(UTC) - timedelta(seconds=200)

    completed = await service.complete(user_id, trade.id)
    assert completed.profit == Decimal("0.15000000")
    assert ledger.credited_profit == Decimal("0.15000000")


@pytest.mark.asyncio
async def test_bypass_direct_start_impossible_documented() -> None:
    """POST /trade/start without pre_started state must fail — fixes kairox.cc bypass."""
    repo = FakeTradeRepo()
    service = TradeService(repo, FakeLedgerRepo())  # type: ignore[arg-type]
    user_id = uuid4()
    idle_trade = await repo.create_pre_start(
        user_id, 1, Decimal("50"), 120, datetime.now(UTC) + timedelta(seconds=60)
    )
    assert idle_trade.state == TradeState.IDLE

    with pytest.raises(AppError) as exc:
        await service.start(user_id, idle_trade.id)
    assert exc.value.status_code == 403
    assert "pre-started" in exc.value.message.lower()
