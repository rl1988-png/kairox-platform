from decimal import Decimal
from uuid import uuid4

import pytest

from kairox_api.constants.enums import LedgerEntryType
from kairox_api.services.team_commission_service import TeamCommissionService


class FakeUser:
    def __init__(
        self,
        *,
        is_official: bool = True,
        referrer_id=None,
        team_id=None,
    ) -> None:
        self.id = uuid4()
        self.is_official = is_official
        self.referrer_id = referrer_id
        self.team_id = team_id


class FakeTrade:
    def __init__(self) -> None:
        self.id = uuid4()


class FakeUserRepo:
    def __init__(self, users: dict) -> None:
        self.users = users

    async def get_by_id(self, user_id):
        return self.users.get(user_id)

    async def get_referrer_chain(self, user_id, max_depth=3):
        chain = []
        current = self.users.get(user_id)
        while current and current.referrer_id and len(chain) < max_depth:
            chain.append(current.referrer_id)
            current = self.users.get(current.referrer_id)
        return chain


class FakeTeamEarningRepo:
    def __init__(self) -> None:
        self.created: list = []
        self.existing: set[tuple] = set()

    async def exists_for_trade(self, trade_id, beneficiary_user_id):
        return (trade_id, beneficiary_user_id) in self.existing

    async def create(self, team_id, beneficiary_user_id, source_user_id, trade_id, amount):
        self.existing.add((trade_id, beneficiary_user_id))
        self.created.append(
            {
                "team_id": team_id,
                "beneficiary_user_id": beneficiary_user_id,
                "source_user_id": source_user_id,
                "trade_id": trade_id,
                "amount": amount,
            }
        )
        return None


class FakeLedgerRepo:
    def __init__(self) -> None:
        self.credits: list = []

    async def credit(self, user_id, amount, entry_type, reference_id, reference_type):
        self.credits.append(
            {
                "user_id": user_id,
                "amount": amount,
                "entry_type": entry_type,
                "reference_id": reference_id,
                "reference_type": reference_type,
            }
        )


@pytest.mark.asyncio
async def test_commission_skips_non_official_trader() -> None:
    trader = FakeUser(is_official=False)
    service = TeamCommissionService(
        FakeUserRepo({trader.id: trader}),  # type: ignore[arg-type]
        FakeTeamEarningRepo(),  # type: ignore[arg-type]
        FakeLedgerRepo(),  # type: ignore[arg-type]
    )
    payouts = await service.distribute_trade_commission(trader, FakeTrade(), Decimal("0.15"))  # type: ignore[arg-type]
    assert payouts == []


@pytest.mark.asyncio
async def test_commission_pays_direct_referrer() -> None:
    referrer = FakeUser(team_id=uuid4())
    trader = FakeUser(is_official=True, referrer_id=referrer.id, team_id=uuid4())
    users = {trader.id: trader, referrer.id: referrer}
    earnings = FakeTeamEarningRepo()
    ledger = FakeLedgerRepo()
    service = TeamCommissionService(
        FakeUserRepo(users),  # type: ignore[arg-type]
        earnings,  # type: ignore[arg-type]
        ledger,  # type: ignore[arg-type]
    )
    trade = FakeTrade()
    payouts = await service.distribute_trade_commission(trader, trade, Decimal("0.15"))  # type: ignore[arg-type]

    assert len(payouts) == 1
    assert payouts[0]["amount"] == "0.01500000"
    assert len(earnings.created) == 1
    assert ledger.credits[0]["entry_type"] == LedgerEntryType.TEAM_COMMISSION
    assert ledger.credits[0]["amount"] == Decimal("0.01500000")


@pytest.mark.asyncio
async def test_commission_idempotent_per_trade() -> None:
    referrer = FakeUser(team_id=uuid4())
    trader = FakeUser(is_official=True, referrer_id=referrer.id, team_id=uuid4())
    users = {trader.id: trader, referrer.id: referrer}
    earnings = FakeTeamEarningRepo()
    earnings.existing.add((uuid4(), referrer.id))
    ledger = FakeLedgerRepo()
    service = TeamCommissionService(
        FakeUserRepo(users),  # type: ignore[arg-type]
        earnings,  # type: ignore[arg-type]
        ledger,  # type: ignore[arg-type]
    )
    trade = FakeTrade()
    earnings.existing = {(trade.id, referrer.id)}
    payouts = await service.distribute_trade_commission(trader, trade, Decimal("0.15"))  # type: ignore[arg-type]
    assert payouts == []
    assert ledger.credits == []
