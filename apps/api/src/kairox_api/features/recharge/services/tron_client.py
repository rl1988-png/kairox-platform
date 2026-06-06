from dataclasses import dataclass
from decimal import Decimal

import httpx

from kairox_api.config.settings import settings

USDT_DECIMALS = Decimal("1000000")


@dataclass
class TronTransferInfo:
    tx_hash: str
    amount: Decimal
    confirmations: int
    from_address: str
    to_address: str
    block_timestamp: int


class TronClient:
    """TronGrid client for TRC20 USDT verification — mockable in tests."""

    BASE_URL = "https://api.trongrid.io"

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key or settings.trongrid_api_key

    def _headers(self) -> dict[str, str]:
        if self._api_key:
            return {"TRON-PRO-API-KEY": self._api_key}
        return {}

    async def verify_usdt_transfer(
        self,
        tx_hash: str,
        expected_to: str,
        contract_address: str,
        expected_amount: Decimal | None = None,
    ) -> TronTransferInfo | None:
        transfer = await self._fetch_transfer_by_hash(tx_hash, contract_address)
        if transfer is None:
            return None
        if not self._address_matches(transfer.to_address, expected_to):
            return None
        if expected_amount is not None and not self._amount_within_tolerance(
            expected_amount, transfer.amount
        ):
            return None
        return transfer

    async def list_incoming_usdt_transfers(
        self,
        to_address: str,
        contract_address: str,
        min_timestamp_ms: int,
        limit: int = 50,
    ) -> list[TronTransferInfo]:
        if not to_address:
            return []

        params = {
            "contract_address": contract_address,
            "only_to": "true",
            "limit": limit,
            "min_timestamp": min_timestamp_ms,
            "order_by": "block_timestamp,desc",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/v1/accounts/{to_address}/transactions/trc20",
                headers=self._headers(),
                params=params,
            )
            if response.status_code != 200:
                return []

            payload = response.json()
            transfers: list[TronTransferInfo] = []
            for item in payload.get("data", []):
                parsed = self._parse_trc20_item(item, contract_address)
                if parsed is not None:
                    transfers.append(parsed)
            return transfers

    async def fetch_transfer_by_hash(
        self, tx_hash: str, contract_address: str
    ) -> TronTransferInfo | None:
        return await self._fetch_transfer_by_hash(tx_hash, contract_address)

    @staticmethod
    def address_matches(actual: str, expected: str) -> bool:
        return TronClient._address_matches(actual, expected)

    async def _fetch_transfer_by_hash(
        self, tx_hash: str, contract_address: str
    ) -> TronTransferInfo | None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/v1/transactions/{tx_hash}/events",
                headers=self._headers(),
            )
            if response.status_code != 200:
                return None

            payload = response.json()
            events = payload.get("data", payload if isinstance(payload, list) else [])
            for event in events:
                if event.get("event_name") != "Transfer":
                    continue
                if event.get("contract_address") != contract_address:
                    continue
                result = event.get("result", {})
                to_address = result.get("to", result.get("1", ""))
                from_address = result.get("from", result.get("0", ""))
                value_raw = result.get("value", result.get("2", "0"))
                amount = Decimal(str(value_raw)) / USDT_DECIMALS
                confirmations = int(event.get("confirmations", 0))
                block_ts = int(event.get("block_timestamp", 0))
                return TronTransferInfo(
                    tx_hash=tx_hash,
                    amount=amount,
                    confirmations=confirmations,
                    from_address=from_address,
                    to_address=to_address,
                    block_timestamp=block_ts,
                )
        return None

    def _parse_trc20_item(
        self, item: dict[str, object], contract_address: str
    ) -> TronTransferInfo | None:
        token_info = item.get("token_info", {})
        if token_info.get("address") != contract_address:
            return None
        tx_hash = str(item.get("transaction_id", ""))
        if not tx_hash:
            return None
        value_raw = item.get("value", "0")
        amount = Decimal(str(value_raw)) / USDT_DECIMALS
        return TronTransferInfo(
            tx_hash=tx_hash,
            amount=amount,
            confirmations=int(item.get("confirmations", 0)),
            from_address=str(item.get("from", "")),
            to_address=str(item.get("to", "")),
            block_timestamp=int(item.get("block_timestamp", 0)),
        )

    @staticmethod
    def _address_matches(actual: str, expected: str) -> bool:
        return actual == expected or actual.lower() == expected.lower()

    @staticmethod
    def _amount_within_tolerance(expected: Decimal, actual: Decimal) -> bool:
        from kairox_api.constants.limits import RECHARGE_AMOUNT_TOLERANCE

        return abs(actual - expected) <= RECHARGE_AMOUNT_TOLERANCE
