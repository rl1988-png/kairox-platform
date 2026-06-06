from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"
    SUPPORT = "support"


class LedgerEntryType(StrEnum):
    RECHARGE = "recharge"
    WITHDRAW = "withdraw"
    TRADE_LOCK = "trade_lock"
    TRADE_UNLOCK = "trade_unlock"
    TRADE_PROFIT = "trade_profit"
    TRADE_LOSS = "trade_loss"
    ADMIN_ADJUSTMENT = "admin_adjustment"
    TEAM_COMMISSION = "team_commission"
    REGISTRATION_BONUS = "registration_bonus"


class TradeState(StrEnum):
    IDLE = "idle"
    PRE_STARTED = "pre_started"
    PENDING_FUNDS = "pending_funds"
    READY = "ready"
    RUNNING = "running"
    SETTLING = "settling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RechargeStatus(StrEnum):
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    PAID = "paid"
    EXPIRED = "expired"
    FAILED = "failed"


class WithdrawStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class AuditAction(StrEnum):
    WITHDRAW_APPROVE = "withdraw_approve"
    WITHDRAW_CONFIRM = "withdraw_confirm"
    WITHDRAW_FAIL = "withdraw_fail"
    WITHDRAW_REJECT = "withdraw_reject"
    USER_ROLE_CHANGE = "user_role_change"
    LEDGER_ADJUSTMENT = "ledger_adjustment"
    RECHARGE_MANUAL = "recharge_manual"
    VIP_LEVEL_ADJUST = "vip_level_adjust"


class TxVerifyVerdict(StrEnum):
    CREDIT_OK = "CREDIT_OK"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    WRONG_ADDRESS = "WRONG_ADDRESS"
    NOT_FOUND = "NOT_FOUND"
    ALREADY_USED = "ALREADY_USED"


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    INVALID_TRADE_STATE = "INVALID_TRADE_STATE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
