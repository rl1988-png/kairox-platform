import json
from typing import Any

from ai_gateway.types import AnalysisResult


class NoopProvider:
    name = "noop"
    model = "none"

    async def analyze(self, prompt: str, context: dict[str, Any]) -> AnalysisResult:
        use_case = context.get("use_case", "unknown")
        return AnalysisResult(
            data={
                "summary": "AI unavailable",
                "confidence": 0.0,
                "use_case": use_case,
            },
            provider=self.name,
            model=self.model,
            confidence=0.0,
            raw_response=None,
        )

    async def health_check(self) -> bool:
        return True
