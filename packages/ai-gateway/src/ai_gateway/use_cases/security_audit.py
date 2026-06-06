from typing import Any

from ai_gateway.providers.noop_provider import NoopProvider
from ai_gateway.providers.base import AiProvider, load_prompt
from ai_gateway.types import AnalysisResult


async def run_security_audit(provider: AiProvider, payload: dict[str, Any]) -> AnalysisResult:
    prompt = load_prompt("security_audit")
    context = {"use_case": "security_audit", "payload": payload, "system_prompt": prompt}
    result = await provider.analyze(prompt, context)
    data = result.data
    if isinstance(provider, NoopProvider):
        data = {
            "report_markdown": "## AI unavailable\n\nSecurity audit requires an AI provider.",
            "findings": [],
            "confidence": 0.0,
        }
    data.setdefault("report_markdown", "# Security Audit\n\nNo findings.")
    data.setdefault("findings", [])
    return AnalysisResult(
        data=data,
        provider=result.provider,
        model=result.model,
        confidence=result.confidence,
        raw_response=result.raw_response,
    )
