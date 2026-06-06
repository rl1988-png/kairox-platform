from decimal import Decimal, InvalidOperation
from typing import Any

from ai_gateway.providers.base import AiProvider, load_prompt
from ai_gateway.types import AnalysisResult


def _parse_amount(value: object) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def rule_based_tx_verdict(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Fast path for obvious amount mismatch fraud (e.g. 30 vs 3000 USDT)."""
    on_chain = _parse_amount(payload.get("amount_on_chain"))
    claimed = _parse_amount(payload.get("claimed_amount"))
    if on_chain is None or claimed is None:
        return None

    if claimed > on_chain * Decimal("10") and on_chain <= Decimal("50"):
        return {
            "verdict": "LIKELY_FRAUD",
            "reasons": [
                f"on_chain {on_chain} USDT but user claims {claimed} USDT",
            ],
            "recommended_action": "REJECT_AND_EDUCATE",
            "confidence": 0.95,
        }
    if claimed != on_chain and abs(claimed - on_chain) > Decimal("0.01"):
        return {
            "verdict": "SUSPICIOUS",
            "reasons": [f"claimed {claimed} USDT differs from on-chain {on_chain} USDT"],
            "recommended_action": "MANUAL_REVIEW",
            "confidence": 0.7,
        }
    return {
        "verdict": "LIKELY_LEGIT",
        "reasons": ["on-chain amount matches claim within tolerance"],
        "recommended_action": "APPROVE_CREDIT",
        "confidence": 0.85,
    }


async def run_tx_fraud_check(provider: AiProvider, payload: dict[str, Any]) -> AnalysisResult:
    ruled = rule_based_tx_verdict(payload)
    if ruled is not None and ruled["verdict"] == "LIKELY_FRAUD":
        return AnalysisResult(
            data=ruled,
            provider="rules",
            model="tx-fraud-rules",
            confidence=float(ruled["confidence"]),
        )

    prompt = load_prompt("tx_fraud_check")
    context = {"use_case": "tx_fraud_check", "payload": payload, "system_prompt": prompt}
    result = await provider.analyze(prompt, context)
    if ruled is not None and result.confidence < float(ruled["confidence"]):
        return AnalysisResult(
            data=ruled,
            provider="rules",
            model="tx-fraud-rules",
            confidence=float(ruled["confidence"]),
        )
    return result
