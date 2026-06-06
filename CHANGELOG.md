# Changelog

All notable changes to Kairox Platform v2 are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0-rc1] - 2026-06-05

Release candidate — core platform feature-complete for staging.

### Added

- Phase 9 documentation: `ROADMAP.md`, `SECURITY_AUDIT_REPORT.md`, `DEPLOYMENT.md`, `RUNNER_INTEGRATION.md`, `FRONTEND.md`
- Security regression matrix in `SECURITY.md`
- `is_official` auto-activation when cumulative recharge ≥ 50 USDT
- Multi-level team commission on profitable trades (L1 10%, L2 5%, L3 2% of profit)
- Trial: 72h window (`trial_expires_at`), 7 USDT registration bonus ledger credit
- Migration `008_phase8_trial_bonus`
- Frontend: `QrCode` component, Service Worker app-shell cache
- Migration `007_phase8_team_commission` (`team_commission` ledger type)
- Docker API image builds `packages/ai-gateway` from monorepo root

### Changed

- `docker-compose.yml` API build context → monorepo root
- `TradeService` / `RechargeService` wired to activation + commission services

## [2.7.0] - 2026-06-05

### Added

- Phase 8 team referrals: migration `006`, invite codes, `GET /team/*`
- User UI: `/home`, `/account`, wallet bill/bind, team list, BottomNav, i18n de/en
- PWA manifest, `docs/HANDOVER.md`

## [2.6.0] - 2026-06-05

### Added

- Phase 7 AI Gateway: `packages/ai-gateway/` Python package (OpenAI, Anthropic, noop fallback)
- Use cases: support_assist, tx_fraud_check, security_audit
- Versioned prompts in `prompts/*.md`, PII masking, retry with backoff
- API: `POST /admin/ai/analyze`, `GET /admin/ai/health` (admin only, 20/h Redis limit)
- Admin UI `/admin/ai` with use-case selector and copy-suggested-reply
- `docs/AI_INTEGRATION.md` with architecture diagram and cost estimates

## [2.5.0] - 2026-06-05

### Added

- Phase 6 admin operations: dashboard, users, withdraw queue, trades, audit log
- RBAC: `admin` full access; `support` read + TX verify only
- Manual credit with idempotency key (ledger + audit in one transaction)
- Withdraw E2E: bind address → request → admin approve/reject
- TX verify verdicts: `CREDIT_OK`, `AMOUNT_MISMATCH`, `WRONG_ADDRESS`, `NOT_FOUND`, `ALREADY_USED`
- Migration `005_phase6_admin_operations`
- Frontend `/admin/*` console with DataTable, ManualCreditForm, TxVerifyPanel
- `docs/ADMIN_RUNBOOK.md`

### Changed

- Withdraw API: `POST /withdraw/requests` (amount only, bound address)
- `POST /wallet/bind-address` for one-time TRC20 binding
- Removed legacy `/support/verify-tx` and `/admin/withdrawals/*` routes

## [2.4.0] - 2026-06-05

### Added

- Phase 5 trade system: pre-start → start → complete flow
- State machine `idle → pre_started (60s) → running → completed | failed`
- VIP levels in `config/trade_levels.py` (VIP1–VIP3)
- Business rules: min balance, 2 trades/day, cooldown, server-side profit
- Bypass fix: start without pre_start → 403
- Migration `004_phase5_trade_system`
- Frontend: VIP level cards, confirm dialog, countdown
- Tests: bypass, expiry 410, double-start 409, daily limit, profit server-side

### Removed

- Generic `POST /trade/{id}/transition` endpoint (replaced by explicit flow)

## [2.3.0] - 2026-06-05

### Added

- Phase 4 TRC20 USDT recharge: order flow with 30 min TTL, min 30 USDT
- Endpoints: `POST/GET /recharge/orders`, `GET /recharge/orders/{id}/status`
- TronGrid client with TRC20 transfer parsing (`services/tron_client.py`)
- Background deposit watcher (15s poll, idempotent ledger credit)
- Admin/support: `GET /admin/recharge/verify?tx_hash=...`
- Anti-fraud: tx_hash unique, amount tolerance ±0.01 USDT, IDOR-protected orders
- Frontend recharge page: amount, QR, countdown, status polling
- Migration `003_phase4_recharge_orders`
- Tests: recharge service + watcher with mock TronGrid

### Changed

- Recharge credits only after on-chain verification (no screenshot/submit flow)
- `docs/api.md` and `docs/SECURITY.md` updated

## [2.2.0] - 2026-06-05

### Added

- Phase 3 auth: register (invite required), login, logout, password reset, `/me`
- `AuthService` + `SessionService` with Argon2 password hashing
- HttpOnly `kairox_session` cookie + CSRF double-submit (`kairox_csrf` / `X-CSRF-Token`)
- Redis auth rate limits: login 5/min/IP, register 3/h/IP
- `SecurityHeadersMiddleware` (CSP, HSTS, X-Frame-Options, nosniff)
- Admin audit logging on withdraw approval
- Frontend: login, register, reset-password pages; `useAuth` hook (cookie-based, no localStorage)
- Zod auth schemas mirroring Pydantic 1:1
- `docs/SECURITY.md`
- pytest: CSRF reject, rate limit, session expiry, generic login errors

### Changed

- Session-based auth replaces refresh-token-in-cookie pattern
- `packages/shared` types: `rememberMe`, required `inviteCode`

## [2.1.0] - 2026-06-05

### Added

- Phase 2 database schema: immutable `wallet_ledger`, `sessions`, `recharge_orders`, `withdraw_requests`, `trades`, `team_earnings`, `admin_audit_log`, `api_rate_limits`
- `LedgerRepository` with credit/debit/lock/unlock and negative-balance prevention
- Alembic migration `002_phase2_wallet_ledger`
- Seed: admin + kxtest01 + kxtest02
- `docs/DATABASE.md` with ER diagram
- 7+ ledger unit tests (credit, debit, lock, sum consistency)

### Changed

- Removed mutable `wallets` / `ledger_entries` tables (replaced by append-only ledger)
- Models split into feature files under `models/`
- Repositories split; all balance mutations via `LedgerRepository`

## [2.0.0] - 2026-06-05

### Added

- Monorepo scaffold (pnpm workspaces + Turborepo)
- FastAPI backend with Clean Architecture (auth, wallet, trade, recharge, withdraw, team, admin, support)
- Next.js 15 frontend with Kairox design tokens and core UI components
- Shared TypeScript contracts in `packages/shared`
- AI gateway abstraction in `packages/ai-gateway`
- PostgreSQL + Redis via Docker Compose with healthchecks
- Alembic migrations, pytest suite, GitHub Actions CI
- Security hardening: JWT httpOnly cookies, CSRF, rate limiting, trade state machine (no client bypass)
- Documentation in `docs/`
