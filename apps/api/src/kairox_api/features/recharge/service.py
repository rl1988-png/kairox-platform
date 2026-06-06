from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID

from kairox_api.config.settings import settings
from kairox_api.constants.enums import ErrorCode, LedgerEntryType, RechargeStatus
from kairox_api.constants.limits import (
    MIN_RECHARGE_AMOUNT,
    RECHARGE_AMOUNT_TOLERANCE,
    RECHARGE_ORDER_TTL_SECONDS,
)
from kairox_api.core.errors import AppError
from kairox_api.features.recharge.services.tron_client import TronClient, TronTransferInfo
from kairox_api.models.recharge_order import RechargeOrder
from kairox_api.models.user import User
from kairox_api.repositories.ledger_repository import LedgerRepository
from kairox_api.repositories.order_repository import RechargeRepository
from kairox_api.services.user_activation_service import UserActivationService


class RechargeService:
    def __init__(
        self,
        recharge_repo: RechargeRepository,
        ledger_repo: LedgerRepository,
        tron_client: TronClient,
        activation_service: UserActivationService | None = None,
    ) -> None:
        self._recharge_repo = recharge_repo
        self._ledger_repo = ledger_repo
        self._tron = tron_client
        self._activation = activation_service

    async def create_order(self, user: User, amount_raw: str, network: str) -> RechargeOrder:
        if network != "TRC20":
            raise AppError(ErrorCode.VALIDATION_ERROR, "Only TRC20 network is supported", 422)

        amount = self._parse_amount(amount_raw)
        if amount < MIN_RECHARGE_AMOUNT:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                f"Minimum recharge amount is {MIN_RECHARGE_AMOUNT} USDT",
                422,
            )

        deposit_address = user.deposit_address or settings.tron_deposit_address
        if not deposit_address:
            raise AppError(
                ErrorCode.INTERNAL_ERROR,
                "Deposit address is not configured",
                503,
            )

        expires_at = datetime.now(UTC) + timedelta(seconds=RECHARGE_ORDER_TTL_SECONDS)
        return await self._recharge_repo.create_order(
            user_id=user.id,
            expected_amount=amount,
            deposit_address=deposit_address,
            expires_at=expires_at,
        )

    async def get_order_for_user(self, user_id: UUID, order_id: UUID) -> RechargeOrder:
        order = await self._recharge_repo.get_by_id_for_user(order_id, user_id)
        if order is None:
            raise AppError(ErrorCode.NOT_FOUND, "Recharge order not found", 404)
        return order

    async def get_order_status_for_user(self, user_id: UUID, order_id: UUID) -> RechargeOrder:
        return await self.get_order_for_user(user_id, order_id)

    async def verify_tx_for_support(self, tx_hash: str) -> dict[str, object]:
        deposit_address = settings.tron_deposit_address
        transfer = await self._tron.verify_usdt_transfer(
            tx_hash,
            deposit_address,
            settings.usdt_trc20_contract,
        )
        existing = await self._recharge_repo.get_by_tx_hash(tx_hash)
        credited = existing is not None and existing.status in {
            RechargeStatus.PAID,
            RechargeStatus.CONFIRMED,
        }
        return {
            "tx_hash": tx_hash,
            "found": transfer is not None,
            "amount": str(transfer.amount) if transfer else None,
            "to_address": transfer.to_address if transfer else None,
            "confirmations": transfer.confirmations if transfer else 0,
            "contract_match": transfer is not None,
            "credited": credited,
        }

    async def run_watcher_cycle(self) -> None:
        await self._expire_stale_orders()
        pending = await self._recharge_repo.list_pending_active()
        if not pending:
            return

        addresses = {order.deposit_address for order in pending if order.deposit_address}
        for address in addresses:
            address_orders = [o for o in pending if o.deposit_address == address]
            min_ts = min(int(o.created_at.timestamp() * 1000) for o in address_orders)
            transfers = await self._tron.list_incoming_usdt_transfers(
                address,
                settings.usdt_trc20_contract,
                min_ts,
            )
            for order in address_orders:
                if order.status != RechargeStatus.PENDING:
                    continue
                for transfer in transfers:
                    if await self._try_match_transfer(order, transfer):
                        break

        confirming = await self._recharge_repo.list_confirming()
        for order in confirming:
            if not order.tx_hash:
                continue
            transfer = await self._tron.verify_usdt_transfer(
                order.tx_hash,
                order.deposit_address or "",
                settings.usdt_trc20_contract,
                order.expected_amount,
            )
            if transfer is None:
                continue
            order.confirmations = transfer.confirmations
            if transfer.confirmations >= settings.tron_min_confirmations:
                await self._credit_order(order, transfer.amount)

    async def _try_match_transfer(self, order: RechargeOrder, transfer: TronTransferInfo) -> bool:
        if order.expires_at and datetime.now(UTC) > order.expires_at:
            return False
        if not self._amount_within_tolerance(order.expected_amount, transfer.amount):
            return False

        existing = await self._recharge_repo.get_by_tx_hash(transfer.tx_hash)
        if existing is not None:
            return False

        order.tx_hash = transfer.tx_hash
        order.amount = transfer.amount
        order.confirmations = transfer.confirmations

        if transfer.confirmations >= settings.tron_min_confirmations:
            await self._credit_order(order, transfer.amount)
        else:
            order.status = RechargeStatus.CONFIRMING
        return True

    async def _credit_order(self, order: RechargeOrder, amount: Decimal) -> None:
        if order.status in {RechargeStatus.PAID, RechargeStatus.CONFIRMED}:
            return

        if await self._ledger_repo.entry_exists(order.id, "recharge_order"):
            order.status = RechargeStatus.PAID
            return

        await self._ledger_repo.credit(
            order.user_id,
            amount,
            LedgerEntryType.RECHARGE,
            order.id,
            "recharge_order",
        )
        order.amount = amount
        order.status = RechargeStatus.PAID
        if self._activation is not None:
            await self._activation.maybe_activate_official(order.user_id)

    async def _expire_stale_orders(self) -> None:
        now = datetime.now(UTC)
        stale = await self._recharge_repo.list_expirable(now)
        for order in stale:
            order.status = RechargeStatus.EXPIRED

    @staticmethod
    def _parse_amount(raw: str) -> Decimal:
        try:
            amount = Decimal(raw)
        except InvalidOperation as exc:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Invalid amount", 422) from exc
        if amount <= 0:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Amount must be positive", 422)
        return amount

    @staticmethod
    def _amount_within_tolerance(expected: Decimal, actual: Decimal) -> bool:
        return abs(actual - expected) <= RECHARGE_AMOUNT_TOLERANCE
