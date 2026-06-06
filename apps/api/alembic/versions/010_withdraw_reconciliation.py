"""Add withdraw reconciliation fields

Revision ID: 010_withdraw_reconciliation
Revises: 009_admin_audit_vip_adjust
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "010_withdraw_reconciliation"
down_revision: str | None = "009_admin_audit_vip_adjust"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE withdrawstatus ADD VALUE IF NOT EXISTS 'failed'")
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'withdraw_confirm'")
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'withdraw_fail'")

    op.add_column(
        "withdraw_requests",
        sa.Column("confirmations", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "withdraw_requests",
        sa.Column("broadcasted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "withdraw_requests",
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "withdraw_requests",
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_withdraw_requests_tx_hash_unique",
        "withdraw_requests",
        ["tx_hash"],
        unique=True,
        postgresql_where=sa.text("tx_hash IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_withdraw_requests_tx_hash_unique", table_name="withdraw_requests")
    op.drop_column("withdraw_requests", "failed_at")
    op.drop_column("withdraw_requests", "confirmed_at")
    op.drop_column("withdraw_requests", "broadcasted_at")
    op.drop_column("withdraw_requests", "confirmations")
