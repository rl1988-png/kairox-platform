from datetime import datetime
from decimal import Decimal
from uuid import UUID

from kairox_api.config.settings import settings
from kairox_api.constants.enums import AuditAction, ErrorCode, LedgerEntryType, UserRole
from kairox_api.core.errors import AppError
from kairox_api.models.admin_audit_log import AdminAuditLog
from kairox_api.models.trade import Trade
from kairox_api.models.user import User
from kairox_api.models.withdraw_request import WithdrawRequest
from kairox_api.repositories.audit_repository import AuditRepository
from kairox_api.repositories.ledger_repository import LedgerRepository
from kairox_api.repositories.order_repository import RechargeRepository, TradeRepository
from kairox_api.repositories.user_repository import UserRepository
from kairox_api.repositories.withdraw_repository import WithdrawRepository
from kairox_api.services.withdraw_service import WithdrawService


def _decimal_str(value: Decimal) -> str:
    return format(value.normalize(), "f")


class AdminService:
    def __init__(
        self,
        user_repo: UserRepository,
        ledger_repo: LedgerRepository,
        audit_repo: AuditRepository,
        recharge_repo: RechargeRepository,
        trade_repo: TradeRepository,
        withdraw_repo: WithdrawRepository,
        withdraw_service: WithdrawService,
    ) -> None:
        self._user_repo = user_repo
        self._ledger_repo = ledger_repo
        self._audit_repo = audit_repo
        self._recharge_repo = recharge_repo
        self._trade_repo = trade_repo
        self._withdraw_repo = withdraw_repo
        self._withdraw_service = withdraw_service

    async def get_dashboard(self) -> dict[str, object]:
        return {
            "users_total": await self._user_repo.count_all(),
            "users_active_today": await self._user_repo.count_active_today(),
            "recharge_pending": await self._recharge_repo.count_pending(),
            "recharge_paid_today": _decimal_str(await self._recharge_repo.sum_paid_today()),
            "withdraw_pending": await self._withdraw_repo.count_pending(),
            "withdraw_pending_amount": _decimal_str(await self._withdraw_repo.sum_pending_amount()),
            "trades_today": await self._trade_repo.count_today(),
            "hot_wallet_balance": settings.hot_wallet_balance,
        }

    async def list_users(
        self, search: str = "", page: int = 1, limit: int = 20
    ) -> tuple[list[User], int]:
        return await self._user_repo.search(search, page, limit)

    async def get_user(self, user_id: UUID) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise AppError(ErrorCode.NOT_FOUND, "User not found", 404)
        return user

    async def manual_credit(
        self,
        admin: User,
        target_user_id: UUID,
        amount_raw: str,
        reason: str,
        idempotency_key: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, object]:
        if admin.role != UserRole.ADMIN:
            raise AppError(ErrorCode.FORBIDDEN, "Only admins may issue manual credits", 403)

        existing = await self._audit_repo.get_idempotency(idempotency_key)
        if existing is not None:
            balance = await self._ledger_repo.get_balance(existing.target_user_id)
            return {
                "idempotent": True,
                "user_id": str(existing.target_user_id),
                "available_balance": _decimal_str(balance.available),
            }

        try:
            amount = Decimal(amount_raw)
        except Exception as exc:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Invalid amount", 422) from exc

        if amount <= 0:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Amount must be positive", 422)
        if len(reason.strip()) < 10:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Reason must be at least 10 characters", 422)

        target = await self.get_user(target_user_id)
        await self._ledger_repo.credit(
            target.id,
            amount,
            LedgerEntryType.ADMIN_ADJUSTMENT,
            target.id,
            "manual_credit",
        )
        audit = await self._audit_repo.log(
            admin_user_id=admin.id,
            action=AuditAction.LEDGER_ADJUSTMENT,
            target_type="user",
            target_id=target.id,
            details={"amount": str(amount), "reason": reason, "idempotency_key": idempotency_key},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self._audit_repo.save_idempotency(idempotency_key, admin.id, target.id, audit.id)
        balance = await self._ledger_repo.get_balance(target.id)
        return {
            "idempotent": False,
            "user_id": str(target.id),
            "amount": _decimal_str(amount),
            "available_balance": _decimal_str(balance.available),
        }

    async def adjust_vip(
        self,
        admin: User,
        target_user_id: UUID,
        vip_level: int,
        reason: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        if admin.role != UserRole.ADMIN:
            raise AppError(ErrorCode.FORBIDDEN, "Only admins may adjust VIP level", 403)
        if vip_level < 1 or vip_level > 10:
            raise AppError(ErrorCode.VALIDATION_ERROR, "VIP level must be between 1 and 10", 422)
        if len(reason.strip()) < 10:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Reason must be at least 10 characters", 422)

        target = await self.get_user(target_user_id)
        previous = target.vip_level
        target.vip_level = vip_level
        await self._audit_repo.log(
            admin_user_id=admin.id,
            action=AuditAction.VIP_LEVEL_ADJUST,
            target_type="user",
            target_id=target.id,
            details={"previous": previous, "vip_level": vip_level, "reason": reason},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return target

    async def approve_withdraw(
        self,
        admin: User,
        request_id: UUID,
        admin_note: str | None = None,
        tx_hash: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> WithdrawRequest:
        if admin.role != UserRole.ADMIN:
            raise AppError(ErrorCode.FORBIDDEN, "Only admins may approve withdrawals", 403)

        request = await self._withdraw_service.approve(request_id, admin_note, tx_hash)
        await self._audit_repo.log(
            admin_user_id=admin.id,
            action=AuditAction.WITHDRAW_APPROVE,
            target_type="withdraw_request",
            target_id=request.id,
            details={"admin_note": admin_note, "tx_hash": tx_hash},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return request

    async def confirm_withdraw(
        self,
        admin: User,
        request_id: UUID,
        confirmations: int,
        admin_note: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> WithdrawRequest:
        if admin.role != UserRole.ADMIN:
            raise AppError(ErrorCode.FORBIDDEN, "Only admins may confirm withdrawals", 403)

        request = await self._withdraw_service.confirm(request_id, confirmations, admin_note)
        await self._audit_repo.log(
            admin_user_id=admin.id,
            action=AuditAction.WITHDRAW_CONFIRM,
            target_type="withdraw_request",
            target_id=request.id,
            details={
                "admin_note": admin_note,
                "tx_hash": request.tx_hash,
                "confirmations": confirmations,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return request

    async def fail_withdraw(
        self,
        admin: User,
        request_id: UUID,
        admin_note: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> WithdrawRequest:
        if admin.role != UserRole.ADMIN:
            raise AppError(ErrorCode.FORBIDDEN, "Only admins may fail withdrawals", 403)

        request = await self._withdraw_service.fail(request_id, admin_note)
        await self._audit_repo.log(
            admin_user_id=admin.id,
            action=AuditAction.WITHDRAW_FAIL,
            target_type="withdraw_request",
            target_id=request.id,
            details={"admin_note": admin_note, "tx_hash": request.tx_hash},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return request

    async def reject_withdraw(
        self,
        admin: User,
        request_id: UUID,
        admin_note: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> WithdrawRequest:
        if admin.role != UserRole.ADMIN:
            raise AppError(ErrorCode.FORBIDDEN, "Only admins may reject withdrawals", 403)

        request = await self._withdraw_service.reject(request_id, admin_note)
        await self._audit_repo.log(
            admin_user_id=admin.id,
            action=AuditAction.WITHDRAW_REJECT,
            target_type="withdraw_request",
            target_id=request.id,
            details={"admin_note": admin_note},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return request

    async def list_audit(
        self,
        actor_id: UUID | None = None,
        action: AuditAction | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[AdminAuditLog], int]:
        entries, total = await self._audit_repo.list_entries(
            actor_id, action, from_dt, to_dt, page, limit
        )
        return entries, total

    async def list_trades(self, limit: int = 50) -> list[Trade]:
        return await self._trade_repo.list_recent(limit)
