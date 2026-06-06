import pytest

from ai_gateway.utils.retry import retry_async


@pytest.mark.asyncio
async def test_retry_succeeds_on_third_attempt() -> None:
    attempts = 0

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("temporary")
        return "ok"

    result = await retry_async(flaky, max_attempts=3, base_delay_seconds=0.01)
    assert result == "ok"
    assert attempts == 3
