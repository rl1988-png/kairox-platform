from fastapi import APIRouter, Depends, Request

from kairox_api.core.cookies import validate_csrf
from kairox_api.dependencies.container import (
    ServiceContainer,
    decimal_str,
    get_container,
    get_current_user,
)
from kairox_api.features.trade.schemas.trade import (
    CompleteTradeRequest,
    PreStartTradeRequest,
    StartTradeRequest,
    TradeLevelPublic,
    TradeSessionPublic,
)
from kairox_api.models.user import User

router = APIRouter(prefix="/trade", tags=["trade"])


def _to_public(trade) -> TradeSessionPublic:
    return TradeSessionPublic(
        id=trade.id,
        user_id=trade.user_id,
        state=trade.state.value,
        vip_level=trade.vip_level,
        amount=decimal_str(trade.amount),
        profit=decimal_str(trade.profit) if trade.profit is not None else None,
        expires_at=trade.expires_at,
        duration_seconds=trade.duration_seconds,
        started_at=trade.started_at,
        completed_at=trade.completed_at,
    )


@router.get("/levels", response_model=list[TradeLevelPublic])
async def list_trade_levels(
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> list[TradeLevelPublic]:
    levels = await container.trade.list_levels(user.id)
    return [TradeLevelPublic(**level) for level in levels]


@router.get("/active", response_model=TradeSessionPublic | None)
async def get_active_trade(
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> TradeSessionPublic | None:
    trade = await container.trade.get_active(user.id)
    return _to_public(trade) if trade else None


@router.post("/pre-start", response_model=TradeSessionPublic)
async def pre_start_trade(
    body: PreStartTradeRequest,
    request: Request,
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> TradeSessionPublic:
    validate_csrf(request)
    trade = await container.trade.pre_start(user.id, body.vip_level)
    return _to_public(trade)


@router.post("/start", response_model=TradeSessionPublic)
async def start_trade(
    body: StartTradeRequest,
    request: Request,
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> TradeSessionPublic:
    validate_csrf(request)
    trade = await container.trade.start(user.id, body.trade_id)
    return _to_public(trade)


@router.post("/complete", response_model=TradeSessionPublic)
async def complete_trade(
    body: CompleteTradeRequest,
    request: Request,
    user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> TradeSessionPublic:
    validate_csrf(request)
    trade = await container.trade.complete(user.id, body.trade_id)
    return _to_public(trade)
