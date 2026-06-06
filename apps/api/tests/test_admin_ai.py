import pytest
from httpx import ASGITransport, AsyncClient

from kairox_api.main import app


@pytest.mark.asyncio
async def test_ai_analyze_requires_admin_role() -> None:
    """Non-admin users must receive 403 on AI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/ai/analyze",
            json={
                "use_case": "tx_fraud_check",
                "payload": {"amount_on_chain": "30", "claimed_amount": "3000"},
            },
        )
    assert response.status_code in {401, 403}
