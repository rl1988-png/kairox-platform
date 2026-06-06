from fastapi import APIRouter, Depends

from kairox_api.constants.enums import UserRole
from kairox_api.dependencies.container import ServiceContainer, get_container, require_roles
from kairox_api.features.team.schemas.team import (
    TeamMemberListResponse,
    TeamMemberPublic,
    TeamStatsPublic,
    TeamSummaryPublic,
)
from kairox_api.models.user import User

router = APIRouter(prefix="/team", tags=["team"])


@router.get("", response_model=TeamSummaryPublic | None)
async def get_team(
    user: User = Depends(require_roles(UserRole.USER, UserRole.ADMIN, UserRole.SUPPORT)),
    container: ServiceContainer = Depends(get_container),
) -> TeamSummaryPublic | None:
    if user.team_id is None:
        return None
    team = await container.team_repo.get_by_id(user.team_id)
    if team is None:
        return None
    members = await container.team_repo.list_members(team.id)
    return TeamSummaryPublic(
        id=team.id,
        name=team.name,
        member_count=len(members),
        invite_code=team.invite_code,
    )


@router.get("/stats", response_model=TeamStatsPublic)
async def team_stats(
    days: int = 0,
    user: User = Depends(require_roles(UserRole.USER, UserRole.ADMIN, UserRole.SUPPORT)),
    container: ServiceContainer = Depends(get_container),
) -> TeamStatsPublic:
    stats = await container.team.get_stats(user.id, days)
    return TeamStatsPublic(**stats)


@router.get("/members", response_model=TeamMemberListResponse)
async def team_members(
    level: int = 1,
    page: int = 1,
    limit: int = 20,
    user: User = Depends(require_roles(UserRole.USER, UserRole.ADMIN, UserRole.SUPPORT)),
    container: ServiceContainer = Depends(get_container),
) -> TeamMemberListResponse:
    members, total = await container.team.list_members(user.id, level, page, limit)
    return TeamMemberListResponse(
        items=[TeamMemberPublic.model_validate(m) for m in members],
        total=total,
        page=page,
        limit=limit,
        level=level,
    )


@router.get("/unfinished", response_model=TeamMemberListResponse)
async def team_unfinished(
    level: int = 1,
    page: int = 1,
    limit: int = 20,
    user: User = Depends(require_roles(UserRole.USER, UserRole.ADMIN, UserRole.SUPPORT)),
    container: ServiceContainer = Depends(get_container),
) -> TeamMemberListResponse:
    members, total = await container.team.list_unfinished(user.id, level, page, limit)
    return TeamMemberListResponse(
        items=[TeamMemberPublic.model_validate(m) for m in members],
        total=total,
        page=page,
        limit=limit,
        level=level,
    )
