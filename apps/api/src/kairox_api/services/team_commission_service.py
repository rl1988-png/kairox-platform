from decimal import Decimal

from kairox_api.config.team_rules import MONEY_QUANTIZE, TEAM_COMMISSION_RATES
from kairox_api.constants.enums import LedgerEntryType
from kairox_api.models.trade import Trade
from kairox_api.models.user import User
from kairox_api.repositories.ledger_repository import LedgerRepository
from kairox_api.repositories.team_earning_repository import TeamEarningRepository
from kairox_api.repositories.user_repository import UserRepository


class TeamCommissionService:
    """Pay multi-level referral commission when an official user completes a profitable trade."""

    def __init__(
        self,
        user_repo: UserRepository,
        team_earning_repo: TeamEarningRepository,
        ledger_repo: LedgerRepository,
    ) -> None:
        self._user_repo = user_repo
        self._team_earning_repo = team_earning_repo
        self._ledger_repo = ledger_repo

    async def distribute_trade_commission(
        self,
        trader: User,
        trade: Trade,
        profit: Decimal,
    ) -> list[dict[str, str]]:
        if profit <= 0 or not trader.is_official:
            return []

        referrers = await self._user_repo.get_referrer_chain(trader.id, max_depth=3)
        payouts: list[dict[str, str]] = []

        for level, beneficiary_id in enumerate(referrers, start=1):
            rate = TEAM_COMMISSION_RATES.get(level)
            if rate is None:
                continue

            amount = (profit * rate).quantize(MONEY_QUANTIZE)
            if amount <= 0:
                continue

            if await self._team_earning_repo.exists_for_trade(trade.id, beneficiary_id):
                continue

            beneficiary = await self._user_repo.get_by_id(beneficiary_id)
            if beneficiary is None or beneficiary.team_id is None:
                continue

            await self._team_earning_repo.create(
                team_id=beneficiary.team_id,
                beneficiary_user_id=beneficiary_id,
                source_user_id=trader.id,
                trade_id=trade.id,
                amount=amount,
            )
            await self._ledger_repo.credit(
                beneficiary_id,
                amount,
                LedgerEntryType.TEAM_COMMISSION,
                trade.id,
                "team_commission",
            )
            payouts.append(
                {
                    "level": str(level),
                    "beneficiary_user_id": str(beneficiary_id),
                    "amount": format(amount, "f"),
                }
            )

        return payouts
