from pathlib import Path

from kairox_api.constants.enums import AuditAction, WithdrawStatus


def test_audit_action_enum_values_are_migrated() -> None:
    migrations = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("alembic/versions").glob("*.py")
    )

    for action in AuditAction:
        assert action.value in migrations


def test_withdraw_status_enum_values_are_migrated() -> None:
    migrations = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("alembic/versions").glob("*.py")
    )

    for status in WithdrawStatus:
        assert status.value in migrations


def test_latest_migration_extends_auditaction_for_vip_adjust() -> None:
    migration = Path("alembic/versions/009_admin_audit_vip_adjust.py").read_text(encoding="utf-8")

    assert 'down_revision: str | None = "008_phase8_trial_bonus"' in migration
    assert "ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'vip_level_adjust'" in migration


def test_latest_migration_extends_withdraw_reconciliation() -> None:
    migration = Path("alembic/versions/010_withdraw_reconciliation.py").read_text(encoding="utf-8")

    assert 'down_revision: str | None = "009_admin_audit_vip_adjust"' in migration
    assert "ALTER TYPE withdrawstatus ADD VALUE IF NOT EXISTS 'failed'" in migration
    assert "ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'withdraw_confirm'" in migration
    assert "confirmations" in migration
    assert "ix_withdraw_requests_tx_hash_unique" in migration
