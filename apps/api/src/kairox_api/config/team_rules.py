from decimal import Decimal

TEAM_VALID_MIN_DEPOSIT = Decimal("50")
MONEY_QUANTIZE = Decimal("0.00000001")

# Percent of trade profit paid to referrers (level 1 = direct referrer).
TEAM_COMMISSION_RATES: dict[int, Decimal] = {
    1: Decimal("0.10"),
    2: Decimal("0.05"),
    3: Decimal("0.02"),
}
