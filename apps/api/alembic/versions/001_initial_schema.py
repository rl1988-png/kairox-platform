"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("invite_code", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_teams_invite_code", "teams", ["invite_code"], unique=True)

    user_role = postgresql.ENUM("user", "admin", "support", name="userrole", create_type=False)
    user_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True),
        sa.Column("available", sa.Numeric(18, 8), nullable=False, server_default="0"),
        sa.Column("locked", sa.Numeric(18, 8), nullable=False, server_default="0"),
        sa.Column("deposit_address", sa.String(64), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    ledger_type = postgresql.ENUM(
        "recharge", "withdraw", "trade_lock", "trade_unlock",
        "trade_profit", "trade_loss", "admin_adjustment",
        name="ledgerentrytype", create_type=False,
    )
    ledger_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ledger_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("wallet_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wallets.id")),
        sa.Column("entry_type", ledger_type, nullable=False),
        sa.Column("amount", sa.Numeric(18, 8), nullable=False),
        sa.Column("balance_after", sa.Numeric(18, 8), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    trade_state = postgresql.ENUM(
        "idle", "pending_funds", "ready", "running", "settling",
        "completed", "failed", "cancelled",
        name="tradestate", create_type=False,
    )
    trade_state.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "trade_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("state", trade_state, nullable=False),
        sa.Column("amount", sa.Numeric(18, 8), nullable=False),
        sa.Column("profit", sa.Numeric(18, 8), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    recharge_status = postgresql.ENUM(
        "pending", "confirming", "confirmed", "failed",
        name="rechargestatus", create_type=False,
    )
    recharge_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "recharges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("tx_hash", sa.String(128), nullable=False),
        sa.Column("amount", sa.Numeric(18, 8), nullable=False),
        sa.Column("status", recharge_status, nullable=False),
        sa.Column("confirmations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_recharges_tx_hash", "recharges", ["tx_hash"], unique=True)

    withdraw_status = postgresql.ENUM(
        "pending", "approved", "processing", "completed", "rejected",
        name="withdrawstatus", create_type=False,
    )
    withdraw_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "withdrawals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("amount", sa.Numeric(18, 8), nullable=False),
        sa.Column("to_address", sa.String(64), nullable=False),
        sa.Column("status", withdraw_status, nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("withdrawals")
    op.drop_table("recharges")
    op.drop_table("trade_sessions")
    op.drop_table("ledger_entries")
    op.drop_table("wallets")
    op.drop_table("users")
    op.drop_table("teams")
    sa.Enum(name="withdrawstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="rechargestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tradestate").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="ledgerentrytype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
