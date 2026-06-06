"""Phase 8 team commission ledger entry type

Revision ID: 007_phase8_team_commission
Revises: 006_phase8_team
"""

from collections.abc import Sequence

from alembic import op

revision: str = "007_phase8_team_commission"
down_revision: str | None = "006_phase8_team"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE ledgerentrytype ADD VALUE IF NOT EXISTS 'team_commission'")


def downgrade() -> None:
    pass
