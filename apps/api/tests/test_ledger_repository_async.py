from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from kairox_api.constants.enums import LedgerEntryType
from kairox_api.repositories.exceptions import InsufficientBalanceError
from kairox_api.repositories.ledger_repository import LedgerRepository


def _mock_session_no_entries() -> MagicMock:
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    result.scalar_one.return_value = Decimal("0")
    session.execute = AsyncMock(return_value=result)
    session.flush = AsyncMock()
    return session


def _mock_session_with_balance(available: Decimal, locked: Decimal = Decimal("0")) -> MagicMock:
    session = MagicMock()
    latest = MagicMock()
    latest.available_after = available
    latest.locked_after = locked
    result = MagicMock()
    result.scalar_one_or_none.return_value = latest
    result.scalar_one.return_value = available
    session.execute = AsyncMock(return_value=result)
    session.flush = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_repository_credit_appends_entry() -> None:
    session = _mock_session_no_entries()
    repo = LedgerRepository(session)
    user_id = uuid4()
    entry = await repo.credit(user_id, Decimal("250"), LedgerEntryType.RECHARGE)
    assert entry.available_after == Decimal("250")
    session.add.assert_called_once()


@pytest.mark.asyncio
async def test_repository_debit_reduces_balance() -> None:
    session = _mock_session_with_balance(Decimal("100"))
    repo = LedgerRepository(session)
    entry = await repo.debit(uuid4(), Decimal("40"), LedgerEntryType.WITHDRAW)
    assert entry.available_after == Decimal("60")


@pytest.mark.asyncio
async def test_repository_debit_raises_on_insufficient() -> None:
    session = _mock_session_with_balance(Decimal("10"))
    repo = LedgerRepository(session)
    with pytest.raises(InsufficientBalanceError):
        await repo.debit(uuid4(), Decimal("50"), LedgerEntryType.WITHDRAW)


@pytest.mark.asyncio
async def test_repository_lock_moves_to_locked() -> None:
    session = _mock_session_with_balance(Decimal("200"))
    repo = LedgerRepository(session)
    entry = await repo.lock(uuid4(), Decimal("75"), LedgerEntryType.TRADE_LOCK)
    assert entry.available_after == Decimal("125")
    assert entry.locked_after == Decimal("75")


@pytest.mark.asyncio
async def test_repository_unlock_restores_available() -> None:
    session = _mock_session_with_balance(Decimal("0"), Decimal("100"))
    repo = LedgerRepository(session)
    entry = await repo.unlock(uuid4(), Decimal("100"), LedgerEntryType.TRADE_UNLOCK)
    assert entry.available_after == Decimal("100")
    assert entry.locked_after == Decimal("0")


@pytest.mark.asyncio
async def test_repository_release_locked_and_credit() -> None:
    session = _mock_session_with_balance(Decimal("0"), Decimal("100"))
    repo = LedgerRepository(session)
    entry = await repo.release_locked_and_credit(
        uuid4(), Decimal("100"), Decimal("25"), LedgerEntryType.TRADE_PROFIT
    )
    assert entry.available_after == Decimal("125")
    assert entry.locked_after == Decimal("0")
