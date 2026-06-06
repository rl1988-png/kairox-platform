"""Phase 2 wallet ledger schema

Revision ID: 002_phase2_ledger
Revises: 001_initial
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_phase2_ledger"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("ledger_entries")
    op.drop_table("wallets")
    op.drop_table("trade_sessions")
    op.drop_table("recharges")
    op.drop_table("withdrawals")

    op.add_column("users", sa.Column("deposit_address", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False))
    op.add_column(
        "users",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])

    op.create_table(
        "wallet_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("entry_type", postgresql.ENUM(name="ledgerentrytype", create_type=False), nullable=False),
        sa.Column("amount", sa.Numeric(18, 8), nullable=False),
        sa.Column("available_delta", sa.Numeric(18, 8), nullable=False),
        sa.Column("locked_delta", sa.Numeric(18, 8), server_default="0", nullable=False),
        sa.Column("available_after", sa.Numeric(18, 8), nullable=False),
        sa.Column("locked_after", sa.Numeric(18, 8), nullable=False),
        sa.Column("reference_type", sa.String(32), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_wallet_ledger_user_id", "wallet_ledger", ["user_id"])

    op.create_table(
        "recharge_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tx_hash", sa.String(128), nullable=False),
        sa.Column("amount", sa.Numeric(18, 8), nullable=False),
        sa.Column("status", postgresql.ENUM(name="rechargestatus", create_type=False), nullable=False),
        sa.Column("confirmations", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_recharge_orders_tx_hash", "recharge_orders", ["tx_hash"], unique=True)
    op.create_index("ix_recharge_orders_user_id", "recharge_orders", ["user_id"])

    op.create_table(
        "withdraw_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(18, 8), nullable=False),
        sa.Column("to_address", sa.String(64), nullable=False),
        sa.Column("status", postgresql.ENUM(name="withdrawstatus", create_type=False), nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_withdraw_requests_user_id", "withdraw_requests", ["user_id"])

    op.create_table(
        "trades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("state", postgresql.ENUM(name="tradestate", create_type=False), nullable=False),
        sa.Column("amount", sa.Numeric(18, 8), nullable=False),
        sa.Column("profit", sa.Numeric(18, 8), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_trades_user_id", "trades", ["user_id"])

    audit_action = postgresql.ENUM(
        "withdraw_approve",
        "withdraw_reject",
        "user_role_change",
        "ledger_adjustment",
        "recharge_manual",
        name="auditaction",
        create_type=False,
    )
    audit_action.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "team_earnings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("beneficiary_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("trade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trades.id"), nullable=True),
        sa.Column("amount", sa.Numeric(18, 8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_team_earnings_team_id", "team_earnings", ["team_id"])

    op.create_table(
        "admin_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("admin_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_admin_audit_log_admin_user_id", "admin_audit_log", ["admin_user_id"])

    op.create_table(
        "api_rate_limits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_key", sa.String(128), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("client_key", "window_start", name="uq_rate_limit_window"),
    )
    op.create_index("ix_api_rate_limits_client_key", "api_rate_limits", ["client_key"])


def downgrade() -> None:
    op.drop_table("api_rate_limits")
    op.drop_table("admin_audit_log")
    op.drop_table("team_earnings")
    op.drop_table("trades")
    op.drop_table("withdraw_requests")
    op.drop_table("recharge_orders")
    op.drop_table("wallet_ledger")
    op.drop_table("sessions")

    op.drop_column("users", "updated_at")
    op.drop_column("users", "is_active")
    op.drop_column("users", "deposit_address")

    sa.Enum(name="auditaction").drop(op.get_bind(), checkfirst=True)

    # Legacy Phase 1 tables restored minimally for downgrade
    op.create_table(
        "wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True),
        sa.Column("available", sa.Numeric(18, 8), server_default="0"),
        sa.Column("locked", sa.Numeric(18, 8), server_default="0"),
        sa.Column("deposit_address", sa.String(64), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
