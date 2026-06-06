from dataclasses import dataclass
from typing import Any

from ai_gateway.providers.anthropic_provider import AnthropicProvider
from ai_gateway.providers.base import AiProvider
from ai_gateway.providers.noop_provider import NoopProvider
from ai_gateway.providers.openai_provider import OpenAiProvider
from ai_gateway.types import AnalysisResult, ProviderError
from ai_gateway.use_cases.security_audit import run_security_audit
from ai_gateway.use_cases.support_assist import run_support_assist
from ai_gateway.use_cases.tx_fraud_check import run_tx_fraud_check
from ai_gateway.utils.pii_mask import mask_pii
from ai_gateway.utils.retry import retry_async

USE_CASES = frozenset({"support_assist", "tx_fraud_check", "security_audit"})


@dataclass
class GatewayConfig:
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    default_provider: str = "auto"
    request_timeout_seconds: float = 30.0
    max_tokens: int = 2048
    enable_pii_mask: bool = True
    max_retries: int = 3


class AiGateway:
    """Single entry point for all AI analysis in Kairox Platform."""

    def __init__(self, config: GatewayConfig | None = None) -> None:
        self._config = config or GatewayConfig()
        self._noop = NoopProvider()
        self._openai: OpenAiProvider | None = None
        self._anthropic: AnthropicProvider | None = None
        if self._config.openai_api_key:
            self._openai = OpenAiProvider(
                self._config.openai_api_key,
                timeout_seconds=self._config.request_timeout_seconds,
                max_tokens=self._config.max_tokens,
            )
        if self._config.anthropic_api_key:
            self._anthropic = AnthropicProvider(
                self._config.anthropic_api_key,
                timeout_seconds=self._config.request_timeout_seconds,
                max_tokens=self._config.max_tokens,
            )

    def resolve_provider(self, preference: str = "auto") -> AiProvider:
        pref = preference or self._config.default_provider
        if pref == "openai" and self._openai is not None:
            return self._openai
        if pref == "anthropic" and self._anthropic is not None:
            return self._anthropic
        if pref == "auto":
            if self._openai is not None:
                return self._openai
            if self._anthropic is not None:
                return self._anthropic
        return self._noop

    async def health(self) -> dict[str, object]:
        openai_ok = await self._openai.health_check() if self._openai else False
        anthropic_ok = await self._anthropic.health_check() if self._anthropic else False
        fallback = "noop" if not openai_ok and not anthropic_ok else self._config.default_provider
        return {
            "openai": openai_ok,
            "anthropic": anthropic_ok,
            "fallback": fallback if fallback != "auto" else ("openai" if openai_ok else "noop"),
        }

    async def analyze(
        self,
        use_case: str,
        payload: dict[str, Any],
        *,
        provider_preference: str = "auto",
    ) -> AnalysisResult:
        if use_case not in USE_CASES:
            raise ValueError(f"Unknown use case: {use_case}")

        masked_payload = mask_pii(payload) if self._config.enable_pii_mask else payload
        provider = self.resolve_provider(provider_preference)

        async def _run() -> AnalysisResult:
            if use_case == "support_assist":
                return await run_support_assist(provider, masked_payload)
            if use_case == "tx_fraud_check":
                return await run_tx_fraud_check(provider, masked_payload)
            return await run_security_audit(provider, masked_payload)

        if isinstance(provider, NoopProvider):
            return await _run()

        try:
            return await retry_async(_run, max_attempts=self._config.max_retries)
        except Exception as exc:
            raise ProviderError(str(exc), getattr(provider, "name", None)) from exc
