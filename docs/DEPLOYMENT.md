# Kairox Platform v2 — Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2
- Node 20 + pnpm 9 (local dev)
- Python 3.12 (local dev)
- PostgreSQL 16 and Redis 7 (or use Compose)

## Environment

Copy `.env.example` to `.env` and set at minimum:

| Variable                         | Production                                           |
| -------------------------------- | ---------------------------------------------------- |
| `JWT_SECRET`                     | ≥ 32 random chars                                    |
| `CSRF_SECRET`                    | Unique, not dev default                              |
| `COOKIE_SECURE`                  | `true`                                               |
| `APP_ENV`                        | `production`                                         |
| `WEB_URL`                        | Public HTTPS frontend origin, not localhost          |
| `API_URL`                        | Public HTTPS API origin, not localhost               |
| `CORS_ORIGINS`                   | HTTPS origins, must include `WEB_URL`, no `*`        |
| `DATABASE_URL`                   | PostgreSQL async URL                                 |
| `REDIS_URL`                      | Redis URL                                            |
| `KAIROX_RUN_MIGRATIONS`          | `true` unless a separate release job runs migrations |
| `KAIROX_MIGRATION_ATTEMPTS`      | Retry count for startup migrations                   |
| `KAIROX_MIGRATION_RETRY_SECONDS` | Sleep between migration retries                      |
| `TRON_DEPOSIT_ADDRESS`           | Hot wallet deposit address                           |
| `TRONGRID_API_KEY`               | TronGrid API key                                     |
| `LOG_JSON`                       | `true`                                               |
| `NEXT_PUBLIC_API_URL`            | Public API origin (browser)                          |

Optional AI: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`.

Production startup validates these values before the API serves. Invalid secrets,
HTTP/localhost URLs, wildcard CORS, missing Tron configuration, insecure cookies,
or non-JSON logging fail fast.

## Docker Compose (full stack)

From repo root `kairox-platform/`:

```bash
docker compose up -d --build
```

Services:

| Service  | Port | Notes                                   |
| -------- | ---- | --------------------------------------- |
| postgres | 5432 | Persistent volume                       |
| redis    | 6379 | Sessions + rate limits                  |
| api      | 8000 | Includes `packages/ai-gateway` in image |
| web      | 3000 | Next.js production build                |

Health: `curl http://localhost:8000/health`

The web Docker image enables `KAIROX_WEB_STANDALONE=true` during build so Next.js
emits `.next/standalone` for the runner image. Keep this unset for local Windows
builds to avoid symlink permission failures in OneDrive or non-admin shells.

The API image runs `alembic upgrade head` through `apps/api/docker-entrypoint.sh`
before Uvicorn starts. Startup fails if migrations cannot complete after the
configured retry budget. This prevents serving traffic against an old database
schema.

## Database migrations

```bash
cd apps/api
alembic upgrade head   # through 010_withdraw_reconciliation
```

For production platforms that use a separate release migration job, set
`KAIROX_RUN_MIGRATIONS=false` only after the release job is proven to run
`alembic upgrade head` successfully before API traffic is shifted.

Seed admin + test users:

```bash
python -m kairox_api.scripts.seed
```

Default credentials: see `docs/getting-started.md`.

## Local development (without Docker)

```bash
make install
docker compose up -d postgres redis
make migrate
make seed
make dev
```

API: `http://localhost:8000` · Web: `http://localhost:3000`

If you want to verify a local production build on Windows, run plain
`pnpm --filter @kairox/web build` without `KAIROX_WEB_STANDALONE=true`.

## CI parity

GitHub Actions runs: lint, typecheck, migrate, pytest (≥80% on features/repos), web tests, build.
Deployment artifact tests assert that the API image contains Alembic files and
uses the migration entrypoint before Uvicorn.

## Production notes

1. Terminate TLS at reverse proxy (nginx, Caddy, Cloudflare).
2. Set `WEB_URL` and `API_URL` for CSP `connect-src`.
3. Run API with multiple workers only after verifying advisory locks on ledger.
4. Back up PostgreSQL daily; ledger is append-only — restore = point-in-time recovery.
5. Monitor TronGrid watcher logs and pending recharge count via admin dashboard.
6. Do **not** commit `.env` or production secrets.

## Rollback

1. Stop traffic to new API revision.
2. `alembic downgrade -1` only if migration is reversible. Enum additions such as
   `007_phase8_team_commission`, `008_phase8_trial_bonus`, and
   `009_admin_audit_vip_adjust` / `010_withdraw_reconciliation` enum additions
   are not safely reversible without recreating the
   PostgreSQL enum type.
3. Restore DB snapshot if schema/data incompatible.

## Post-deploy smoke

1. Register with valid invite code → login → `/home`
2. Create recharge order → watcher credits (or admin TX verify read-only)
3. Trade pre-start → start → complete
4. Admin login → dashboard → audit log entry on manual action
