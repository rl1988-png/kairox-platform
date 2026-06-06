# Kairox Runner Integration

The **Kairox Runner** (`kairox_runner-main/`) is a separate Playwright/Python automation project used for trade demos and training. **This monorepo does not modify the runner.**

## Relationship

```
kairox-platform/          ← Production v2 (FastAPI + Next.js)
kairox_runner-main/       ← Automation / demos (reference only)
```

| Component | Platform v2 | Runner |
|-----------|-------------|--------|
| Trade execution | Server state machine | Browser automation |
| Wallet / ledger | PostgreSQL ledger | N/A |
| Test accounts | `seed.py` (admin, kxtest01–02) | lewe, kxtest01–07 |

Shared test password convention: `KairoxTest2026` (change in production).

## Integration options (post-RC1)

1. **API-driven runner** — Point runner at `NEXT_PUBLIC_API_URL`; use session auth + CSRF like the web app.
2. **Demo mode** — Runner continues fake Bitpanda/TronScan screenshots in `tools/` for training; no platform coupling.
3. **CI smoke** — Optional Playwright job against staging URL (not yet in CI).

## Verification

Ensure platform work did not touch runner files:

```bash
# From workspace parent — adjust path if runner exists
git diff -- kairox_runner-main/
```

Expected: no changes from platform development.

## Live reference

Production legacy site: https://kairox.cc — used for UX parity only; v2 reimplements flows with stricter security.
