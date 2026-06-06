# Kairox Platform v2 — Security Audit Report

**Date:** 2026-06-05  
**Scope:** `kairox-platform/` (API, Web, AI Gateway)  
**Auditor:** Internal Phase 9 review  
**Release candidate:** v1.0.0-rc1

## Executive summary

The platform v2 rebuild addresses the primary weaknesses of legacy kairox.cc: missing CSRF, weak session handling, and absent audit trails. Critical money paths (ledger, recharge, withdraw, trade) enforce server-side validation and idempotency. **No critical blockers** were found for RC1; remaining items are operational hardening and UX completeness.

**Overall rating:** Acceptable for controlled staging / soft launch with monitoring.

## Methodology

1. Architecture review (routes → services → repositories)
2. Static analysis: Ruff, mypy strict, ESLint, TypeScript strict
3. Automated tests: pytest (85+), AI gateway isolated tests
4. Manual threat walkthrough per `docs/SECURITY.md`
5. Docker / dependency surface review

## Findings

### Resolved in v2

| ID | Finding | Mitigation |
|----|---------|------------|
| S-01 | Auth tokens in localStorage (legacy) | HttpOnly session cookie + in-memory JWT |
| S-02 | Missing CSRF on mutations | Double-submit cookie + header |
| S-03 | No admin audit trail | `admin_audit_log` + idempotency keys |
| S-04 | Manual recharge screenshots | TronGrid watcher only |
| S-05 | Trade profit client tampering | Server-side `calculate_profit()` |
| S-06 | Withdraw without address binding | One-time TRC20 bind + trial block |
| S-07 | TX hash replay | Unique index + ledger idempotency |
| S-08 | Team commission double-pay | `team_earnings` per trade + beneficiary |

### Low / informational

| ID | Finding | Risk | Recommendation |
|----|---------|------|----------------|
| S-09 | Auth/admin/money routes failed open if Redis was down | MED | Resolved: protected routes now fail closed with 503 while health/docs remain available |
| S-14 | Production runtime config validation was incomplete | MED | Resolved: production now fails fast on unsafe secrets, HTTP/localhost URLs, wildcard CORS, missing Tron config, insecure cookies, or non-JSON logs |
| S-15 | Withdraw approval debited ledger before on-chain settlement was confirmed | HIGH | Resolved: approval records TX hash and moves to `processing`; ledger debit occurs only on confirmation; failed processing unlocks funds |
| S-10 | AI admin endpoint sends masked PII to third parties | LOW | Keep PII mask on; document in `AI_INTEGRATION.md` |
| S-11 | No WAF / Cloudflare in repo | LOW | Configure at edge in production |
| S-12 | Service Worker not deployed | LOW | Phase 8 follow-up; do not cache API responses |
| S-13 | `mypy` legacy warnings in `tron_client.py` | LOW | Clean up post-RC1 |

### Not in scope

- Penetration test of production infrastructure
- Smart contract audit (uses standard USDT TRC20)
- Social engineering / support process review

## Regression test matrix

See `docs/SECURITY.md` § Regression tests — all cases must pass before production promote.

## Sign-off checklist

- [x] Ledger append-only enforced in repository layer
- [x] Admin mutations audited
- [x] RBAC enforced via `require_roles`
- [x] Secrets not committed (`.env.example` only)
- [x] `kairox_runner-main/` untouched by platform work
- [ ] External pentest (optional pre-GA)

## Comparison to legacy kairox.cc

| Control | Legacy | Platform v2 |
|---------|--------|-------------|
| CSRF | Often absent | Required |
| Session | Variable | HttpOnly + server session row |
| Recharge | Manual risk | Automated watcher |
| Audit | Limited | Structured log |
| Rate limits | Weak | Redis per-endpoint |
