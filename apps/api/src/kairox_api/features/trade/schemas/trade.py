from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PreStartTradeRequest(BaseModel):
    vip_level: int = Field(ge=1, le=10)


class StartTradeRequest(BaseModel):
    trade_id: UUID


class CompleteTradeRequest(BaseModel):
    trade_id: UUID


class TradeLevelPublic(BaseModel):
    level: int
    name: str
    trade_amount: str
    min_balance: str
    profit_rate: str
    duration_seconds: int
    available: bool


class TradeSessionPublic(BaseModel):
    id: UUID
    user_id: UUID
    state: str
    vip_level: int | None
    amount: str
    profit: str | None
    expires_at: datetime | None
    duration_seconds: int | None
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}
