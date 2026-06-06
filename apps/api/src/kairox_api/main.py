import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from kairox_api.config.settings import settings
from kairox_api.constants.enums import ErrorCode
from kairox_api.core.errors import AppError, app_error_handler, error_response
from kairox_api.core.logging import setup_logging
from kairox_api.core.middleware import RateLimitMiddleware
from kairox_api.core.redis_client import close_redis
from kairox_api.core.security_headers import SecurityHeadersMiddleware
from kairox_api.features.admin.routes import router as admin_router
from kairox_api.features.auth.routes import router as auth_router
from kairox_api.features.recharge.routes import router as recharge_router
from kairox_api.features.recharge.watcher import start_deposit_watcher
from kairox_api.features.team.routes import router as team_router
from kairox_api.features.trade.routes import router as trade_router
from kairox_api.features.wallet.routes import router as wallet_router
from kairox_api.features.withdraw.routes import router as withdraw_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    watcher_task = start_deposit_watcher()
    yield
    if watcher_task is not None:
        watcher_task.cancel()
        with suppress(asyncio.CancelledError):
            await watcher_task
    await close_redis()


app = FastAPI(
    title="Kairox Platform API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

app.add_exception_handler(AppError, app_error_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return error_response(ErrorCode.INTERNAL_ERROR, "Internal server error", 500)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "version": "2.0.0"}


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(wallet_router)
api_router.include_router(trade_router)
api_router.include_router(recharge_router)
api_router.include_router(withdraw_router)
api_router.include_router(team_router)
api_router.include_router(admin_router)
app.include_router(api_router)
