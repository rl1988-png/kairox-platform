from uuid import UUID

from kairox_api.config.trial_rules import REGISTRATION_BONUS_USDT
from kairox_api.constants.enums import LedgerEntryType
from kairox_api.repositories.ledger_repository import LedgerRepository


class RegistrationBonusService:
    """One-time 7 USDT ledger credit for new registrations (idempotent)."""

    def __init__(self, ledger_repo: LedgerRepository) -> None:
        self._ledger_repo = ledger_repo

    async def grant_if_eligible(self, user_id: UUID) -> bool:
        if await self._ledger_repo.entry_exists(user_id, "registration_bonus"):
            return False

        await self._ledger_repo.credit(
            user_id,
            REGISTRATION_BONUS_USDT,
            LedgerEntryType.REGISTRATION_BONUS,
            user_id,
            "registration_bonus",
        )
        return True
