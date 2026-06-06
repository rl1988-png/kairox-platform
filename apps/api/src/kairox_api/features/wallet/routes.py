from fastapi import APIRouter, Depends, Request

from kairox_api.core.cookies import validate_csrf
from kairox_api.dependencies.container import (
    ServiceContainer,
    decimal_str,
    get_container,
    get_current_user,
)
from kairox_api.features.admin.schemas.admin import BindAddressRequest
from kairox_api.features.schemas import LedgerEntryPublic, WalletBalance, WalletSummary
from kairox_api.models.user import User

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("", response_model=WalletSummary)
async def get_wallet(
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> WalletSummary:
    balance = await container.ledger_repo.get_balance(user.id)
    return WalletSummary(
        user_id=user.id,
        balance=WalletBalance(
            available=decimal_str(balance.available),
            locked=decimal_str(balance.locked),
        ),
        deposit_address=user.deposit_address,
    )


@router.get("/ledger", response_model=list[LedgerEntryPublic])
async def get_ledger(
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> list[LedgerEntryPublic]:
    entries = await container.ledger_repo.list_entries(user.id)
    return [
        LedgerEntryPublic(
            id=e.id,
            entry_type=e.entry_type.value,
            amount=decimal_str(e.amount),
            balance_after=decimal_str(e.available_after),
            reference_id=e.reference_id,
            created_at=e.created_at,
        )
        for e in entries
    ]


@router.get("/deposit-info")
async def deposit_info(user: User = Depends(get_current_user)) -> dict[str, str | None]:
    from kairox_api.config.settings import settings

    return {
        "address": user.deposit_address or settings.tron_deposit_address,
        "network": "TRC20",
        "currency": "USDT",
    }


@router.post("/bind-address")
async def bind_withdraw_address(
    body: BindAddressRequest,
    request: Request,
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> dict[str, str]:
    validate_csrf(request)
    updated = await container.withdraw.bind_address(user, body.network, body.address)
    return {
        "network": updated.withdrawal_network or body.network,
        "address": updated.withdrawal_address or body.address,
    }
