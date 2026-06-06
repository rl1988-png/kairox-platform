# Kairox Platform v2 — Handover

Stand: **Juni 2026** · Workspace: `kairox-platform/` (nicht anfassen: `kairox_runner-main/`)

Dieses Dokument fasst zusammen, **was implementiert wurde**, **wie es zusammenhängt**, und **was noch fehlt** für Release-Readiness.

---

## 1. Phasen-Übersicht

| Phase | Thema                                  | Status    | Version   |
| ----- | -------------------------------------- | --------- | --------- |
| 1–2   | Monorepo, DB, Ledger, Wallet           | ✅ Fertig | 2.0–2.1   |
| 3     | Auth, CSRF, Rate-Limits, Sessions      | ✅ Fertig | 2.2       |
| 4     | TRC20 Recharge, TronGrid Watcher       | ✅ Fertig | 2.3       |
| 5     | Trade State-Machine, VIP-Levels        | ✅ Fertig | 2.4       |
| 6     | Admin, Withdraw, TX-Verify, Audit      | ✅ Fertig | 2.5       |
| 7     | AI-Gateway Package                     | ✅ Fertig | 2.6       |
| 8     | User-UI, Team, PWA, i18n, kairox.cc UI | 🟡 ~95%   | 2.7       |
| 9     | Final-Audit, Hardening, Release        | 🟡 RC1    | 1.0.0-rc1 |

---

## 2. Architektur (kurz)

```
apps/web (Next.js 15)  ──HTTP+CSRF──►  apps/api (FastAPI)
                                           │
                    routes → services → repositories → models
                                           │
                              PostgreSQL + Redis
packages/shared     — TypeScript-Typen (API-Contracts)
packages/ai-gateway — isoliertes Python-Paket (Provider-agnostisch)
```

**Regeln (durchgängig):**

- Keine Business-Logik in Routes/UI
- Geld: `DECIMAL(18,8)`, nie `float`
- Errors: `{ "error": { "code", "message", "details" } }`
- Design: Tailwind-Tokens (`bg-kairox-pink`, `bg-bg-primary`), kein hardcoded `#fc81b9`

---

## 3. Was eingebaut wurde (Detail)

### 3.1 Backend API (`apps/api/`)

#### Auth & Security (Phase 3)

- Register/Login/Logout, Argon2, HttpOnly Session-Cookie
- CSRF Double-Submit (`kairox_csrf` + `X-CSRF-Token`)
- Redis Rate-Limits: Login 5/min, Register 3/h
- Password Reset (Redis Token, 1h TTL)

#### Wallet & Ledger (Phase 2)

- Append-only `wallet_ledger`, advisory locks pro User
- `GET /wallet`, `GET /wallet/ledger`
- `POST /wallet/bind-address` (TRC20, einmalig)

#### Recharge (Phase 4)

- `POST/GET /recharge/orders`, 30 USDT min, 30 min TTL
- TronGrid Watcher (15s), idempotente Gutschrift
- Kein Screenshot-Flow

#### Trade (Phase 5)

- Flow: `pre-start` → 60s → `start` → `complete`
- VIP-Levels **VIP1–VIP3** in `config/trade_levels.py`
- Bypass-Fix: Start ohne Pre-Start → 403

#### Admin & Withdraw (Phase 6)

- Admin-Dashboard, Users, Manual-Credit (idempotent), VIP-Adjust
- Withdraw: bind → request → approve(TX hash) → confirm/fail oder reject (Ledger + Audit)
- TX-Verify mit Verdicts (`CREDIT_OK`, `AMOUNT_MISMATCH`, …)
- Audit-Log filterbar
- Migration `005_phase6_admin`, `009_admin_audit_vip_adjust`
- Migration `010_withdraw_reconciliation`: Processing/Confirm/Fail mit TX-Hash, Confirmations und Settlement-Zeitstempeln

#### AI-Gateway (Phase 7)

- Paket `packages/ai-gateway/` (Python, pytest-isoliert)
- Use Cases: `support_assist`, `tx_fraud_check`, `security_audit`
- Provider: OpenAI, Anthropic, noop-Fallback
- PII-Maskierung, Retry, versionierte Prompts `.md`
- `POST /admin/ai/analyze`, `GET /admin/ai/health` (admin, 20/h)

#### Team & Post-RC1 (Phase 8)

