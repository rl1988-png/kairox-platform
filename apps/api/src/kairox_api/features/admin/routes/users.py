from uuid import UUID

from fastapi import APIRouter, Depends, Request

from kairox_api.constants.enums import UserRole
from kairox_api.core.cookies import validate_csrf
from kairox_api.dependencies.container import (
    ServiceContainer,
    get_client_ip,
    get_container,
    require_roles,
)
from kairox_api.features.admin.schemas.admin import (
    AdjustVipRequest,
    AdminUserListResponse,
    AdminUserPublic,
    ManualCreditRequest,
    ManualCreditResponse,
)
from kairox_api.models.user import User

router = APIRouter()


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    search: str = "",
    page: int = 1,
    limit: int = 20,
    _staff: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPPORT)),
    container: ServiceContainer = Depends(get_container),
) -> AdminUserListResponse:
    users, total = await container.admin.list_users(search, page, limit)
    return AdminUserListResponse(
        items=[AdminUserPublic.model_validate(u) for u in users],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/users/{user_id}", response_model=AdminUserPublic)
async def get_user(
    user_id: UUID,
    _staff: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPPORT)),
    container: ServiceContainer = Depends(get_container),
) -> AdminUserPublic:
    user = await container.admin.get_user(user_id)
    return AdminUserPublic.model_validate(user)


@router.post("/users/{user_id}/manual-credit", response_model=ManualCreditResponse)
async def manual_credit(
    user_id: UUID,
    body: ManualCreditRequest,
    request: Request,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    container: ServiceContainer = Depends(get_container),
) -> ManualCreditResponse:
    validate_csrf(request)
    result = await container.admin.manual_credit(
        admin,
        user_id,
        body.amount,
        body.reason,
        body.idempotency_key,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return ManualCreditResponse(**result)


@router.post("/users/{user_id}/adjust-vip", response_model=AdminUserPublic)
async def adjust_vip(
    user_id: UUID,
    body: AdjustVipRequest,
    request: Request,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    container: ServiceContainer = Depends(get_container),
) -> AdminUserPublic:
    validate_csrf(request)
    user = await container.admin.adjust_vip(
        admin,
        user_id,
        body.vip_level,
        body.reason,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return AdminUserPublic.model_validate(user)
