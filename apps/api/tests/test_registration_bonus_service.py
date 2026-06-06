from decimal import Decimal
from uuid import uuid4

import pytest

from kairox_api.constants.enums import LedgerEntryType
from kairox_api.services.registration_bonus_service import RegistrationBonusService


class FakeLedgerRepo:
    def __init__(self) -> None:
        self.credits: list = []
        self.existing: set[tuple] = set()

    async def entry_exists(self, reference_id, reference_type):
        return (reference_id, reference_type) in self.existing

    async def credit(self, user_id, amount, entry_type, reference_id, reference_type):
        self.existing.add((reference_id, reference_type))
        self.credits.append(
            {
                "user_id": user_id,
                "amount": amount,
                "entry_type": entry_type,
            }
        )


@pytest.mark.asyncio
async def test_registration_bonus_credits_once() -> None:
    ledger = FakeLedgerRepo()
    service = RegistrationBonusService(ledger)  # type: ignore[arg-type]
    user_id = uuid4()

    assert await service.grant_if_eligible(user_id) is True
    assert await service.grant_if_eligible(user_id) is False
    assert len(ledger.credits) == 1
    assert ledger.credits[0]["amount"] == Decimal("7")
    assert ledger.credits[0]["entry_type"] == LedgerEntryType.REGISTRATION_BONUS