- Migration `006_phase8_team`: `users.invite_code`, `users.referrer_id`
- Migration `007_phase8_team_commission` (`team_commission` Ledger-Typ)
- Migration `008_phase8_trial_bonus`: `trial_expires_at`, Registrierungsbonus
- `GET /team`, `/team/stats`, `/team/members`, `/team/unfinished`
- `UserActivationService`: `is_official=true` bei kumulierter Recharge ≥ 50 USDT
- `TeamCommissionService`: L1 10% / L2 5% / L3 2% vom Trade-Profit
- `RegistrationBonusService`: einmalig 7 USDT bei Register (Ledger)
- `TrialService`: 72h Trial, blockiert Trade wenn abgelaufen

### 3.2 Frontend (`apps/web/`)

#### User-Bereich

| Route                                     | Status | Hinweis                                          |
| ----------------------------------------- | ------ | ------------------------------------------------ |
| `/login`, `/register`, `/reset-password`  | ✅     | kairox.cc AuthLayout, Tabs, Roboter              |
| `/download`, `/info/privacy`              | ✅     | PWA-Hinweis + Privacy (Platzhalter-Text)         |
| `/home`                                   | ✅     | Balance-Hero, Action-Tiles, Announcement         |
| `/trade`                                  | ✅     | VIP-Cards, Countdown, Pill-Buttons               |
| `/wallet`, `/wallet/bill`, `/wallet/bind` | ✅     | SubNav + PageBanner                              |
| `/recharge`, `/withdraw`                  | ✅     | QR, Polling, Wallet-SubNav                       |
| `/team`, `/team/list`                     | ✅     | Stats, echte Mitgliederliste, L1-L3/Offen-Filter |
| `/account`, `/account/invite`             | ✅     | Mine-Tab, Invite-QR                              |
| `/`, `/dashboard`                         | ✅     | Redirect → `/login` bzw. `/home`                 |

#### Navigation (kairox.cc)

- **Bottom bar (5 Tabs):** Home · Wallet · **Trade (Mitte, groß)** · Team · Mine
- **Wallet-SubNav:** Balance · Recharge · Withdraw · Bill · Address
- **Team-SubNav:** Mein Team · Statistik · Invite
- **Account-SubNav:** Profil · Invite · Passwort
- Zentral: `src/lib/navigation.ts`, `SubNavTabs`, `BottomNav` (`.wa-footer`)

#### Admin-Bereich

| Route                                        | Status                  |
| -------------------------------------------- | ----------------------- |
| `/admin`                                     | ✅ Dashboard + StatGrid |
| `/admin/users`                               | ✅ + ManualCredit       |
| `/admin/recharge`                            | ✅ TX-Verify            |
| `/admin/withdraw`                            | ✅ Approve/Reject       |
| `/admin/trades`, `/admin/audit`, `/admin/ai` | ✅                      |

AdminShell: Logo, pink Nav, Mobile-Pill-Tabs, `AdminPageHeader` auf allen Seiten.

#### UI-Komponenten & Assets

| Komponente                               | Pfad / Hinweis                                                    |
| ---------------------------------------- | ----------------------------------------------------------------- |
| `AuthLayout`, `AppShell`, `MobileHeader` | kairox.cc Look                                                    |
| `KairoxRobot`, `FloatingServiceBot`      | `/assets/kairox/service.png`, draggable                           |
| `PageBanner`, `PageHeader`, `SubNavTabs` | Pink Hero + Unter-Tabs                                            |
| `QrCode`                                 | Recharge + Invite                                                 |
| `BottomNav`                              | 5-Tab `.wa-footer`                                                |
| Assets                                   | `public/assets/kairox/` (logo, login-bg, icons)                   |
| PWA                                      | `manifest.json`, `sw.js`, `ServiceWorkerRegister`, `icon-192/512` |
| i18n                                     | `messages/de.json`, `en.json` + `useTranslations()`               |

#### Technische Frontend-Fixes

- `themeColor` → `viewport` Export (Next.js 15)
- `outputFileTracingRoot` in `next.config.ts` (Monorepo-Warnung)
- `KAIROX_WEB_STANDALONE=true` nur fuer Docker-Build; lokaler Windows-Build ohne Standalone

### 3.3 Dokumentation

