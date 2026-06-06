from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kairox_api.models.team_earning import TeamEarning


class TeamEarningRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_for_trade(self, trade_id: UUID, beneficiary_user_id: UUID) -> bool:
        result = await self._session.execute(
            select(TeamEarning.id).where(
                TeamEarning.trade_id == trade_id,
                TeamEarning.beneficiary_user_id == beneficiary_user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        team_id: UUID,
        beneficiary_user_id: UUID,
        source_user_id: UUID,
        trade_id: UUID,
        amount: Decimal,
    ) -> TeamEarning:
        earning = TeamEarning(
            team_id=team_id,
            beneficiary_user_id=beneficiary_user_id,
            source_user_id=source_user_id,
            trade_id=trade_id,
            amount=amount,
        )
        self._session.add(earning)
        await self._session.flush()
        return earning
