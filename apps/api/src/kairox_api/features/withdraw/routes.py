from decimal import Decimal

from fastapi import APIRouter, Depends, Request

from kairox_api.core.cookies import validate_csrf
from kairox_api.dependencies.container import (
    ServiceContainer,
    decimal_str,
    get_container,
    get_current_user,
)
from kairox_api.features.admin.schemas.admin import CreateWithdrawRequest
from kairox_api.features.schemas import WithdrawPublic
from kairox_api.models.user import User

router = APIRouter(prefix="/withdraw", tags=["withdraw"])


@router.post("/requests", response_model=WithdrawPublic)
async def create_withdraw_request(
    body: CreateWithdrawRequest,
    request: Request,
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> WithdrawPublic:
    validate_csrf(request)
    withdrawal = await container.withdraw.create_request(user, Decimal(body.amount))
    return WithdrawPublic(
        id=withdrawal.id,
        amount=decimal_str(withdrawal.amount),
        to_address=withdrawal.to_address,
        status=withdrawal.status.value,
        tx_hash=withdrawal.tx_hash,
        confirmations=withdrawal.confirmations,
        broadcasted_at=withdrawal.broadcasted_at,
        confirmed_at=withdrawal.confirmed_at,
        failed_at=withdrawal.failed_at,
        created_at=withdrawal.created_at,
    )


@router.get("/history", response_model=list[WithdrawPublic])
async def withdraw_history(
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> list[WithdrawPublic]:
    records = await container.withdraw.list_for_user(user.id)
    return [
        WithdrawPublic(
            id=w.id,
            amount=decimal_str(w.amount),
            to_address=w.to_address,
            status=w.status.value,
            tx_hash=w.tx_hash,
            confirmations=w.confirmations,
            broadcasted_at=w.broadcasted_at,
            confirmed_at=w.confirmed_at,
            failed_at=w.failed_at,
            created_at=w.created_at,
        )
        for w in records
    ]