| Datei                                                          | Inhalt                  |
| -------------------------------------------------------------- | ----------------------- |
| `docs/api.md`                                                  | API-Referenz            |
| `docs/SECURITY.md`                                             | RBAC, Regression-Matrix |
| `docs/ADMIN_RUNBOOK.md`                                        | Support-Workflows       |
| `docs/AI_INTEGRATION.md`                                       | AI-Architektur          |
| `docs/FRONTEND.md`                                             | Routen, Tokens, PWA     |
| `docs/ROADMAP.md`, `DEPLOYMENT.md`, `SECURITY_AUDIT_REPORT.md` | Phase 9                 |
| `docs/HANDOVER.md`                                             | Dieses Dokument         |
| `CHANGELOG.md`                                                 | bis **1.0.0-rc1**       |

### 3.4 Tests & CI

- **API pytest:** **97 passed**, 1 skipped (Stand lokal)
- **AI-Gateway pytest:** 10 passed (isoliert)
- **Frontend Vitest:** `QrCode.test.tsx`, `contract.test.ts`
- **CI:** `.github/workflows/ci.yml` — lint, typecheck, migrate, test, build

---

## 4. RBAC-Matrix (Kurz)

| Bereich                         | user | support | admin |
| ------------------------------- | :--: | :-----: | :---: |
| User-Routes (trade, wallet, …)  |  ✅  |    —    |   —   |
| `/admin/*` read                 |  —   |   ✅    |  ✅   |
| Manual credit, withdraw approve |  —   |    —    |  ✅   |
| `/admin/ai/analyze`             |  —   |    —    |  ✅   |

---

## 5. Deployment & lokaler Start

```bash
# Im Monorepo-Root kairox-platform/
cp .env.example .env
docker compose up -d postgres redis
cd apps/api && alembic upgrade head && python -m kairox_api.scripts.seed
cd ../.. && npx pnpm dev
```

Docker full-stack start (`docker compose up -d --build`) runs `alembic upgrade head`
inside the API container before Uvicorn serves traffic. Use
`KAIROX_RUN_MIGRATIONS=false` only when a separate release migration job has
already completed successfully.

**URLs:** Web `http://localhost:3000` · API `http://localhost:8000` · Health `GET /health`

**Test-Accounts (Seed):**

| User     | Passwort       | Rolle |
| -------- | -------------- | ----- |
| kxtest01 | KairoxTest2026 | user  |
| admin    | KairoxTest2026 | admin |

Invite-Code Dev: `KAIROX-DEV`

**Wichtig:** `NEXT_PUBLIC_API_URL=http://localhost:8000` für Browser → API.

---

## 6. Was noch fehlt

### 6.1 Phase 8 — Rest (~5%)

| Item                               | Priorität | Status                                                   |
| ---------------------------------- | --------- | -------------------------------------------------------- |
| Route-Gruppen `(auth)/`, `(main)/` | LOW       | Offen (flache `app/`-Struktur OK)                        |
| **next-intl** vollständig          | LOW       | Lightweight-Hook reicht aktuell                          |
| **Team-Mitgliederliste UI**        | DONE      | API `/team/members` + `/team/unfinished` in `/team/list` |
| **VIP4–VIP6**                      | MED       | Backend nur VIP1–3; kairox.cc zeigt mehr                 |
| **Lighthouse ≥ 90**                | MED       | Noch nicht gemessen/dokumentiert                         |
| **Playwright** Smoke-Tests         | MED       | Nicht eingerichtet                                       |
| **Vitest** UI-Tests erweitern      | LOW       | Button, Countdown, Recharge-Zod                          |
| **Lang-Seite** `/lang`             | LOW       | kairox.cc hat Sprachwahl — noch offen                    |
| **ERC20/BEP20**                    | LOW       | Nur TRC20 aktiv                                          |

### 6.2 Bereits erledigt (früher als „offen“ gelistet)

| Item                                        | Status |
| ------------------------------------------- | ------ |
| QrCode (Recharge + Invite)                  | ✅     |
| Team-Mitgliederliste mit L1-L3/Offen-Filter | ✅     |
| Service Worker (`public/sw.js`)             | ✅     |
| PWA Icons 192 + 512                         | ✅     |
| `docs/FRONTEND.md`                          | ✅     |
| kairox.cc UI-Redesign                       | ✅     |
| 5-Tab Bottom-Nav + SubNav                   | ✅     |
| Admin UI polish                             | ✅     |
| Trial 72h + 7 USDT Bonus                    | ✅     |
| `is_official` bei Recharge ≥ 50 USDT        | ✅     |
| Team-Commission bei Trades                  | ✅     |
| Login-Redirect → `/home`                    | ✅     |
| Docker monorepo + ai-gateway                | ✅     |

