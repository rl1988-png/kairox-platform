from typing import Any

from ai_gateway.types import AnalysisResult


class MockProvider:
    name = "mock"
    model = "mock-model"
    calls = 0
    fail_until: int

    def __init__(self, fail_until: int = 0) -> None:
        self.fail_until = fail_until

    async def analyze(self, prompt: str, context: dict[str, Any]) -> AnalysisResult:
        self.calls += 1
        if self.calls <= self.fail_until:
            raise RuntimeError("provider unavailable")
        return AnalysisResult(
            data={"summary": "ok", "confidence": 0.9},
            provider=self.name,
            model=self.model,
            confidence=0.9,
            raw_response='{"summary":"ok"}',
        )

    async def health_check(self) -> bool:
        return True
