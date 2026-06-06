from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AdminDashboardResponse(BaseModel):
    users_total: int
    users_active_today: int
    recharge_pending: int
    recharge_paid_today: str
    withdraw_pending: int
    withdraw_pending_amount: str
    trades_today: int
    hot_wallet_balance: str


class AdminUserPublic(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    vip_level: int
    is_official: bool
    is_active: bool
    withdrawal_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    items: list[AdminUserPublic]
    total: int
    page: int
    limit: int


class ManualCreditRequest(BaseModel):
    amount: str = Field(min_length=1, max_length=32)
    reason: str = Field(min_length=10, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=128)


class ManualCreditResponse(BaseModel):
    idempotent: bool
    user_id: str
    amount: str | None = None
    available_balance: str


class AdjustVipRequest(BaseModel):
    vip_level: int = Field(ge=1, le=10)
    reason: str = Field(min_length=10, max_length=500)


class WithdrawActionRequest(BaseModel):
    admin_note: str | None = Field(default=None, max_length=500)
    tx_hash: str = Field(min_length=10, max_length=128)


class WithdrawConfirmRequest(BaseModel):
    confirmations: int = Field(ge=0)
    admin_note: str | None = Field(default=None, max_length=500)


class WithdrawFailRequest(BaseModel):
    admin_note: str | None = Field(default=None, max_length=500)


class WithdrawRejectRequest(BaseModel):
    admin_note: str | None = Field(default=None, max_length=500)


class AdminWithdrawPublic(BaseModel):
    id: UUID
    user_id: UUID
    amount: str
    fee_amount: str
    to_address: str
    status: str
    admin_note: str | None
    tx_hash: str | None
    confirmations: int
    broadcasted_at: datetime | None
    confirmed_at: datetime | None
    failed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TxVerifyResponse(BaseModel):
    tx_hash: str
    found: bool
    network: str
    token: str
    amount_on_chain: str | None
    to_address: str | None
    confirmed: bool
    matches_order: bool
    matched_order_id: str | None
    verdict: str


class AuditLogPublic(BaseModel):
    id: UUID
    actor_id: UUID
    action: str
    target_type: str
    target_id: UUID | None
    ip_address: str | None
    user_agent: str | None
    payload_json: dict[str, object] | None
    created_at: datetime


class AuditListResponse(BaseModel):
    items: list[AuditLogPublic]
    total: int
    page: int
    limit: int


class AdminTradePublic(BaseModel):
    id: UUID
    user_id: UUID
    state: str
    vip_level: int | None
    amount: str
    profit: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BindAddressRequest(BaseModel):
    network: str = Field(default="TRC20", pattern=r"^TRC20$")
    address: str = Field(min_length=30, max_length=64)


class CreateWithdrawRequest(BaseModel):
    amount: str = Field(min_length=1, max_length=32)