### 6.3 Phase 9 — Final-Audit

| Kategorie                                                      | Status                          |
| -------------------------------------------------------------- | ------------------------------- |
| `docs/ROADMAP.md`, `SECURITY_AUDIT_REPORT.md`, `DEPLOYMENT.md` | ✅                              |
| Regression-Matrix `SECURITY.md`                                | ✅                              |
| `kairox_runner-main/` unverändert                              | ⏳ manuell prüfen               |
| Production-Staging Smoke (E2E)                                 | ⏳                              |
| v1.0.0 GA Release                                              | ⏳ nach Lighthouse + Playwright |

### 6.4 Bekannte technische Schulden

1. **Mypy** — vereinzelt Legacy-Warnungen (`tron_client.py`, `cookies.py`)
2. **Windows Dev** — `pnpm` ggf. via `npx pnpm`; `@kairox/shared` Build vor `typecheck`
3. **Privacy Policy** — Platzhalter-Text, vor Production durch Legal ersetzen
4. **PostgreSQL Enums** — `pg_enum()` Helper für lowercase (Windows/Seed-Fix)

---

## 7. Migrations-Reihenfolge

```
001_initial_schema
002_phase2_wallet_ledger_schema
003_phase4_recharge_orders
004_phase5_trade_system
005_phase6_admin
006_phase8_team
007_phase8_team_commission
008_phase8_trial_bonus
009_admin_audit_vip_adjust
010_withdraw_reconciliation
```

```bash
cd apps/api && alembic upgrade head
```

---

## 8. Wichtige ENV-Variablen

| Variable                                   | Zweck                                                  |
| ------------------------------------------ | ------------------------------------------------------ |
| `DATABASE_URL`                             | PostgreSQL async                                       |
| `REDIS_URL`                                | Sessions, Rate-Limits, AI-Limit                        |
| `JWT_SECRET`, `CSRF_SECRET`                | Auth (prod: ändern!)                                   |
| `TRON_DEPOSIT_ADDRESS`, `TRONGRID_API_KEY` | Recharge                                               |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`      | AI (optional)                                          |
| `NEXT_PUBLIC_API_URL`                      | Frontend → API                                         |
| `BLOCK_TRIAL_WITHDRAW`                     | Trial-User Withdraw sperren                            |
| `WEB_URL`, `API_URL`, `CORS_ORIGINS`       | HTTPS Production origins                               |
| `COOKIE_SECURE`, `LOG_JSON`                | Production must be `true`                              |
| `TRON_MIN_CONFIRMATIONS`                   | Mindestbestätigungen für Recharge und Withdraw-Confirm |

---

## 9. Nächste empfohlene Schritte

1. **VIP4–VIP6** sauber fachlich definieren oder UI auf VIP1-VIP3 begrenzen
2. **Playwright Smoke:** register → login → recharge → trade pre-start → admin TX-verify
3. **Lighthouse** messen, Bilder/Fonts optimieren, Ziel ≥ 90 dokumentieren
4. **`/lang`** — i18n-Umschalter wie kairox.cc (optional)
5. Staging: API migration gate or release job + Seed + manueller Full-Flow-Test

---

## 10. Übergabe-Checkliste

- [ ] `.env` mit Tron/Secrets befüllt (nicht committen)
- [ ] Production config validation bestanden (`APP_ENV=production`, HTTPS URLs, CORS, secure cookies, JSON logs)
- [ ] `alembic upgrade head` durch API-Entrypoint oder Release-Job auf Ziel-DB verifiziert
- [ ] Seed ausgeführt (`python -m kairox_api.scripts.seed`)
- [ ] CI grün auf `main`
- [ ] `kairox_runner-main/` diff leer verifiziert
- [ ] Staging-Smoke dokumentiert
- [ ] Privacy/Legal-Text vor Go-Live ersetzen

---

_Zuletzt aktualisiert: Juni 2026 — Phasen 3–9, Post-RC1 UI & PWA._
