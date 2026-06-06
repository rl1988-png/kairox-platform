# Kairox Platform v2 - Frontend

## Stack

- Next.js 15 App Router - React 19 - Tailwind CSS
- Shared types: `packages/shared`
- API client: `apps/web/src/lib/api/` (cookies + CSRF)

## Design tokens (Tailwind)

| Token             | Usage                                |
| ----------------- | ------------------------------------ |
| `bg-bg-primary`   | Page background (`#0b1220`)          |
| `bg-kairox-pink`  | Primary actions, accents (`#fc81b9`) |
| `text-text-muted` | Secondary copy                       |
| `border-border`   | Card borders                         |

Do not hardcode hex colors in components.

## Routes

| Path                                      | Purpose                                              |
| ----------------------------------------- | ---------------------------------------------------- |
| `/login`, `/register`, `/reset-password`  | Auth                                                 |
| `/home`                                   | Landing after login                                  |
| `/trade`                                  | VIP trade flow                                       |
| `/wallet`, `/wallet/bill`, `/wallet/bind` | Balance & ledger                                     |
| `/recharge`                               | TRC20 deposit + QR                                   |
| `/withdraw`                               | Withdraw request                                     |
| `/team`, `/team/list`                     | Referral stats, L1-L3 member list, unfinished filter |
| `/account`, `/account/invite`             | Profile + invite QR                                  |
| `/admin/*`                                | Staff console                                        |

## Key components

| Component               | Path                             |
| ----------------------- | -------------------------------- |
| `AppShell`              | `components/layout/AppShell.tsx` |
| `BottomNav`             | Mobile navigation                |
| `QrCode`                | Local SVG QR (`react-qr-code`)   |
| `ServiceWorkerRegister` | PWA shell (production only)      |

## PWA

- Manifest: `public/manifest.json`
- Service worker: `public/sw.js` - caches app shell only, never API
- Registered in root `layout.tsx`

## i18n

Lightweight hook: `lib/i18n/index.tsx` + `messages/de.json`, `en.json`

## Testing

```bash
pnpm --filter @kairox/web test
pnpm --filter @kairox/web typecheck
pnpm --filter @kairox/web lint
```
