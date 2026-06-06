"""Phase 8 trial period and registration bonus

Revision ID: 008_phase8_trial_bonus
Revises: 007_phase8_team_commission
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008_phase8_trial_bonus"
down_revision: str | None = "007_phase8_team_commission"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("trial_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("ALTER TYPE ledgerentrytype ADD VALUE IF NOT EXISTS 'registration_bonus'")


def downgrade() -> None:
    op.drop_column("users", "trial_expires_at")
