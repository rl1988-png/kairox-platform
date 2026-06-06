from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TeamSummaryPublic(BaseModel):
    id: UUID
    name: str
    member_count: int
    invite_code: str


class TeamStatsPublic(BaseModel):
    team_register_num: int
    team_valid_num: int
    team_commission: str
    lv1_valid_num: int
    lv2_valid_num: int
    lv3_valid_num: int
    lv1_register_num: int
    lv2_register_num: int
    lv3_register_num: int


class TeamMemberPublic(BaseModel):
    id: UUID
    username: str
    is_official: bool
    vip_level: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamMemberListResponse(BaseModel):
    items: list[TeamMemberPublic]
    total: int
    page: int
    limit: int
    level: int
