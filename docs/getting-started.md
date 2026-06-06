# Getting Started

## Prerequisites

- Node.js 20+
- pnpm 9+
- Python 3.12+
- Docker & Docker Compose

## Setup

```bash
cd kairox-platform
cp .env.example .env
make docker-up          # PostgreSQL + Redis
make install            # pnpm + pip
make migrate            # Alembic
make seed               # admin + kxtest01 test accounts
make dev                # web :3000 + api :8000
```

## Test Accounts (after seed)

| User | Password | Role | Balance |
|------|----------|------|---------|
| admin | KairoxTest2026 | admin | 0 USDT |
| kxtest01 | KairoxTest2026 | user | 1000 USDT |
| kxtest02 | KairoxTest2026 | user | 500 USDT |

See [DATABASE.md](./DATABASE.md) for full schema documentation.

## URLs

- Web: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start all dev servers |
| `make test` | Run all tests |
| `make lint` | Lint all packages |
| `make typecheck` | TypeScript + mypy |
| `make migrate` | Apply DB migrations |
| `make seed` | Seed dev data |

## Environment

See `.env.example` for all variables with descriptions.

Required for production:

- `JWT_SECRET` — generate with `openssl rand -hex 32`
- `CSRF_SECRET` — separate secret
- `TRONGRID_API_KEY` — for recharge verification
- `TRON_DEPOSIT_ADDRESS` — platform wallet
