from decimal import Decimal

from kairox_api.config.settings import settings
from kairox_api.constants.enums import RechargeStatus, TxVerifyVerdict
from kairox_api.constants.limits import RECHARGE_AMOUNT_TOLERANCE
from kairox_api.features.recharge.services.tron_client import TronClient
from kairox_api.models.recharge_order import RechargeOrder
from kairox_api.repositories.order_repository import RechargeRepository


def _decimal_str(value: Decimal) -> str:
    return format(value.normalize(), "f")


class SupportVerifyService:
    def __init__(
        self,
        recharge_repo: RechargeRepository,
        tron_client: TronClient,
    ) -> None:
        self._recharge_repo = recharge_repo
        self._tron = tron_client

    async def verify_recharge_tx(self, tx_hash: str) -> dict[str, object]:
        deposit_address = settings.tron_deposit_address
        contract = settings.usdt_trc20_contract

        existing = await self._recharge_repo.get_by_tx_hash(tx_hash)
        if existing is not None and existing.status in {
            RechargeStatus.PAID,
            RechargeStatus.CONFIRMED,
        }:
            return self._build_response(
                tx_hash=tx_hash,
                found=True,
                amount_on_chain=_decimal_str(existing.amount),
                to_address=existing.deposit_address,
                confirmed=True,
                matches_order=True,
                matched_order_id=str(existing.id),
                verdict=TxVerifyVerdict.ALREADY_USED,
            )

        transfer = await self._tron.fetch_transfer_by_hash(tx_hash, contract)
        if transfer is None:
            return self._build_response(
                tx_hash=tx_hash, found=False, verdict=TxVerifyVerdict.NOT_FOUND
            )

        confirmed = transfer.confirmations >= settings.tron_min_confirmations
        amount_str = _decimal_str(transfer.amount)

        if not self._tron.address_matches(transfer.to_address, deposit_address):
            return self._build_response(
                tx_hash=tx_hash,
                found=True,
                amount_on_chain=amount_str,
                to_address=transfer.to_address,
                confirmed=confirmed,
                matches_order=False,
                matched_order_id=None,
                verdict=TxVerifyVerdict.WRONG_ADDRESS,
            )

        pending_match = await self._find_pending_order(transfer.amount, deposit_address)
        if pending_match is None:
            return self._build_response(
                tx_hash=tx_hash,
                found=True,
                amount_on_chain=amount_str,
                to_address=transfer.to_address,
                confirmed=confirmed,
                matches_order=False,
                matched_order_id=None,
                verdict=TxVerifyVerdict.AMOUNT_MISMATCH,
            )

        return self._build_response(
            tx_hash=tx_hash,
            found=True,
            amount_on_chain=amount_str,
            to_address=transfer.to_address,
            confirmed=confirmed,
            matches_order=True,
            matched_order_id=str(pending_match.id),
            verdict=TxVerifyVerdict.CREDIT_OK,
        )

    async def _find_pending_order(
        self, amount: Decimal, deposit_address: str
    ) -> RechargeOrder | None:
        pending = await self._recharge_repo.list_pending_active(limit=200)
        for order in pending:
            if not self._tron.address_matches(order.deposit_address or "", deposit_address):
                continue
            if abs(order.expected_amount - amount) <= RECHARGE_AMOUNT_TOLERANCE:
                return order
        return None

    def _build_response(
        self,
        *,
        tx_hash: str,
        found: bool,
        amount_on_chain: str | None = None,
        to_address: str | None = None,
        confirmed: bool = False,
        matches_order: bool = False,
        matched_order_id: str | None = None,
        verdict: TxVerifyVerdict,
    ) -> dict[str, object]:
        return {
            "tx_hash": tx_hash,
            "found": found,
            "network": "TRC20",
            "token": "USDT",
            "amount_on_chain": amount_on_chain,
            "to_address": to_address,
            "confirmed": confirmed,
            "matches_order": matches_order,
            "matched_order_id": matched_order_id,
            "verdict": verdict.value,
        }
