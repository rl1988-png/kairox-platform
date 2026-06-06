from fastapi import APIRouter, Depends

from kairox_api.constants.enums import UserRole
from kairox_api.dependencies.container import (
    ServiceContainer,
    decimal_str,
    get_container,
    require_roles,
)
from kairox_api.features.admin.schemas.admin import AdminTradePublic
from kairox_api.models.user import User

router = APIRouter()


@router.get("/trades", response_model=list[AdminTradePublic])
async def list_trades(
    limit: int = 50,
    _staff: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPPORT)),
    container: ServiceContainer = Depends(get_container),
) -> list[AdminTradePublic]:
    trades = await container.admin.list_trades(limit)
    return [
        AdminTradePublic(
            id=t.id,  # type: ignore[attr-defined]
            user_id=t.user_id,  # type: ignore[attr-defined]
            state=t.state.value,  # type: ignore[attr-defined]
            vip_level=t.vip_level,  # type: ignore[attr-defined]
            amount=decimal_str(t.amount),  # type: ignore[attr-defined]
            profit=decimal_str(t.profit) if t.profit is not None else None,  # type: ignore[attr-defined]
            created_at=t.created_at,  # type: ignore[attr-defined]
        )
        for t in trades
    ]
