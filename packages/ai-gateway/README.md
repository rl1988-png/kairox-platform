# AI Gateway

Provider-agnostic AI analysis for Kairox Platform support, fraud detection, and security audits.

## Install

```bash
pip install -e ".[dev]"
pytest
```

## Usage

```python
from ai_gateway import AiGateway, GatewayConfig

gateway = AiGateway(GatewayConfig())
result = await gateway.analyze("tx_fraud_check", {"claimed_amount": "3000", ...})
```

## Fallback

When no API keys are configured, `noop_provider` returns graceful degradation responses — no crashes.

## Tests

```bash
pytest -v
```
