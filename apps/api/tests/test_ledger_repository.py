from decimal import Decimal

import pytest

from kairox_api.constants.enums import LedgerEntryType
from kairox_api.repositories.exceptions import InsufficientBalanceError
from kairox_api.repositories.ledger_repository import BalanceSnapshot, apply_balance_delta


def test_credit_increases_available_balance() -> None:
    start = BalanceSnapshot(available=Decimal("100"), locked=Decimal("0"))
    result = apply_balance_delta(start, Decimal("50"), Decimal("0"))
    assert result.available == Decimal("150")
    assert result.locked == Decimal("0")


def test_debit_decreases_available_balance() -> None:
    start = BalanceSnapshot(available=Decimal("100"), locked=Decimal("0"))
    result = apply_balance_delta(start, Decimal("-30"), Decimal("0"))
    assert result.available == Decimal("70")


def test_debit_rejects_negative_available_balance() -> None:
    start = BalanceSnapshot(available=Decimal("20"), locked=Decimal("0"))
    with pytest.raises(InsufficientBalanceError):
        apply_balance_delta(start, Decimal("-50"), Decimal("0"))


def test_lock_moves_funds_from_available_to_locked() -> None:
    start = BalanceSnapshot(available=Decimal("200"), locked=Decimal("0"))
    result = apply_balance_delta(start, Decimal("-100"), Decimal("100"))
    assert result.available == Decimal("100")
    assert result.locked == Decimal("100")


def test_sum_consistency_after_multiple_operations() -> None:
    balance = BalanceSnapshot(available=Decimal("0"), locked=Decimal("0"))
    deltas = [
        (Decimal("1000"), Decimal("0")),
        (Decimal("-100"), Decimal("100")),
        (Decimal("50"), Decimal("-50")),
        (Decimal("-200"), Decimal("0")),
    ]
    for avail_d, lock_d in deltas:
        balance = apply_balance_delta(balance, avail_d, lock_d)

    sum_available = sum(d[0] for d in deltas)
    sum_locked = sum(d[1] for d in deltas)
    assert balance.available == sum_available
    assert balance.locked == sum_locked
    assert balance.available == Decimal("750")


def test_unlock_restores_available_from_locked() -> None:
    start = BalanceSnapshot(available=Decimal("0"), locked=Decimal("100"))
    result = apply_balance_delta(start, Decimal("100"), Decimal("-100"))
    assert result.available == Decimal("100")
    assert result.locked == Decimal("0")


def test_ledger_entry_type_enum_values() -> None:
    assert LedgerEntryType.RECHARGE.value == "recharge"
    assert LedgerEntryType.TRADE_LOCK.value == "trade_lock"
