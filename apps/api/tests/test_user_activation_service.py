from decimal import Decimal
from uuid import uuid4

import pytest

from kairox_api.constants.enums import LedgerEntryType
from kairox_api.services.user_activation_service import UserActivationService


class FakeUser:
    def __init__(self, is_official: bool = False) -> None:
        self.id = uuid4()
        self.is_official = is_official


class FakeUserRepo:
    def __init__(self, user: FakeUser) -> None:
        self.user = user

    async def get_by_id(self, user_id):
        if user_id == self.user.id:
            return self.user
        return None


class FakeLedgerRepo:
    def __init__(self, total: Decimal) -> None:
        self.total = total

    async def sum_credit_amount_by_type(self, user_id, entry_type):
        assert entry_type == LedgerEntryType.RECHARGE
        return self.total


@pytest.mark.asyncio
async def test_activation_below_threshold() -> None:
    user = FakeUser()
    service = UserActivationService(FakeUserRepo(user), FakeLedgerRepo(Decimal("30")))  # type: ignore[arg-type]
    assert await service.maybe_activate_official(user.id) is False
    assert user.is_official is False


@pytest.mark.asyncio
async def test_activation_at_threshold() -> None:
    user = FakeUser()
    service = UserActivationService(FakeUserRepo(user), FakeLedgerRepo(Decimal("50")))  # type: ignore[arg-type]
    assert await service.maybe_activate_official(user.id) is True
    assert user.is_official is True


@pytest.mark.asyncio
async def test_activation_idempotent() -> None:
    user = FakeUser(is_official=True)
    service = UserActivationService(FakeUserRepo(user), FakeLedgerRepo(Decimal("100")))  # type: ignore[arg-type]
    assert await service.maybe_activate_official(user.id) is False
