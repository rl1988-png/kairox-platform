from typing import Any

from ai_gateway.providers.base import AiProvider, load_prompt
from ai_gateway.types import AnalysisResult


async def run_support_assist(provider: AiProvider, payload: dict[str, Any]) -> AnalysisResult:
    prompt = load_prompt("support_assist")
    context = {"use_case": "support_assist", "payload": payload, "system_prompt": prompt}
    result = await provider.analyze(prompt, context)
    data = result.data
    data.setdefault("summary", "Analysis complete")
    data.setdefault("suggested_reply_de", "")
    data.setdefault("risk_flags", [])
    data["provider"] = result.provider
    data["model"] = result.model
    return AnalysisResult(
        data=data,
        provider=result.provider,
        model=result.model,
        confidence=result.confidence,
        raw_response=result.raw_response,
    )
