from fastapi import APIRouter, Depends

from kairox_api.constants.enums import UserRole
from kairox_api.dependencies.container import ServiceContainer, get_container, require_roles
from kairox_api.features.admin.schemas.admin import AdminDashboardResponse
from kairox_api.models.user import User

router = APIRouter()


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def admin_dashboard(
    _staff: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPPORT)),
    container: ServiceContainer = Depends(get_container),
) -> AdminDashboardResponse:
    data = await container.admin.get_dashboard()
    return AdminDashboardResponse(**data)
