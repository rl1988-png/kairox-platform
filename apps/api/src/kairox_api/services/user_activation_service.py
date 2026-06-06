from uuid import UUID

from kairox_api.config.team_rules import TEAM_VALID_MIN_DEPOSIT
from kairox_api.constants.enums import LedgerEntryType
from kairox_api.repositories.ledger_repository import LedgerRepository
from kairox_api.repositories.user_repository import UserRepository


class UserActivationService:
    """Promote trial users to official when cumulative recharge reaches the team threshold."""

    def __init__(
        self,
        user_repo: UserRepository,
        ledger_repo: LedgerRepository,
    ) -> None:
        self._user_repo = user_repo
        self._ledger_repo = ledger_repo

    async def maybe_activate_official(self, user_id: UUID) -> bool:
        user = await self._user_repo.get_by_id(user_id)
        if user is None or user.is_official:
            return False

        total_recharge = await self._ledger_repo.sum_credit_amount_by_type(
            user_id, LedgerEntryType.RECHARGE
        )
        if total_recharge < TEAM_VALID_MIN_DEPOSIT:
            return False

        user.is_official = True
        return True
