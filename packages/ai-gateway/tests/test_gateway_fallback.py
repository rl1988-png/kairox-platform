import pytest

from ai_gateway import AiGateway, GatewayConfig


@pytest.mark.asyncio
async def test_gateway_without_keys_uses_noop() -> None:
    gateway = AiGateway(GatewayConfig())
    result = await gateway.analyze("support_assist", {"message": "Hilfe"})
    assert result.data["summary"] == "AI unavailable"
    assert result.confidence == 0.0
    assert result.provider == "noop"


@pytest.mark.asyncio
async def test_gateway_health_no_keys() -> None:
    gateway = AiGateway(GatewayConfig())
    health = await gateway.health()
    assert health["openai"] is False
    assert health["anthropic"] is False
    assert health["fallback"] == "noop"
