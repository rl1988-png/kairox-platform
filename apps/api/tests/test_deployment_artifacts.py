from pathlib import Path


def test_api_dockerfile_runs_migrations_before_uvicorn() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "COPY apps/api/alembic.ini /app/apps/api/alembic.ini" in dockerfile
    assert "COPY apps/api/alembic /app/apps/api/alembic" in dockerfile
    assert "COPY apps/api/docker-entrypoint.sh" in dockerfile
    assert 'ENTRYPOINT ["/app/apps/api/docker-entrypoint.sh"]' in dockerfile
    assert 'CMD ["uvicorn", "kairox_api.main:app"' in dockerfile


def test_api_entrypoint_enforces_alembic_upgrade_head() -> None:
    entrypoint = Path("docker-entrypoint.sh").read_text(encoding="utf-8")

    assert "alembic upgrade head" in entrypoint
    assert "KAIROX_RUN_MIGRATIONS" in entrypoint
    assert "KAIROX_MIGRATION_ATTEMPTS" in entrypoint
    assert 'exec "$@"' in entrypoint


def test_compose_exposes_api_migration_gate_controls() -> None:
    compose = Path("../../docker-compose.yml").read_text(encoding="utf-8")

    assert "KAIROX_RUN_MIGRATIONS" in compose
    assert "KAIROX_MIGRATION_ATTEMPTS" in compose
    assert "KAIROX_MIGRATION_RETRY_SECONDS" in compose


def test_dockerignore_excludes_secrets_and_generated_artifacts() -> None:
    dockerignore = Path("../../.dockerignore").read_text(encoding="utf-8")

    assert ".env" in dockerignore
    assert "!.env.example" in dockerignore
    assert "**/__pycache__/" in dockerignore
    assert "**/*.pyc" in dockerignore
    assert "**/node_modules" in dockerignore
    assert "apps/web/.next" in dockerignore
