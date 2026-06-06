# Kairox Platform v2 — Security

This document describes authentication, session management, and security controls implemented in Phase 3. It is the authoritative reference for reviewers and operators.

## Threat model (summary)

| Threat | Mitigation |
|--------|------------|
| Credential stuffing | Redis rate limits on login (5/min/IP) and register (3/h/IP) |
| User enumeration | Generic login and password-reset responses |
| XSS token theft | HttpOnly session cookie; JWT access token only in memory |
| CSRF | Double-submit cookie + `X-CSRF-Token` header on state-changing requests |
| Session fixation | New session token issued on login/register |
| Weak passwords | Argon2 hashing (bcrypt fallback for legacy hashes) |
| Clickjacking | `X-Frame-Options: DENY`, CSP `frame-ancestors 'none'` |
| MIME sniffing | `X-Content-Type-Options: nosniff` |
| Downgrade attacks | HSTS in production |

## Authentication endpoints

All routes are prefixed with `/api/v1/auth`.

| Method | Path | Auth | CSRF | Rate limit |
|--------|------|------|------|------------|
| POST | `/register` | No | Yes | 3/h/IP |
| POST | `/login` | No | Yes | 5/min/IP |
| POST | `/logout` | Session | Yes | — |
| POST | `/reset-password/request` | No | Yes | — |
| POST | `/reset-password/confirm` | No | Yes | — |
| GET | `/me` | Session or Bearer | No | — |

### Registration

- **Invite code required** — registration fails with a generic message if the code is invalid or the username/email is taken.
- User is assigned to the team associated with the invite code.
- On success: DB session created, HttpOnly cookie set, short-lived JWT returned in JSON (for API clients).

### Login

- Accepts `username`, `password`, optional `remember_me`.
- **Always returns the same error message** for wrong username or password: `Invalid username or password` (HTTP 401).
- `remember_me` extends session TTL (30 days vs 24 hours); it does **not** store credentials client-side.

### Logout

- Revokes the server-side session and clears session + CSRF cookies.

### Password reset

- **Request**: accepts email; always responds with a generic success message whether or not the account exists.
- **Confirm**: accepts one-time token (Redis, 1 h TTL) and new password; invalid/expired tokens return 400.

### Current user (`/me`)

- Validates session cookie or `Authorization: Bearer <access_token>`.
- Returns user profile and fresh tokens when authenticated via session.

## Session model

```
Browser                    API                         PostgreSQL / Redis
   |                        |                                |
   |-- POST /login -------->| create UserSession row         |
   |                        | hash(session_token) stored     |
   |<-- Set-Cookie ---------| kairox_session (HttpOnly)      |
   |    kairox_csrf         |                                |
   |                        |                                |
   |-- POST /trade -------->| validate CSRF + session        |
   |   Cookie + X-CSRF      | lookup session by token hash   |
```

### Cookies

| Cookie | Purpose | Flags |
|--------|---------|-------|
| `kairox_session` | Opaque session token | `HttpOnly`, `Secure` (prod), `SameSite=Strict`, `Path=/` |
| `kairox_csrf` | CSRF double-submit | **Not** HttpOnly (JS reads for header), same Site/Secure flags |

Session TTL constants (`constants/limits.py`):

- Default: **24 hours** (`SESSION_TTL_SECONDS`)
- Remember me: **30 days** (`SESSION_REMEMBER_TTL_SECONDS`)

### JWT access token

- Short-lived (default 30 min, `JWT_ACCESS_TTL_MINUTES`).
- Returned in login/register/me JSON for in-memory use by the SPA.
- **Never** stored in `localStorage` or `sessionStorage` by the official frontend.

## Password hashing

Implementation: `core/password.py`

- **Primary**: Argon2id via `argon2-cffi`.
- **Fallback verify**: bcrypt for hashes created before Phase 3 migration.
- New passwords are always hashed with Argon2.

## CSRF protection

Implementation: `core/cookies.py`

1. On login/register, server sets `kairox_csrf` cookie.
2. Frontend reads cookie and sends value in `X-CSRF-Token` on `POST`, `PUT`, `PATCH`, `DELETE`.
3. Server compares cookie and header; mismatch → HTTP 403.

Safe methods (`GET`, `HEAD`, `OPTIONS`) skip CSRF validation.

## Rate limiting

### Auth-specific (Redis)

