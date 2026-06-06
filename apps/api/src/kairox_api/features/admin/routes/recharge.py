from fastapi import APIRouter, Depends

from kairox_api.constants.enums import UserRole
from kairox_api.dependencies.container import ServiceContainer, get_container, require_roles
from kairox_api.features.admin.schemas.admin import TxVerifyResponse
from kairox_api.models.user import User

router = APIRouter()


@router.get("/recharge/verify", response_model=TxVerifyResponse)
async def verify_recharge_tx(
    tx_hash: str,
    _staff: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPPORT)),
    container: ServiceContainer = Depends(get_container),
) -> TxVerifyResponse:
    result = await container.support_verify.verify_recharge_tx(tx_hash)
    return TxVerifyResponse(**result)
