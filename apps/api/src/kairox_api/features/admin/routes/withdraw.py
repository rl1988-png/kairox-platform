from uuid import UUID

from fastapi import APIRouter, Depends, Request

from kairox_api.constants.enums import UserRole, WithdrawStatus
from kairox_api.core.cookies import validate_csrf
from kairox_api.dependencies.container import (
    ServiceContainer,
    decimal_str,
    get_client_ip,
    get_container,
    require_roles,
)
from kairox_api.features.admin.schemas.admin import (
    AdminWithdrawPublic,
    WithdrawActionRequest,
    WithdrawConfirmRequest,
    WithdrawFailRequest,
    WithdrawRejectRequest,
)
from kairox_api.models.user import User

router = APIRouter()


def _map_withdraw(w: object) -> AdminWithdrawPublic:
    return AdminWithdrawPublic(
        id=w.id,  # type: ignore[attr-defined]
        user_id=w.user_id,  # type: ignore[attr-defined]
        amount=decimal_str(w.amount),  # type: ignore[attr-defined]
        fee_amount=decimal_str(w.fee_amount),  # type: ignore[attr-defined]
        to_address=w.to_address,  # type: ignore[attr-defined]
        status=w.status.value,  # type: ignore[attr-defined]
        admin_note=w.admin_note,  # type: ignore[attr-defined]
        tx_hash=w.tx_hash,  # type: ignore[attr-defined]
        confirmations=w.confirmations,  # type: ignore[attr-defined]
        broadcasted_at=w.broadcasted_at,  # type: ignore[attr-defined]
        confirmed_at=w.confirmed_at,  # type: ignore[attr-defined]
        failed_at=w.failed_at,  # type: ignore[attr-defined]
        created_at=w.created_at,  # type: ignore[attr-defined]
    )


@router.get("/withdraw/requests", response_model=list[AdminWithdrawPublic])
async def list_withdraw_requests(
    status: str | None = "pending",
    _staff: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPPORT)),
    container: ServiceContainer = Depends(get_container),
) -> list[AdminWithdrawPublic]:
    parsed_status = WithdrawStatus(status) if status else None
    records = await container.withdraw.list_by_status(parsed_status)
    return [_map_withdraw(w) for w in records]


@router.post("/withdraw/requests/{request_id}/approve", response_model=AdminWithdrawPublic)
async def approve_withdraw(
    request_id: UUID,
    body: WithdrawActionRequest,
    request: Request,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    container: ServiceContainer = Depends(get_container),
) -> AdminWithdrawPublic:
    validate_csrf(request)
    record = await container.admin.approve_withdraw(
        admin,
        request_id,
        body.admin_note,
        body.tx_hash,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return _map_withdraw(record)


@router.post("/withdraw/requests/{request_id}/confirm", response_model=AdminWithdrawPublic)
async def confirm_withdraw(
    request_id: UUID,
    body: WithdrawConfirmRequest,
    request: Request,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    container: ServiceContainer = Depends(get_container),
) -> AdminWithdrawPublic:
    validate_csrf(request)
    record = await container.admin.confirm_withdraw(
        admin,
        request_id,
        body.confirmations,
        body.admin_note,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return _map_withdraw(record)


@router.post("/withdraw/requests/{request_id}/fail", response_model=AdminWithdrawPublic)
async def fail_withdraw(
    request_id: UUID,
    body: WithdrawFailRequest,
    request: Request,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    container: ServiceContainer = Depends(get_container),
) -> AdminWithdrawPublic:
    validate_csrf(request)
    record = await container.admin.fail_withdraw(
        admin,
        request_id,
        body.admin_note,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return _map_withdraw(record)


@router.post("/withdraw/requests/{request_id}/reject", response_model=AdminWithdrawPublic)
async def reject_withdraw(
    request_id: UUID,
    body: WithdrawRejectRequest,
    request: Request,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    container: ServiceContainer = Depends(get_container),
) -> AdminWithdrawPublic:
    validate_csrf(request)
    record = await container.admin.reject_withdraw(
        admin,
        request_id,
        body.admin_note,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return _map_withdraw(record)
