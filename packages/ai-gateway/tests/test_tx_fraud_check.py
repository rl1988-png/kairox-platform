import pytest

from ai_gateway import AiGateway, GatewayConfig
from ai_gateway.use_cases.tx_fraud_check import run_tx_fraud_check
from tests.mocks.provider_mock import MockProvider


@pytest.mark.asyncio
async def test_tx_fraud_30_vs_3000_likely_fraud() -> None:
    provider = MockProvider()
    result = await run_tx_fraud_check(
        provider,
        {
            "tx_hash": "abc123",
            "amount_on_chain": "30.00",
            "claimed_amount": "3000.00",
            "verdict_on_chain": "CREDIT_OK",
        },
    )
    assert result.data["verdict"] == "LIKELY_FRAUD"
    assert result.data["recommended_action"] == "REJECT_AND_EDUCATE"
    assert "3000" in result.data["reasons"][0]


@pytest.mark.asyncio
async def test_tx_fraud_via_gateway() -> None:
    gateway = AiGateway(GatewayConfig())
    result = await gateway.analyze(
        "tx_fraud_check",
        {"amount_on_chain": "30", "claimed_amount": "3000"},
    )
    assert result.data["verdict"] == "LIKELY_FRAUD"
