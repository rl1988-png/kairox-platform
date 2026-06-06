from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Enum, Numeric

# PostgreSQL DECIMAL(18,8) for all monetary values
MONEY = Numeric(18, 8)

type Money = Decimal


def pg_enum[EnumT: PyEnum](enum_cls: type[EnumT], name: str) -> Enum:
    """Map Python StrEnum values (lowercase) to PostgreSQL native enums."""
    return Enum(enum_cls, name=name, values_callable=lambda x: [e.value for e in x])
