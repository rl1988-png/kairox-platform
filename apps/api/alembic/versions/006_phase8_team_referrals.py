"""Phase 8 team referrals and invite codes

Revision ID: 006_phase8_team
Revises: 005_phase6_admin
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_phase8_team"
down_revision: str | None = "005_phase6_admin"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("invite_code", sa.String(16), nullable=True))
    op.add_column(
        "users",
        sa.Column("referrer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_users_invite_code", "users", ["invite_code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_invite_code", table_name="users")
    op.drop_column("users", "referrer_id")
    op.drop_column("users", "invite_code")
