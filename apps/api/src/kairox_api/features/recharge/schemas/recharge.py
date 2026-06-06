from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateRechargeOrderRequest(BaseModel):
    amount: str = Field(min_length=1, max_length=32)
    network: str = Field(default="TRC20", pattern=r"^TRC20$")


class RechargeOrderPublic(BaseModel):
    id: UUID
    expected_amount: str
    amount: str
    deposit_address: str
    network: str = "TRC20"
    status: str
    tx_hash: str | None
    confirmations: int
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class RechargeOrderStatusPublic(BaseModel):
    id: UUID
    status: str
    tx_hash: str | None
    confirmations: int
    expires_at: datetime
    paid_at: datetime | None = None


class RechargeVerifyPublic(BaseModel):
    tx_hash: str
    found: bool
    amount: str | None
    to_address: str | None
    confirmations: int
    contract_match: bool
    credited: bool
