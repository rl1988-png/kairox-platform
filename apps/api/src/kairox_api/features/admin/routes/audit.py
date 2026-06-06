from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends

from kairox_api.constants.enums import AuditAction, UserRole
from kairox_api.dependencies.container import ServiceContainer, get_container, require_roles
from kairox_api.features.admin.schemas.admin import AuditListResponse, AuditLogPublic
from kairox_api.models.user import User

router = APIRouter()


@router.get("/audit", response_model=AuditListResponse)
async def list_audit(
    actor_id: UUID | None = None,
    action: str | None = None,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    page: int = 1,
    limit: int = 20,
    _staff: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPPORT)),
    container: ServiceContainer = Depends(get_container),
) -> AuditListResponse:
    parsed_action = AuditAction(action) if action else None
    entries, total = await container.admin.list_audit(
        actor_id, parsed_action, from_dt, to_dt, page, limit
    )
    items = [
        AuditLogPublic(
            id=e.id,  # type: ignore[attr-defined]
            actor_id=e.admin_user_id,  # type: ignore[attr-defined]
            action=e.action.value,  # type: ignore[attr-defined]
            target_type=e.target_type,  # type: ignore[attr-defined]
            target_id=e.target_id,  # type: ignore[attr-defined]
            ip_address=e.ip_address,  # type: ignore[attr-defined]
            user_agent=e.user_agent,  # type: ignore[attr-defined]
            payload_json=e.details,  # type: ignore[attr-defined]
            created_at=e.created_at,  # type: ignore[attr-defined]
        )
        for e in entries
    ]
    return AuditListResponse(items=items, total=total, page=page, limit=limit)
