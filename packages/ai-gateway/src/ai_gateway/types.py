from dataclasses import dataclass, field
from typing import Any


class ProviderError(Exception):
    """Raised when all provider retries are exhausted."""

    def __init__(self, message: str, provider: str | None = None) -> None:
        self.provider = provider
        super().__init__(message)


@dataclass(frozen=True)
class AnalysisRequest:
    use_case: str
    payload: dict[str, Any]
    provider_preference: str = "auto"


@dataclass
class AnalysisResult:
    data: dict[str, Any]
    provider: str
    model: str
    confidence: float = 0.0
    raw_response: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
