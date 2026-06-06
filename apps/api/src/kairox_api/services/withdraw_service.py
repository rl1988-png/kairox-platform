from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from kairox_api.config.settings import settings
from kairox_api.config.withdraw_fees import WITHDRAW_FEE_USDT
from kairox_api.constants.enums import ErrorCode, LedgerEntryType, WithdrawStatus
from kairox_api.constants.limits import MIN_WITHDRAW_AMOUNT
from kairox_api.core.errors import AppError
from kairox_api.models.user import User
from kairox_api.models.withdraw_request import WithdrawRequest
from kairox_api.repositories.exceptions import InsufficientBalanceError
from kairox_api.repositories.ledger_repository import LedgerRepository
from kairox_api.repositories.withdraw_repository import WithdrawRepository


class WithdrawService:
    def __init__(
        self,
        withdraw_repo: WithdrawRepository,
        ledger_repo: LedgerRepository,
    ) -> None:
        self._withdraw_repo = withdraw_repo
        self._ledger_repo = ledger_repo

    async def bind_address(self, user: User, network: str, address: str) -> User:
        if user.withdrawal_address:
            raise AppError(ErrorCode.CONFLICT, "Withdrawal address already bound", 409)
        if network != "TRC20":
            raise AppError(ErrorCode.VALIDATION_ERROR, "Only TRC20 network is supported", 422)
        if len(address) != 34 or not address.startswith("T"):
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Invalid TRC20 address (must be 34 chars, start with T)",
            )

        user.withdrawal_address = address
        user.withdrawal_network = network
        return user

    async def create_request(self, user: User, amount: Decimal) -> WithdrawRequest:
        if settings.block_trial_withdraw and not user.is_official:
            raise AppError(ErrorCode.FORBIDDEN, "Withdrawals not available for trial accounts", 403)

        if amount < MIN_WITHDRAW_AMOUNT:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                f"Minimum withdrawal is {MIN_WITHDRAW_AMOUNT} USDT",
                422,
            )

        if not user.withdrawal_address:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Bind a withdrawal address first",
                422,
            )

        pending = await self._withdraw_repo.get_pending_for_user(user.id)
        if pending is not None:
            raise AppError(ErrorCode.CONFLICT, "A pending withdrawal already exists", 409)

        total_lock = amount + WITHDRAW_FEE_USDT
        balance = await self._ledger_repo.get_balance(user.id)
        if balance.available < total_lock:
            raise AppError(ErrorCode.INSUFFICIENT_FUNDS, "Insufficient withdrawable balance", 422)

        try:
            request = await self._withdraw_repo.create(
                user.id, amount, WITHDRAW_FEE_USDT, user.withdrawal_address
            )
            await self._ledger_repo.lock(
                user.id,
                total_lock,
                LedgerEntryType.WITHDRAW,
                request.id,
                "withdraw_request",
            )
        except InsufficientBalanceError as exc:
            raise AppError(ErrorCode.INSUFFICIENT_FUNDS, exc.message, 422) from exc

        return request

    async def list_for_user(self, user_id: UUID) -> list[WithdrawRequest]:
        return await self._withdraw_repo.list_for_user(user_id)

    async def list_pending(self) -> list[WithdrawRequest]:
        return await self._withdraw_repo.list_pending()

    async def list_by_status(self, status: WithdrawStatus | None) -> list[WithdrawRequest]:
        return await self._withdraw_repo.list_by_status(status)

    async def approve(
        self,
        withdrawal_id: UUID,
        admin_note: str | None = None,
        tx_hash: str | None = None,
    ) -> WithdrawRequest:
        request = await self._get_pending(withdrawal_id)
        if not tx_hash or len(tx_hash.strip()) < 10:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "TX hash is required before withdrawal can enter processing",
                422,
            )

        request.status = WithdrawStatus.PROCESSING
        request.admin_note = admin_note
        request.tx_hash = tx_hash.strip()
        request.broadcasted_at = datetime.now(UTC)
        request.confirmations = 0
        return await self._withdraw_repo.save(request)

    async def confirm(
        self,
        withdrawal_id: UUID,
        confirmations: int,
        admin_note: str | None = None,
    ) -> WithdrawRequest:
        request = await self._get_processing(withdrawal_id)
        if confirmations < settings.tron_min_confirmations:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                f"Withdrawal requires at least {settings.tron_min_confirmations} confirmations",
                422,
            )

        total = request.amount + request.fee_amount
        await self._ledger_repo.unlock(
            request.user_id,
            total,
            LedgerEntryType.WITHDRAW,
            request.id,
            "withdraw_request",
        )
        await self._ledger_repo.debit(
            request.user_id,
            total,
            LedgerEntryType.WITHDRAW,
            request.id,
            "withdraw_request",
        )

        request.status = WithdrawStatus.COMPLETED
        request.confirmations = confirmations
        request.confirmed_at = datetime.now(UTC)
        if admin_note:
            request.admin_note = admin_note
        return await self._withdraw_repo.save(request)

    async def fail(
        self,
        withdrawal_id: UUID,
        admin_note: str | None = None,
    ) -> WithdrawRequest:
        request = await self._get_processing(withdrawal_id)
        total = request.amount + request.fee_amount

        await self._ledger_repo.unlock(
            request.user_id,
            total,
            LedgerEntryType.WITHDRAW,
            request.id,
            "withdraw_request",
        )

        request.status = WithdrawStatus.FAILED
        request.admin_note = admin_note
        request.failed_at = datetime.now(UTC)
        return await self._withdraw_repo.save(request)

    async def reject(
        self,
        withdrawal_id: UUID,
        admin_note: str | None = None,
    ) -> WithdrawRequest:
        request = await self._get_pending(withdrawal_id)
        total = request.amount + request.fee_amount

        await self._ledger_repo.unlock(
            request.user_id,
            total,
            LedgerEntryType.WITHDRAW,
            request.id,
            "withdraw_request",
        )

        request.status = WithdrawStatus.REJECTED
        request.admin_note = admin_note
        return await self._withdraw_repo.save(request)

    async def _get_pending(self, withdrawal_id: UUID) -> WithdrawRequest:
        request = await self._withdraw_repo.get_by_id(withdrawal_id)
        if request is None:
            raise AppError(ErrorCode.NOT_FOUND, "Withdrawal not found", 404)
        if request.status != WithdrawStatus.PENDING:
            raise AppError(ErrorCode.CONFLICT, "Withdrawal is not pending", 409)
        return request

    async def _get_processing(self, withdrawal_id: UUID) -> WithdrawRequest:
        request = await self._withdraw_repo.get_by_id(withdrawal_id)
        if request is None:
            raise AppError(ErrorCode.NOT_FOUND, "Withdrawal not found", 404)
        if request.status != WithdrawStatus.PROCESSING:
            raise AppError(ErrorCode.CONFLICT, "Withdrawal is not processing", 409)
        if not request.tx_hash:
            raise AppError(ErrorCode.CONFLICT, "Withdrawal has no TX hash", 409)
        return request
