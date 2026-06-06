from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from kairox_api.constants.enums import LedgerEntryType
from kairox_api.models.wallet_ledger import WalletLedger
from kairox_api.repositories.exceptions import InsufficientBalanceError, InsufficientLockedError


@dataclass(frozen=True)
class BalanceSnapshot:
    available: Decimal
    locked: Decimal


def apply_balance_delta(
    balance: BalanceSnapshot,
    available_delta: Decimal,
    locked_delta: Decimal,
) -> BalanceSnapshot:
    """Pure balance transition — raises if result would be negative."""
    available_after = balance.available + available_delta
    locked_after = balance.locked + locked_delta
    if available_after < 0:
        raise InsufficientBalanceError("Operation would result in negative available balance")
    if locked_after < 0:
        raise InsufficientLockedError("Operation would result in negative locked balance")
    return BalanceSnapshot(available=available_after, locked=locked_after)


class LedgerRepository:
    """Single write path for wallet balances — append-only wallet_ledger."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_balance(self, user_id: UUID) -> BalanceSnapshot:
        snapshot = await self._latest_snapshot(user_id)
        if snapshot is None:
            return BalanceSnapshot(available=Decimal("0"), locked=Decimal("0"))
        return snapshot

    async def credit(
        self,
        user_id: UUID,
        amount: Decimal,
        entry_type: LedgerEntryType,
        reference_id: UUID | None = None,
        reference_type: str | None = None,
    ) -> WalletLedger:
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        return await self._append(
            user_id=user_id,
            entry_type=entry_type,
            amount=amount,
            available_delta=amount,
            locked_delta=Decimal("0"),
            reference_id=reference_id,
            reference_type=reference_type,
        )

    async def debit(
        self,
        user_id: UUID,
        amount: Decimal,
        entry_type: LedgerEntryType,
        reference_id: UUID | None = None,
        reference_type: str | None = None,
    ) -> WalletLedger:
        if amount <= 0:
            raise ValueError("Debit amount must be positive")
        balance = await self.get_balance(user_id)
        if balance.available < amount:
            raise InsufficientBalanceError()
        return await self._append(
            user_id=user_id,
            entry_type=entry_type,
            amount=amount,
            available_delta=-amount,
            locked_delta=Decimal("0"),
            reference_id=reference_id,
            reference_type=reference_type,
        )

    async def lock(
        self,
        user_id: UUID,
        amount: Decimal,
        entry_type: LedgerEntryType,
        reference_id: UUID | None = None,
        reference_type: str | None = None,
    ) -> WalletLedger:
        if amount <= 0:
            raise ValueError("Lock amount must be positive")
        balance = await self.get_balance(user_id)
        if balance.available < amount:
            raise InsufficientBalanceError()
        return await self._append(
            user_id=user_id,
            entry_type=entry_type,
            amount=amount,
            available_delta=-amount,
            locked_delta=amount,
            reference_id=reference_id,
            reference_type=reference_type,
        )

    async def unlock(
        self,
        user_id: UUID,
        amount: Decimal,
        entry_type: LedgerEntryType,
        reference_id: UUID | None = None,
        reference_type: str | None = None,
    ) -> WalletLedger:
        if amount <= 0:
            raise ValueError("Unlock amount must be positive")
        balance = await self.get_balance(user_id)
        if balance.locked < amount:
            raise InsufficientLockedError()
        return await self._append(
            user_id=user_id,
            entry_type=entry_type,
            amount=amount,
            available_delta=amount,
            locked_delta=-amount,
            reference_id=reference_id,
            reference_type=reference_type,
        )

    async def release_locked_and_credit(
        self,
        user_id: UUID,
        locked_amount: Decimal,
        profit: Decimal,
        entry_type: LedgerEntryType,
        reference_id: UUID | None = None,
        reference_type: str | None = None,
    ) -> WalletLedger:
        """Release locked trade capital and apply profit/loss to available balance."""
        if locked_amount <= 0:
            raise ValueError("Locked amount must be positive")
        if profit < -locked_amount:
            raise ValueError("Loss cannot exceed locked capital")
        balance = await self.get_balance(user_id)
        if balance.locked < locked_amount:
            raise InsufficientLockedError()
        net_available = locked_amount + profit
        return await self._append(
            user_id=user_id,
            entry_type=entry_type,
            amount=abs(profit) if profit != 0 else locked_amount,
            available_delta=net_available,
            locked_delta=-locked_amount,
            reference_id=reference_id,
            reference_type=reference_type,
        )

    async def list_entries(self, user_id: UUID, limit: int = 50) -> list[WalletLedger]:
        result = await self._session.execute(
            select(WalletLedger)
            .where(WalletLedger.user_id == user_id)
            .order_by(WalletLedger.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def sum_available_deltas(self, user_id: UUID) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(WalletLedger.available_delta), 0)).where(
                WalletLedger.user_id == user_id
            )
        )
        total = result.scalar_one()
        return Decimal(str(total))

    async def sum_locked_deltas(self, user_id: UUID) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(WalletLedger.locked_delta), 0)).where(
                WalletLedger.user_id == user_id
            )
        )
        total = result.scalar_one()
        return Decimal(str(total))

    async def entry_exists(self, reference_id: UUID, reference_type: str) -> bool:
        result = await self._session.execute(
            select(WalletLedger.id).where(
                WalletLedger.reference_id == reference_id,
                WalletLedger.reference_type == reference_type,
            )
        )
        return result.scalar_one_or_none() is not None

    async def sum_credit_amount_by_type(
        self, user_id: UUID, entry_type: LedgerEntryType
    ) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(WalletLedger.amount), 0)).where(
                WalletLedger.user_id == user_id,
                WalletLedger.entry_type == entry_type,
            )
        )
        return Decimal(str(result.scalar_one()))

    async def _latest_snapshot(self, user_id: UUID) -> BalanceSnapshot | None:
        result = await self._session.execute(
            select(WalletLedger)
            .where(WalletLedger.user_id == user_id)
            .order_by(WalletLedger.created_at.desc(), WalletLedger.id.desc())
            .limit(1)
        )
        entry = result.scalar_one_or_none()
        if entry is None:
            return None
        return BalanceSnapshot(available=entry.available_after, locked=entry.locked_after)

    async def _acquire_wallet_lock(self, user_id: UUID) -> None:
        """Serialize concurrent wallet mutations for one user via a PostgreSQL advisory lock.

        pg_advisory_xact_lock is transaction-scoped — released automatically on commit/rollback.
        The int64 key is derived from the first 8 bytes of the UUID, which is unique per user.
        """
        lock_key = int.from_bytes(user_id.bytes[:8], byteorder="big", signed=True)
        await self._session.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": lock_key})

    async def _append(
        self,
        user_id: UUID,
        entry_type: LedgerEntryType,
        amount: Decimal,
        available_delta: Decimal,
        locked_delta: Decimal,
        reference_id: UUID | None,
        reference_type: str | None,
    ) -> WalletLedger:
        # Acquire per-user advisory lock before the authoritative balance read.
        # Prevents TOCTOU overdraw when concurrent requests race for the same wallet.
        await self._acquire_wallet_lock(user_id)
        balance = await self.get_balance(user_id)
        new_balance = apply_balance_delta(balance, available_delta, locked_delta)

        entry = WalletLedger(
            user_id=user_id,
            entry_type=entry_type,
            amount=amount,
            available_delta=available_delta,
            locked_delta=locked_delta,
            available_after=new_balance.available,
            locked_after=new_balance.locked,
            reference_id=reference_id,
            reference_type=reference_type,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
