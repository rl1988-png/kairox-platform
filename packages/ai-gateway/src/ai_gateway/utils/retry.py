import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def retry_async(
    func: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.5,
) -> T:
    """Exponential backoff retry — raises last exception after max_attempts."""
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as exc:
            last_exc = exc
            if attempt == max_attempts - 1:
                break
            delay = base_delay_seconds * (2**attempt)
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc
