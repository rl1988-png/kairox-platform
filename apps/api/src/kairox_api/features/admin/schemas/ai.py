from typing import Any

from pydantic import BaseModel, Field


class AiAnalyzeRequest(BaseModel):
    use_case: str = Field(pattern=r"^(support_assist|tx_fraud_check|security_audit)$")
    payload: dict[str, Any] = Field(default_factory=dict)
    provider_preference: str = Field(default="auto", pattern=r"^(openai|anthropic|auto)$")


class AiAnalyzeResponse(BaseModel):
    use_case: str
    data: dict[str, Any]
    provider: str
    model: str
    confidence: float


class AiHealthResponse(BaseModel):
    openai: bool
    anthropic: bool
    fallback: str
