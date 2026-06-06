# Netlify — Kairox Web

Production site: **https://shimmering-bienenstitch-a213d0.netlify.app**

Netlify hosts **only the Next.js frontend**. The FastAPI backend, PostgreSQL, and Redis must run elsewhere (Railway, Render, Fly.io, VPS + Docker).

## Netlify UI settings

| Setting | Value |
|---------|--------|
| Base directory | `kairox-platform` (if repo root is parent) or `.` (if repo is `kairox-platform`) |
| Build command | *(from `netlify.toml`)* |
| Node version | 20 |

## Required environment variables (Netlify → Site settings → Environment)

| Variable | Example | Notes |
|----------|---------|--------|
| `NEXT_PUBLIC_API_URL` | `https://shimmering-bienenstitch-a213d0.netlify.app` | Same origin → cookies work via proxy |
| `API_PROXY_URL` | `https://your-api.onrender.com` | **Server-only** — Next rewrites `/api/*` to backend |

Without `API_PROXY_URL`, the UI loads but **login/API calls fail**.

## Backend (API host) — required env

```env
APP_ENV=production
WEB_URL=https://shimmering-bienenstitch-a213d0.netlify.app
API_URL=https://your-api.onrender.com
CORS_ORIGINS=https://shimmering-bienenstitch-a213d0.netlify.app
COOKIE_SECURE=true
LOG_JSON=true
JWT_SECRET=<32+ random chars>
CSRF_SECRET=<32+ random chars>
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
TRON_DEPOSIT_ADDRESS=T...
TRONGRID_API_KEY=...
```

Run once on the API database:

```bash
alembic upgrade head
python -m kairox_api.scripts.seed
```

## Redeploy

After changing env vars: **Deploys → Trigger deploy → Clear cache and deploy**.

## Smoke test

1. `https://shimmering-bienenstitch-a213d0.netlify.app/login` → 200
2. Login with seeded user (after API + seed)
3. `/home` loads with balance