| Action | Key pattern | Limit | Window |
|--------|-------------|-------|--------|
| Login | `auth:login:{ip}` | 5 | 60 s |
| Register | `auth:register:{ip}` | 3 | 3600 s |

Exceeded → HTTP 429, `RATE_LIMITED`.

### Global API (Redis)

Configured via `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` (default 100/min/IP).

If Redis is unavailable, auth rate limits fail closed. The global limiter also fails
closed for authenticated, admin, wallet, withdraw, trade, recharge, and team API
paths. Health/docs endpoints remain available so operators can diagnose the
outage without weakening protected routes.

## Security headers

`SecurityHeadersMiddleware` adds on every response:

- `Content-Security-Policy` — restrictive default; `connect-src` includes `WEB_URL` and `API_URL`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` — disables camera, microphone, geolocation
- `Strict-Transport-Security` — **production only** (`max-age=31536000; includeSubDomains`)

## Admin audit log

Admin actions that mutate state (e.g. withdraw approval) write to `admin_audit_log` via `AuditRepository`:

- `admin_user_id`, `action`, `target_type`, `target_id`, `metadata`, `created_at`

Audit entries are append-only from application code.

## Recharge security (Phase 4)

| Control | Implementation |
|---------|----------------|
| No manual/screenshot credit | Ledger credit only via background watcher after TronGrid verification |
| TX replay prevention | Unique `tx_hash` index; duplicate hashes rejected |
| Amount tampering | On-chain amount must match order `expected_amount` within ±0.01 USDT |
| IDOR | `GET /recharge/orders/{id}` scoped to authenticated `user_id` |
| Order enumeration | UUID order IDs; no public listing without auth |
| Time-bound orders | 30-minute `expires_at`; expired orders never credited |
| Idempotent credit | `ledger.entry_exists(reference_id)` before credit; safe watcher retries |

TronGrid polling runs server-side every 15 seconds (`RECHARGE_POLL_INTERVAL_SECONDS`). Frontend only polls order status — no blockchain logic in the browser.

### Official user activation (Phase 8)

| Control | Implementation |
|---------|----------------|
| Trial vs official | `users.is_official` defaults `false` |
| Trial window | `trial_expires_at` = register + 72h (`TRIAL_DURATION_HOURS`) |
| Registration bonus | 7 USDT ledger credit once (`registration_bonus`, idempotent) |
| Activation threshold | Cumulative `RECHARGE` ledger credits ≥ 50 USDT (`TEAM_VALID_MIN_DEPOSIT`) |
| Trigger official | `UserActivationService.maybe_activate_official()` after watcher credit |
| Trial trade block | `TrialService.assert_trial_active()` on trade pre-start |
| Withdraw gate | `BLOCK_TRIAL_WITHDRAW=true` blocks non-official withdrawals |

## Team security (Phase 8)

| Control | Implementation |
|---------|----------------|
| Referral depth | Max 3 levels via `referrer_id` chain |
| Valid member stats | `count_valid_referrals` uses `is_official` |
| Commission basis | Server-side % of trade **profit** only (`TEAM_COMMISSION_RATES`) |
| Eligible trades | Trader must be `is_official`; profit > 0 |
| Double payout | `team_earnings` unique per `(trade_id, beneficiary_user_id)` + ledger idempotency |
| Ledger type | `team_commission` entry credits beneficiary wallet |

## Trade security (Phase 5)

| Control | Implementation |
|---------|----------------|
| Pre-start bypass | `POST /trade/start` requires `pre_started` state — direct start returns **403** |
| Pre-start expiry | 60s TTL; expired session returns **410** |
| Double start | Second start on running trade → **409** |
| Daily limit | Max 2 completed trades/day (`MAX_TRADES_PER_DAY`) |
| Cooldown | `TRADE_COOLDOWN_SECONDS` between trades |
| Profit tampering | Profit computed in `config/trade_levels.py` on complete — no client input |

## Frontend security

- All auth state in `hooks/useAuth.tsx` — **no auth logic in page components**.
- Zod schemas in `lib/validations/auth.ts` mirror Pydantic schemas 1:1.
- API client uses `credentials: 'include'` for cookies.
- German user-facing errors; generic messages for auth failures.

## Environment variables

See `.env.example`. Production **must** set:

| Variable | Requirement |
|----------|-------------|
| `JWT_SECRET` | ≥ 32 chars, not dev default |
| `CSRF_SECRET` | ≥ 32 chars, unique, not dev default |
| `COOKIE_SECURE` | `true` (HTTPS only) |
| `APP_ENV` | `production` triggers validation |
| `WEB_URL`, `API_URL` | HTTPS origins, not localhost |
| `CORS_ORIGINS` | HTTPS origins, no wildcard, includes `WEB_URL` |
| `TRON_DEPOSIT_ADDRESS` | Required valid TRON address |
| `TRONGRID_API_KEY` | Required when recharge watcher is enabled |
| `LOG_JSON` | `true` for production auditability |

## RBAC matrix (Phase 6)

| Endpoint / action | user | support | admin |
|-------------------|:----:|:-------:|:-----:|
| `/admin/dashboard` | — | read | read |
| `/admin/users` (list/detail) | — | read | read |
| `/admin/users/{id}/manual-credit` | — | — | **write** |
| `/admin/users/{id}/adjust-vip` | — | — | **write** |
| `/admin/recharge/verify` | — | read | read |
| `/admin/withdraw/requests` (list) | — | read | read |
| `/admin/withdraw/requests/{id}/approve` | — | — | **write** |
| `/admin/withdraw/requests/{id}/confirm` | — | — | **write** |
| `/admin/withdraw/requests/{id}/fail` | — | — | **write** |
| `/admin/withdraw/requests/{id}/reject` | — | — | **write** |
| `/admin/trades`, `/admin/audit` | — | read | read |
| `/wallet/bind-address`, `/withdraw/requests` | write | — | — |

### Audit policy

Every admin **mutation** (manual credit, VIP adjust, withdraw approve/confirm/fail/reject) writes exactly one row to `admin_audit_log` with:

- `actor_id`, `action`, `target_type`, `target_id`
- `ip_address`, `user_agent`
- `payload_json` (amount, reason, notes, idempotency key where applicable)

Manual credits additionally store idempotency keys in `admin_idempotency_keys` to prevent duplicate ledger entries.

## Regression tests

Run before every production promote (`make test` or CI):

| Area | Test file | Cases |
|------|-----------|-------|
| Auth / CSRF | `test_auth_security.py` | CSRF reject, generic errors, rate limit |
| Ledger | `test_ledger_repository_async.py` | Credit, debit, lock, negative balance blocked |
| Recharge | `test_recharge_service.py` | Min amount, IDOR, watcher credit, TX replay |
| Trade | `test_trade_service.py` | Pre-start bypass, daily limit, server profit |
| Withdraw | `test_withdraw_service.py`, `test_admin_phase6.py` | Trial block, processing/confirm/fail/reject ledger order |
| Admin | `test_admin_phase6.py` | Manual credit idempotency, TX verify verdicts |
| Team activation | `test_user_activation_service.py` | 50 USDT threshold, idempotent |
| Team commission | `test_team_commission_service.py` | Official-only, L1 payout, idempotent |
| Registration bonus | `test_registration_bonus_service.py` | 7 USDT once, idempotent |
| Trial expiry | `test_trial_service.py` | Blocks expired trial trades |
| AI gateway | `packages/ai-gateway/tests/` | PII mask, provider fallback |

Manual smoke (staging):

1. Register → login → `/home`
2. Recharge order → paid status (or TX verify read-only)
3. Trade full cycle
4. Admin audit log after mutation

## Testing

Security-related pytest coverage (`tests/test_auth_security.py`):

- CSRF rejection on logout without token
- Generic invalid-credentials message
- Session expiry returns unauthenticated
- Login rate limit enforcement (mocked Redis)

Run full suite:

```bash
make test
make lint
```

## Comparison to legacy kairox.cc

| Area | Legacy risk | Platform v2 |
|------|-------------|---------------|
| Token storage | localStorage common | HttpOnly cookie + memory-only JWT |
| CSRF | Often missing | Mandatory on mutations |
| Rate limits | Weak/absent | Redis per-endpoint limits |
| Password hash | Variable | Argon2id standard |
| Error messages | User enumeration | Generic auth errors |
| Security headers | Minimal | CSP, HSTS, frame denial |
| Audit | Limited | Structured admin audit log |

## Reporting vulnerabilities

Do not open public GitHub issues for security bugs. Contact the platform maintainers directly with steps to reproduce and impact assessment.
