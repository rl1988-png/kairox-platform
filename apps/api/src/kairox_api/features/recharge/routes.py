from uuid import UUID

from fastapi import APIRouter, Depends, Request

from kairox_api.core.cookies import validate_csrf
from kairox_api.dependencies.container import (
    ServiceContainer,
    decimal_str,
    get_container,
    get_current_user,
)
from kairox_api.features.recharge.schemas.recharge import (
    CreateRechargeOrderRequest,
    RechargeOrderPublic,
    RechargeOrderStatusPublic,
)
from kairox_api.models.recharge_order import RechargeOrder
from kairox_api.models.user import User

router = APIRouter(prefix="/recharge", tags=["recharge"])


def _to_order_public(order: RechargeOrder) -> RechargeOrderPublic:
    return RechargeOrderPublic(
        id=order.id,
        expected_amount=decimal_str(order.expected_amount),
        amount=decimal_str(order.amount),
        deposit_address=order.deposit_address or "",
        network="TRC20",
        status=order.status.value,
        tx_hash=order.tx_hash,
        confirmations=order.confirmations,
        expires_at=order.expires_at,  # type: ignore[arg-type]
        created_at=order.created_at,
    )


def _to_status_public(order: RechargeOrder) -> RechargeOrderStatusPublic:
    paid_at = order.updated_at if order.status.value in {"paid", "confirmed"} else None
    return RechargeOrderStatusPublic(
        id=order.id,
        status=order.status.value,
        tx_hash=order.tx_hash,
        confirmations=order.confirmations,
        expires_at=order.expires_at,  # type: ignore[arg-type]
        paid_at=paid_at,
    )


@router.post("/orders", response_model=RechargeOrderPublic)
async def create_recharge_order(
    body: CreateRechargeOrderRequest,
    request: Request,
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> RechargeOrderPublic:
    validate_csrf(request)
    order = await container.recharge.create_order(user, body.amount, body.network)
    return _to_order_public(order)


@router.get("/orders/{order_id}", response_model=RechargeOrderPublic)
async def get_recharge_order(
    order_id: UUID,
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> RechargeOrderPublic:
    order = await container.recharge.get_order_for_user(user.id, order_id)
    return _to_order_public(order)


@router.get("/orders/{order_id}/status", response_model=RechargeOrderStatusPublic)
async def get_recharge_order_status(
    order_id: UUID,
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> RechargeOrderStatusPublic:
    order = await container.recharge.get_order_status_for_user(user.id, order_id)
    return _to_status_public(order)
