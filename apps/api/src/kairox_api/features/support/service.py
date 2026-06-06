from kairox_api.features.recharge.services.tron_client import TronClient
from kairox_api.repositories.order_repository import RechargeRepository


class SupportService:
    def __init__(
        self,
        recharge_repo: RechargeRepository,
        tron_client: TronClient,
    ) -> None:
        self._recharge_repo = recharge_repo
        self._tron = tron_client

    async def verify_tx(
        self,
        tx_hash: str,
        deposit_address: str,
        contract_address: str,
    ) -> dict[str, object]:
        order = await self._recharge_repo.get_by_tx_hash(tx_hash)
        on_chain = await self._tron.verify_usdt_transfer(tx_hash, deposit_address, contract_address)

        return {
            "tx_hash": tx_hash,
            "found": on_chain is not None,
            "amount": str(on_chain.amount) if on_chain else None,
            "confirmations": on_chain.confirmations if on_chain else 0,
            "credited": order is not None and order.status.value == "confirmed",
        }
