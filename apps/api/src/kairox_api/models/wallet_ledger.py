import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, event, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kairox_api.constants.enums import LedgerEntryType
from kairox_api.core.database import Base
from kairox_api.models.types import MONEY, pg_enum

if TYPE_CHECKING:
    from kairox_api.models.user import User


class WalletLedger(Base):
    """Append-only immutable ledger â€” updates and deletes are forbidden."""

    __tablename__ = "wallet_ledger"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    entry_type: Mapped[LedgerEntryType] = mapped_column(pg_enum(LedgerEntryType, "ledgerentrytype"))
    amount: Mapped[Decimal] = mapped_column(MONEY)
    available_delta: Mapped[Decimal] = mapped_column(MONEY)
    locked_delta: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    available_after: Mapped[Decimal] = mapped_column(MONEY)
    locked_after: Mapped[Decimal] = mapped_column(MONEY)
    reference_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="ledger_entries")


@event.listens_for(WalletLedger, "before_update")
def _reject_ledger_update(_mapper: object, _connection: object, _target: WalletLedger) -> None:
    raise RuntimeError("wallet_ledger is immutable â€” updates are not allowed")


@event.listens_for(WalletLedger, "before_delete")
def _reject_ledger_delete(_mapper: object, _connection: object, _target: WalletLedger) -> None:
    raise RuntimeError("wallet_ledger is immutable â€” deletes are not allowed")
