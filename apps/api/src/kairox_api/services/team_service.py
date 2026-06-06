from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kairox_api.models.team_earning import TeamEarning
from kairox_api.repositories.team_repository import TeamRepository
from kairox_api.repositories.user_repository import UserRepository


class TeamService:
    def __init__(
        self,
        team_repo: TeamRepository,
        user_repo: UserRepository,
        session: AsyncSession,
    ) -> None:
        self._team_repo = team_repo
        self._user_repo = user_repo
        self._session = session

    async def get_team_summary(self, user_id: UUID, team_id: UUID | None) -> object | None:
        if team_id is None:
            return None
        team = await self._team_repo.get_by_id(team_id)
        if team is None:
            return None
        members = await self._team_repo.list_members(team.id)
        return team, members

    async def get_stats(self, user_id: UUID, days: int = 0) -> dict[str, object]:
        since = None
        if days > 0:
            since = datetime.now(UTC) - timedelta(days=days)

        commission = await self._sum_commission(user_id, since)
        return {
            "team_register_num": await self._user_repo.count_referrals(user_id, 1)
            + await self._user_repo.count_referrals(user_id, 2)
            + await self._user_repo.count_referrals(user_id, 3),
            "team_valid_num": await self._user_repo.count_valid_referrals(user_id, 1)
            + await self._user_repo.count_valid_referrals(user_id, 2)
            + await self._user_repo.count_valid_referrals(user_id, 3),
            "team_commission": str(commission),
            "lv1_valid_num": await self._user_repo.count_valid_referrals(user_id, 1),
            "lv2_valid_num": await self._user_repo.count_valid_referrals(user_id, 2),
            "lv3_valid_num": await self._user_repo.count_valid_referrals(user_id, 3),
            "lv1_register_num": await self._user_repo.count_referrals(user_id, 1),
            "lv2_register_num": await self._user_repo.count_referrals(user_id, 2),
            "lv3_register_num": await self._user_repo.count_referrals(user_id, 3),
        }

    async def list_members(
        self, user_id: UUID, level: int, page: int = 1, limit: int = 20
    ) -> tuple[list[object], int]:
        return await self._user_repo.list_referrals_by_level(user_id, level, page, limit)

    async def list_unfinished(
        self, user_id: UUID, level: int, page: int = 1, limit: int = 20
    ) -> tuple[list[object], int]:
        return await self._user_repo.list_unfinished_referrals(user_id, level, page, limit)

    async def _sum_commission(self, user_id: UUID, since: datetime | None) -> Decimal:
        query = select(func.coalesce(func.sum(TeamEarning.amount), 0)).where(
            TeamEarning.beneficiary_user_id == user_id
        )
        if since is not None:
            query = query.where(TeamEarning.created_at >= since)
        result = await self._session.execute(query)
        return Decimal(str(result.scalar_one()))
