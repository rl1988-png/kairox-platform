from ai_gateway import AiGateway, GatewayConfig, ProviderError
from ai_gateway.types import AnalysisResult

from kairox_api.config.settings import settings


def build_ai_gateway() -> AiGateway:
    return AiGateway(
        GatewayConfig(
            openai_api_key=settings.openai_api_key,
            anthropic_api_key=settings.anthropic_api_key,
            default_provider=settings.ai_default_provider,
            request_timeout_seconds=float(settings.ai_request_timeout_sec),
            max_tokens=settings.ai_max_tokens,
            enable_pii_mask=settings.ai_enable_pii_mask,
        )
    )


class AiAnalysisService:
    def __init__(self, gateway: AiGateway | None = None) -> None:
        self._gateway = gateway or build_ai_gateway()

    async def analyze(
        self,
        use_case: str,
        payload: dict[str, object],
        provider_preference: str = "auto",
    ) -> AnalysisResult:
        try:
            return await self._gateway.analyze(
                use_case,
                payload,
                provider_preference=provider_preference,
            )
        except ProviderError:
            raise
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    async def health(self) -> dict[str, object]:
        return await self._gateway.health()
