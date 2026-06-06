# Kairox Platform v2 — Roadmap

Stand: Juni 2026 · Release-Ziel: **v1.0.0-rc1**

## Completed (Phases 1–8 core)

| Phase | Scope | Version |
|-------|--------|---------|
| 1–2 | Monorepo, PostgreSQL, immutable ledger | 2.0–2.1 |
| 3 | Auth, CSRF, sessions, rate limits | 2.2 |
| 4 | TRC20 recharge + TronGrid watcher | 2.3 |
| 5 | Trade state machine, VIP levels | 2.4 |
| 6 | Admin, withdraw, TX verify, audit | 2.5 |
| 7 | AI gateway package + admin UI | 2.6 |
| 8 | User UI, team API, i18n, PWA manifest | 2.7 |
| 8+ | `is_official` activation, team commission | 2.7.1 |

## v1.0.0-rc1 (current milestone)

- [x] Admin VIP-adjust audit enum migration (`009_admin_audit_vip_adjust`)
- [x] Protected-route rate limits fail closed when Redis is unavailable
- [x] API container migration gate runs `alembic upgrade head` before serving
- [x] Production config validation fails fast on unsafe runtime settings
- [x] Withdraw reconciliation lifecycle (`pending` → `processing` → `completed`/`failed`)
- [x] Team valid-member rule (`is_official` at ≥ 50 USDT cumulative recharge)
- [x] Multi-level team commission on profitable trades
- [x] Docker API build includes `packages/ai-gateway`
- [x] Security audit report + deployment guide
- [x] Trial 72h + 7 USDT registration bonus
- [x] `QrCode` component (recharge + invite)
- [x] Service Worker app-shell cache
- [x] `docs/FRONTEND.md`
- [ ] Lighthouse ≥ 90 documented
- [ ] Playwright smoke suite

## Post-RC1

| Item | Priority | Notes |
|------|----------|-------|
| ERC20 / BEP20 recharge | MED | UI placeholders exist |
| VIP4–VIP6 trade levels | LOW | Align with kairox.cc |
| Full next-intl | MED | Replace lightweight hook |
| Cloud deployment (staging/prod) | HIGH | See `DEPLOYMENT.md` |
| Runner integration automation | MED | See `RUNNER_INTEGRATION.md` |
| Observability (metrics, tracing) | MED | Structured logs exist |

## Out of scope (v2)

- Modifying `kairox_runner-main/` from this repo
- Screenshot-based recharge verification
- Client-side profit calculation
