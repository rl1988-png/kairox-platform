"""Add VIP adjustment audit action

Revision ID: 009_admin_audit_vip_adjust
Revises: 008_phase8_trial_bonus
"""

from collections.abc import Sequence

from alembic import op

revision: str = "009_admin_audit_vip_adjust"
down_revision: str | None = "008_phase8_trial_bonus"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'vip_level_adjust'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without recreating the type.
    pass
