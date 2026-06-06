from kairox_api.constants.enums import ErrorCode
from kairox_api.core.errors import AppError
from kairox_api.core.logging import get_logger
from kairox_api.core.redis_client import get_redis

logger = get_logger(__name__)


async def enforce_login_rate_limit(client_ip: str) -> None:
    await _enforce(f"auth:login:{client_ip}", limit=5, window_seconds=60)


async def enforce_register_rate_limit(client_ip: str) -> None:
    await _enforce(f"auth:register:{client_ip}", limit=3, window_seconds=3600)


async def _enforce(key: str, limit: int, window_seconds: int) -> None:
    try:
        redis = await get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
        if count > limit:
            raise AppError(
                ErrorCode.RATE_LIMITED, "Too many attempts. Please try again later.", 429
            )
    except AppError:
        raise
    except Exception as exc:
        logger.warning("auth_rate_limit_unavailable", key=key, exc_info=exc)
        raise AppError(
            ErrorCode.RATE_LIMITED,
            "Rate limiting is temporarily unavailable. Please try again later.",
            503,
        ) from exc
