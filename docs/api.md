# API Reference

Base URL: `/api/v1`

## Auth

| Method | Path | Auth | CSRF | Description |
|--------|------|------|------|-------------|
| POST | `/auth/register` | — | ✓ | Create account (invite required) |
| POST | `/auth/login` | — | ✓ | Login |
| POST | `/auth/logout` | ✓ | ✓ | Logout |
| POST | `/auth/reset-password/request` | — | ✓ | Request password reset |
| POST | `/auth/reset-password/confirm` | — | ✓ | Confirm password reset |
| GET | `/auth/me` | ✓ | — | Current user + session refresh |

## Wallet

| Method | Path | Description |
|--------|------|-------------|
| GET | `/wallet` | Balance summary |
| GET | `/wallet/ledger` | Ledger entries |
| GET | `/wallet/deposit-info` | Platform deposit address (legacy info) |

## Trade (Phase 5 — Pre-Start required)

| Method | Path | CSRF | Description |
|--------|------|------|-------------|
| GET | `/trade/levels` | — | VIP level cards + eligibility |
| GET | `/trade/active` | — | Active pre_started or running trade |
| POST | `/trade/pre-start` | ✓ | Reserve trade (60s TTL) `{ vip_level }` |
| POST | `/trade/start` | ✓ | Start locked trade `{ trade_id }` — **pre_started only** |
| POST | `/trade/complete` | ✓ | Settle after runtime `{ trade_id }` |

### State machine

`idle → pre_started (60s) → running → completed | failed`

**Bypass fix:** `POST /trade/start` without valid `pre_started` session returns **403**. Expired pre-start returns **410**.

### Business rules (server-side)

- VIP levels in `config/trade_levels.py`
- Min balance per level before pre-start
- Max **2 trades/day** per account
- Cooldown between trades (`TRADE_COOLDOWN_SECONDS`)
- Profit calculated server-side on complete — client cannot set profit

## Recharge (Phase 4 — TRC20 USDT)

| Method | Path | CSRF | Description |
|--------|------|------|-------------|
| POST | `/recharge/orders` | ✓ | Create order (min 30 USDT, 30 min TTL) |
| GET | `/recharge/orders/{id}` | — | Order details (owner only) |
| GET | `/recharge/orders/{id}/status` | — | Lightweight status polling |

### Create order

```json
POST /recharge/orders
{ "amount": "50", "network": "TRC20" }
```

Response includes `deposit_address`, `expected_amount`, `expires_at`, `status: pending`.

### Status values

| Status | Meaning |
|--------|---------|
| `pending` | Waiting for on-chain payment |
| `confirming` | TX detected, awaiting confirmations |
| `paid` | Verified and credited to ledger |
| `expired` | Order TTL elapsed without payment |

Background worker polls TronGrid every **15 seconds**. Credit occurs only after:

- `to_address` matches order deposit address
- Token contract = USDT TRC20
- Amount within **±0.01 USDT** of expected amount
- Confirmations ≥ `TRON_MIN_CONFIRMATIONS` (default 19)
- `tx_hash` unique (no replay)

## Withdraw (Phase 6)

| Method | Path | CSRF | Description |
|--------|------|------|-------------|
| POST | `/wallet/bind-address` | ✓ | Bind TRC20 withdrawal address (once) |
| POST | `/withdraw/requests` | ✓ | Request withdrawal `{ amount }` |
| GET | `/withdraw/history` | — | History |

Rules: min 10 USDT, fee 1 USDT, max 1 pending request, trial users blocked when `BLOCK_TRIAL_WITHDRAW=true`.

## Admin (Phase 6)

| Method | Path | Role | CSRF | Description |
|--------|------|------|------|-------------|
| GET | `/admin/dashboard` | admin/support | — | KPI dashboard |
| GET | `/admin/users` | admin/support | — | User search + pagination |
| GET | `/admin/users/{id}` | admin/support | — | User detail |
| POST | `/admin/users/{id}/manual-credit` | **admin** | ✓ | Ledger credit + audit (idempotent) |
| POST | `/admin/users/{id}/adjust-vip` | **admin** | ✓ | VIP level adjustment |
| GET | `/admin/recharge/verify?tx_hash=` | admin/support | — | On-chain TX verdict |
| GET | `/admin/withdraw/requests?status=` | admin/support | — | Withdraw queue |
| POST | `/admin/withdraw/requests/{id}/approve` | **admin** | ✓ | Attach payout TX hash + move to `processing` |
| POST | `/admin/withdraw/requests/{id}/confirm` | **admin** | ✓ | Confirm on-chain payout + debit ledger |
| POST | `/admin/withdraw/requests/{id}/fail` | **admin** | ✓ | Mark failed + unlock funds |
| POST | `/admin/withdraw/requests/{id}/reject` | **admin** | ✓ | Reject + unlock funds |
| GET | `/admin/trades` | admin/support | — | Recent trades |
| GET | `/admin/audit` | admin/support | — | Audit log |

### TX verify verdicts

`CREDIT_OK` · `AMOUNT_MISMATCH` · `WRONG_ADDRESS` · `NOT_FOUND` · `ALREADY_USED`

### Manual credit body

```json
{
  "amount": "100.00",
  "reason": "Support compensation #1234",
  "idempotency_key": "uuid"
}
```

## Support (removed legacy POST)

Use `GET /admin/recharge/verify?tx_hash=...` instead of screenshot flow.

## AI (Phase 7)

| Method | Path | Role | CSRF | Description |
|--------|------|------|------|-------------|
| POST | `/admin/ai/analyze` | **admin** | ✓ | Run AI use case (20/h limit) |
| GET | `/admin/ai/health` | **admin** | — | Provider health + fallback |

Use cases: `support_assist`, `tx_fraud_check`, `security_audit`. See `docs/AI_INTEGRATION.md`.

## Error format

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Recharge order not found",
    "details": {}
  }
}
```
