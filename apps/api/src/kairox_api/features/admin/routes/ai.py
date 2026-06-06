from ai_gateway.types import ProviderError
from fastapi import APIRouter, Depends, Request

from kairox_api.constants.enums import ErrorCode, UserRole
from kairox_api.core.ai_rate_limit import enforce_ai_rate_limit
from kairox_api.core.cookies import validate_csrf
from kairox_api.core.errors import AppError
from kairox_api.dependencies.container import ServiceContainer, get_container, require_roles
from kairox_api.features.admin.schemas.ai import (
    AiAnalyzeRequest,
    AiAnalyzeResponse,
    AiHealthResponse,
)
from kairox_api.models.user import User

router = APIRouter()


@router.get("/health", response_model=AiHealthResponse)
async def ai_health(
    _admin: User = Depends(require_roles(UserRole.ADMIN)),
    container: ServiceContainer = Depends(get_container),
) -> AiHealthResponse:
    health = await container.ai.health()
    return AiHealthResponse(
        openai=bool(health["openai"]),
        anthropic=bool(health["anthropic"]),
        fallback=str(health["fallback"]),
    )


@router.post("/analyze", response_model=AiAnalyzeResponse)
async def ai_analyze(
    body: AiAnalyzeRequest,
    request: Request,
    admin: User = Depends(require_roles(UserRole.ADMIN)),
    container: ServiceContainer = Depends(get_container),
) -> AiAnalyzeResponse:
    validate_csrf(request)
    await enforce_ai_rate_limit(admin.id)
    try:
        result = await container.ai.analyze(
            body.use_case,
            body.payload,
            provider_preference=body.provider_preference,
        )
    except ProviderError as exc:
        raise AppError(ErrorCode.INTERNAL_ERROR, "AI provider unavailable", 503) from exc
    except ValueError as exc:
        raise AppError(ErrorCode.VALIDATION_ERROR, str(exc), 422) from exc

    return AiAnalyzeResponse(
        use_case=body.use_case,
        data=result.data,
        provider=result.provider,
        model=result.model,
        confidence=result.confidence,
    )
