"""Phase 4 recharge order flow

Revision ID: 003_phase4_recharge
Revises: 002_phase2_ledger
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_phase4_recharge"
down_revision: str | None = "002_phase2_ledger"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE rechargestatus ADD VALUE IF NOT EXISTS 'paid'")
    op.execute("ALTER TYPE rechargestatus ADD VALUE IF NOT EXISTS 'expired'")

    op.add_column(
        "recharge_orders",
        sa.Column("expected_amount", sa.Numeric(18, 8), nullable=True),
    )
    op.add_column(
        "recharge_orders",
        sa.Column("deposit_address", sa.String(64), nullable=True),
    )
    op.add_column(
        "recharge_orders",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("recharge_orders", "tx_hash", existing_type=sa.String(128), nullable=True)

    op.execute("UPDATE recharge_orders SET expected_amount = amount WHERE expected_amount IS NULL")
    op.alter_column("recharge_orders", "expected_amount", nullable=False)

    op.create_index(
        "ix_recharge_orders_status_expires",
        "recharge_orders",
        ["status", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_recharge_orders_status_expires", table_name="recharge_orders")
    op.drop_column("recharge_orders", "expires_at")
    op.drop_column("recharge_orders", "deposit_address")
    op.drop_column("recharge_orders", "expected_amount")
    op.alter_column("recharge_orders", "tx_hash", existing_type=sa.String(128), nullable=False)
