from fastapi import APIRouter

from kairox_api.features.admin.routes import ai, audit, dashboard, recharge, trades, users, withdraw

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(dashboard.router)
router.include_router(users.router)
router.include_router(recharge.router)
router.include_router(withdraw.router)
router.include_router(trades.router)
router.include_router(audit.router)
router.include_router(ai.router, prefix="/ai", tags=["admin-ai"])
