"""Phase 6 admin operations

Revision ID: 005_phase6_admin
Revises: 004_phase5_trade
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_phase6_admin"
down_revision: str | None = "004_phase5_trade"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("vip_level", sa.Integer(), server_default="1", nullable=False))
    op.add_column(
        "users", sa.Column("is_official", sa.Boolean(), server_default="false", nullable=False)
    )
    op.add_column("users", sa.Column("withdrawal_address", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("withdrawal_network", sa.String(16), nullable=True))

    op.add_column(
        "withdraw_requests",
        sa.Column("fee_amount", sa.Numeric(18, 8), server_default="1", nullable=False),
    )
    op.add_column("withdraw_requests", sa.Column("tx_hash", sa.String(128), nullable=True))

    op.add_column("admin_audit_log", sa.Column("user_agent", sa.Text(), nullable=True))

    op.create_table(
        "admin_idempotency_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("admin_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("audit_log_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("admin_audit_log.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("admin_idempotency_keys")
    op.drop_column("admin_audit_log", "user_agent")
    op.drop_column("withdraw_requests", "tx_hash")
    op.drop_column("withdraw_requests", "fee_amount")
    op.drop_column("users", "withdrawal_network")
    op.drop_column("users", "withdrawal_address")
    op.drop_column("users", "is_official")
    op.drop_column("users", "vip_level")
