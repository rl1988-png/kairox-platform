from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WalletBalance(BaseModel):
    available: str
    locked: str
    currency: str = "USDT"


class WalletSummary(BaseModel):
    user_id: UUID
    balance: WalletBalance
    deposit_address: str | None


class LedgerEntryPublic(BaseModel):
    id: UUID
    entry_type: str
    amount: str
    balance_after: str
    reference_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StartTradeRequest(BaseModel):
    amount: str


class TradeTransitionRequest(BaseModel):
    target_state: str


class TradeSessionPublic(BaseModel):
    id: UUID
    user_id: UUID
    state: str
    amount: str
    profit: str | None
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class RechargeSubmitRequest(BaseModel):
    tx_hash: str = Field(min_length=10, max_length=128)


class RechargePublic(BaseModel):
    id: UUID
    tx_hash: str
    amount: str
    status: str
    confirmations: int
    created_at: datetime

    model_config = {"from_attributes": True}


class WithdrawRequest(BaseModel):
    amount: str
    to_address: str = Field(min_length=30, max_length=64)


class WithdrawPublic(BaseModel):
    id: UUID
    amount: str
    to_address: str
    status: str
    tx_hash: str | None = None
    confirmations: int = 0
    broadcasted_at: datetime | None = None
    confirmed_at: datetime | None = None
    failed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamSummary(BaseModel):
    id: UUID
    name: str
    member_count: int
    invite_code: str


class SupportTxVerifyRequest(BaseModel):
    tx_hash: str
    user_id: UUID | None = None
