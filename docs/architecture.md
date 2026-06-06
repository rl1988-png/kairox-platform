# Kairox Platform v2 — Architecture

## Overview

Monorepo with strict layer separation:

```
apps/web          → Next.js 15 (UI, no business logic)
apps/api          → FastAPI (routes → services → repositories → models)
packages/shared   → TypeScript contracts (Frontend ↔ Backend)
packages/ai-gateway → Optional AI provider abstraction
```

## Backend Layers

| Layer | Responsibility | Example |
|-------|---------------|---------|
| `routes/` | HTTP, CSRF, auth deps | `features/auth/routes.py` |
| `services/` | Business rules | `features/trade/service.py` |
| `repositories/` | DB access only | `repositories/user_wallet.py` |
| `models/` | SQLAlchemy entities | `models/entities.py` |

**Rule:** Routes never contain business logic. Services never execute raw SQL.

## Trade State Machine

- Removed: generic `POST /trade/{id}/transition` (Phase 5 uses explicit pre-start/start/complete)

All trade transitions are validated server-side via `features/trade/services/trade_state_machine.py`:

`idle → pre_started (60s TTL) → running → completed | failed`

Starting without pre-start returns **403** (fixes kairox.cc bypass).

```
idle → pending_funds → ready → running → settling → completed
                    ↘ cancelled          ↘ failed
```

Client cannot skip states (fixes v1 bypass vulnerability).

## Security Improvements vs v1

| v1 Issue | v2 Fix |
|----------|--------|
| Trade state bypass | Server state machine |
| No rate limiting | Redis-backed middleware |
| Password in localStorage | sessionStorage token only + httpOnly refresh cookie |
| No CSRF | Double-submit cookie pattern |
| Screenshot credit | On-chain TronGrid verification |

## Error Format

All API errors:

```json
{
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "Insufficient available balance",
    "details": {}
  }
}
```

## Database

PostgreSQL 16 with Alembic migrations. Phase 2 uses an **immutable append-only ledger** (`wallet_ledger`) as the balance source of truth.

See [DATABASE.md](./DATABASE.md) for ER diagram and table reference.

## Caching

Redis for rate limiting and future session/cache use.
