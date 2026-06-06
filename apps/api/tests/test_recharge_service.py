from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from kairox_api.constants.enums import ErrorCode, RechargeStatus
from kairox_api.core.errors import AppError
from kairox_api.features.recharge.service import RechargeService
from kairox_api.features.recharge.services.tron_client import TronTransferInfo


class FakeRechargeRepo:
    def __init__(self) -> None:
        self.orders: dict = {}

    async def create_order(self, user_id, expected_amount, deposit_address, expires_at):
        order = type(
            "Order",
            (),
            {
                "id": uuid4(),
                "user_id": user_id,
                "expected_amount": expected_amount,
                "amount": expected_amount,
                "deposit_address": deposit_address,
                "expires_at": expires_at,
                "status": RechargeStatus.PENDING,
                "tx_hash": None,
                "confirmations": 0,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
        )()
        self.orders[order.id] = order
        return order

    async def get_by_id_for_user(self, order_id, user_id):
        order = self.orders.get(order_id)
        if order and order.user_id == user_id:
            return order
        return None

    async def get_by_tx_hash(self, tx_hash):
        for order in self.orders.values():
            if order.tx_hash == tx_hash:
                return order
        return None

    async def list_pending_active(self, limit=100):
        now = datetime.now(UTC)
        return [
            o
            for o in self.orders.values()
            if o.status == RechargeStatus.PENDING and o.expires_at and o.expires_at > now
        ]

    async def list_confirming(self, limit=100):
        return [o for o in self.orders.values() if o.status == RechargeStatus.CONFIRMING]

    async def list_expirable(self, now, limit=100):
        return [
            o
            for o in self.orders.values()
            if o.status == RechargeStatus.PENDING and o.expires_at and o.expires_at <= now
        ]


class FakeLedgerRepo:
    def __init__(self) -> None:
        self.entries: list = []

    async def entry_exists(self, reference_id, reference_type):
        return any(
            e["reference_id"] == reference_id and e["reference_type"] == reference_type
            for e in self.entries
        )

    async def credit(self, user_id, amount, entry_type, reference_id, reference_type):
        self.entries.append(
            {
                "user_id": user_id,
                "amount": amount,
                "reference_id": reference_id,
                "reference_type": reference_type,
            }
        )


class FakeTronClient:
    def __init__(self, transfers=None):
        self.transfers = transfers or []
        self.verify_result = None

    async def list_incoming_usdt_transfers(
        self, to_address, contract_address, min_timestamp_ms, limit=50
    ):
        return self.transfers

    async def verify_usdt_transfer(
        self, tx_hash, expected_to, contract_address, expected_amount=None
    ):
        return self.verify_result


class FakeUser:
    def __init__(self, deposit_address=None):
        self.id = uuid4()
        self.deposit_address = deposit_address


@pytest.mark.asyncio
async def test_create_order_min_amount(monkeypatch) -> None:
    monkeypatch.setattr(
        "kairox_api.features.recharge.service.settings.tron_deposit_address",
        "TDepositAddress123456789012345678901",
    )
    service = RechargeService(FakeRechargeRepo(), FakeLedgerRepo(), FakeTronClient())
    with pytest.raises(AppError) as exc:
        await service.create_order(FakeUser(), "10", "TRC20")
    assert exc.value.code == ErrorCode.VALIDATION_ERROR


@pytest.mark.asyncio
async def test_create_order_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "kairox_api.features.recharge.service.settings.tron_deposit_address",
        "TDepositAddress123456789012345678901",
    )
    service = RechargeService(FakeRechargeRepo(), FakeLedgerRepo(), FakeTronClient())
    order = await service.create_order(FakeUser(), "50", "TRC20")
    assert order.expected_amount == Decimal("50")
    assert order.status == RechargeStatus.PENDING
    assert order.expires_at > datetime.now(UTC)


@pytest.mark.asyncio
async def test_get_order_idor_protection() -> None:
    repo = FakeRechargeRepo()
    service = RechargeService(repo, FakeLedgerRepo(), FakeTronClient())
    user = FakeUser(deposit_address="TAddr")
    order = await service.create_order(user, "30", "TRC20")
    with pytest.raises(AppError) as exc:
        await service.get_order_for_user(uuid4(), order.id)
    assert exc.value.code == ErrorCode.NOT_FOUND


@pytest.mark.asyncio
async def test_watcher_credits_matching_transfer(monkeypatch) -> None:
    monkeypatch.setattr(
        "kairox_api.features.recharge.service.settings.tron_min_confirmations",
        1,
    )
    monkeypatch.setattr(
        "kairox_api.features.recharge.service.settings.usdt_trc20_contract",
        "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    )

    repo = FakeRechargeRepo()
    ledger = FakeLedgerRepo()
    user = FakeUser(deposit_address="TDepositAddress123456789012345678901")
    monkeypatch.setattr(
        "kairox_api.features.recharge.service.settings.tron_deposit_address",
        user.deposit_address,
    )
    service = RechargeService(repo, ledger, FakeTronClient())
    order = await service.create_order(user, "30", "TRC20")

    transfer = TronTransferInfo(
        tx_hash="abc123txhash",
        amount=Decimal("30"),
        confirmations=19,
        from_address="TSender",
        to_address=user.deposit_address,
        block_timestamp=int(datetime.now(UTC).timestamp() * 1000),
    )
    service._tron.transfers = [transfer]  # type: ignore[attr-defined]

    await service.run_watcher_cycle()

    updated = repo.orders[order.id]
    assert updated.status == RechargeStatus.PAID
    assert updated.tx_hash == "abc123txhash"
    assert len(ledger.entries) == 1


@pytest.mark.asyncio
async def test_watcher_rejects_replay_tx_hash(monkeypatch) -> None:
    monkeypatch.setattr("kairox_api.features.recharge.service.settings.tron_min_confirmations", 1)
    repo = FakeRechargeRepo()
    user = FakeUser(deposit_address="TDepositAddress123456789012345678901")
    monkeypatch.setattr(
        "kairox_api.features.recharge.service.settings.tron_deposit_address",
        user.deposit_address,
    )
    service = RechargeService(repo, FakeLedgerRepo(), FakeTronClient())
    order1 = await service.create_order(user, "30", "TRC20")
    order2 = await service.create_order(user, "30", "TRC20")
    order1.tx_hash = "reused-tx"
    order1.status = RechargeStatus.PAID

    transfer = TronTransferInfo(
        tx_hash="reused-tx",
        amount=Decimal("30"),
        confirmations=19,
        from_address="TSender",
        to_address=user.deposit_address,
        block_timestamp=int(datetime.now(UTC).timestamp() * 1000),
    )
    service._tron.transfers = [transfer]  # type: ignore[attr-defined]
    await service.run_watcher_cycle()
    assert repo.orders[order2.id].status == RechargeStatus.PENDING


@pytest.mark.asyncio
async def test_watcher_expires_stale_orders() -> None:
    repo = FakeRechargeRepo()
    user = FakeUser(deposit_address="TDepositAddress123456789012345678901")
    service = RechargeService(repo, FakeLedgerRepo(), FakeTronClient())
    order = await service.create_order(user, "30", "TRC20")
    order.expires_at = datetime.now(UTC) - timedelta(minutes=1)

    await service.run_watcher_cycle()
    assert repo.orders[order.id].status == RechargeStatus.EXPIRED
