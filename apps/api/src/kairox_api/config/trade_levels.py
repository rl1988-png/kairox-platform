from dataclasses import dataclass
from decimal import Decimal

MAX_TRADES_PER_DAY = 2
TRADE_COOLDOWN_SECONDS = 60
PRE_START_TTL_SECONDS = 60


@dataclass(frozen=True)
class TradeLevel:
    level: int
    name: str
    min_balance: Decimal
    trade_amount: Decimal
    profit_rate: Decimal
    duration_seconds: int


TRADE_LEVELS: dict[int, TradeLevel] = {
    1: TradeLevel(
        level=1,
        name="VIP1",
        min_balance=Decimal("50"),
        trade_amount=Decimal("50"),
        profit_rate=Decimal("0.003"),
        duration_seconds=120,
    ),
    2: TradeLevel(
        level=2,
        name="VIP2",
        min_balance=Decimal("200"),
        trade_amount=Decimal("100"),
        profit_rate=Decimal("0.004"),
        duration_seconds=150,
    ),
    3: TradeLevel(
        level=3,
        name="VIP3",
        min_balance=Decimal("500"),
        trade_amount=Decimal("250"),
        profit_rate=Decimal("0.005"),
        duration_seconds=180,
    ),
}


def get_level(level: int) -> TradeLevel | None:
    return TRADE_LEVELS.get(level)


def calculate_profit(level: TradeLevel, amount: Decimal) -> Decimal:
    return (amount * level.profit_rate).quantize(Decimal("0.00000001"))
