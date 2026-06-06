import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from kairox_api.config.settings import settings
from kairox_api.constants.enums import ErrorCode
from kairox_api.core.errors import error_response
from kairox_api.core.logging import get_logger
from kairox_api.core.redis_client import get_redis

logger = get_logger(__name__)

RATE_LIMIT_BYPASS_PATHS = {"/health", "/docs", "/openapi.json"}
FAIL_CLOSED_PREFIXES = (
    "/api/v1/auth",
    "/api/v1/admin",
    "/api/v1/wallet",
    "/api/v1/withdraw",
    "/api/v1/trade",
    "/api/v1/recharge",
    "/api/v1/team",
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in RATE_LIMIT_BYPASS_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate:{client_ip}:{int(time.time()) // settings.rate_limit_window_seconds}"

        try:
            redis = await get_redis()
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, settings.rate_limit_window_seconds)

            if count > settings.rate_limit_requests:
                return error_response(
                    ErrorCode.RATE_LIMITED,
                    "Too many requests",
                    429,
                )
        except Exception as exc:
            logger.warning(
                "global_rate_limit_unavailable",
                path=request.url.path,
                method=request.method,
                exc_info=exc,
            )
            if _requires_rate_limit(request.url.path):
                return error_response(
                    ErrorCode.RATE_LIMITED,
                    "Rate limiting is temporarily unavailable. Please try again later.",
                    503,
                )

        return await call_next(request)


def _requires_rate_limit(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in FAIL_CLOSED_PREFIXES)
