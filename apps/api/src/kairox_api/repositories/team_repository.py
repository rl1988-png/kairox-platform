from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kairox_api.models.team import Team
from kairox_api.models.user import User


class TeamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_invite_code(self, invite_code: str) -> Team | None:
        result = await self._session.execute(select(Team).where(Team.invite_code == invite_code))
        return result.scalar_one_or_none()

    async def get_by_id(self, team_id: UUID) -> Team | None:
        result = await self._session.execute(select(Team).where(Team.id == team_id))
        return result.scalar_one_or_none()

    async def create(self, name: str, invite_code: str) -> Team:
        team = Team(name=name, invite_code=invite_code)
        self._session.add(team)
        await self._session.flush()
        return team

    async def list_members(self, team_id: UUID) -> list[User]:
        result = await self._session.execute(select(User).where(User.team_id == team_id))
        return list(result.scalars().all())
