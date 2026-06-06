"""Phase 5 trade system

Revision ID: 004_phase5_trade
Revises: 003_phase4_recharge
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_phase5_trade"
down_revision: str | None = "003_phase4_recharge"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE tradestate ADD VALUE IF NOT EXISTS 'pre_started'")

    op.add_column("trades", sa.Column("vip_level", sa.Integer(), nullable=True))
    op.add_column("trades", sa.Column("pre_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("trades", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("trades", sa.Column("duration_seconds", sa.Integer(), nullable=True))

    op.create_index("ix_trades_user_state", "trades", ["user_id", "state"])


def downgrade() -> None:
    op.drop_index("ix_trades_user_state", table_name="trades")
    op.drop_column("trades", "duration_seconds")
    op.drop_column("trades", "expires_at")
    op.drop_column("trades", "pre_started_at")
    op.drop_column("trades", "vip_level")
