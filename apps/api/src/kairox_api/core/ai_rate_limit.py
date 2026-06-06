from uuid import UUID

from kairox_api.constants.enums import ErrorCode
from kairox_api.core.errors import AppError
from kairox_api.core.redis_client import get_redis

AI_RATE_LIMIT = 20
AI_RATE_WINDOW_SECONDS = 3600


async def enforce_ai_rate_limit(admin_user_id: UUID) -> None:
    key = f"ai:analyze:{admin_user_id}"
    try:
        redis = await get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, AI_RATE_WINDOW_SECONDS)
        if count > AI_RATE_LIMIT:
            raise AppError(
                ErrorCode.RATE_LIMITED,
                "AI analysis rate limit exceeded (20/hour)",
                429,
            )
    except AppError:
        raise
    except Exception:
        pass
