from decimal import Decimal
from uuid import uuid4

import pytest

from kairox_api.constants.enums import ErrorCode
from kairox_api.core.errors import AppError
from kairox_api.repositories.exceptions import InsufficientBalanceError
from kairox_api.services.withdraw_service import WithdrawService


class FakeWithdrawRepo:
    async def create(self, user_id, amount, fee_amount, to_address):
        return type("Withdrawal", (), {"id": uuid4(), "amount": amount})()

    async def list_for_user(self, user_id):
        return []

    async def list_pending(self):
        return []

    async def get_by_id(self, request_id):
        return None

    async def get_pending_for_user(self, user_id):
        return None


class FakeLedgerRepo:
    def __init__(self) -> None:
        self.available = Decimal("500")
        self.locked = Decimal("0")

    async def get_balance(self, user_id):
        return type("Bal", (), {"available": self.available, "locked": self.locked})()

    async def lock(self, user_id, amount, entry_type, reference_id=None, reference_type=None):
        if self.available < amount:
            raise InsufficientBalanceError()
        self.available -= amount
        self.locked += amount


@pytest.mark.asyncio
async def test_withdraw_insufficient_funds() -> None:
    ledger = FakeLedgerRepo()
    ledger.available = Decimal("10")
    service = WithdrawService(FakeWithdrawRepo(), ledger)  # type: ignore[arg-type]
    user = type(
        "User",
        (),
        {
            "id": uuid4(),
            "is_official": True,
            "withdrawal_address": "T" + "a" * 33,
        },
    )()
    with pytest.raises(AppError) as exc:
        await service.create_request(user, Decimal("50"))  # type: ignore[arg-type]
    assert exc.value.code == ErrorCode.INSUFFICIENT_FUNDS
