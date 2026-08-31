# Kairox Platform v2

Experimental side project / prototype rebuild of [kairox.cc](https://kairox.cc).

> **Status:** This repository is not part of my core portfolio and is not production-validated. The codebase contains a FastAPI/Next.js implementation and automated checks, but I have not personally completed a full end-to-end verification of all functionality. Treat it as an experimental learning/AI-assisted side project, not as evidence of a production-ready system.

## Monorepo Structure

```
kairox-platform/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # Next.js 15 frontend
├── packages/
│   ├── shared/       # Shared TypeScript types & contracts
│   └── ai-gateway/   # AI provider abstraction
├── docs/             # Architecture & API documentation
└── docker-compose.yml
```

## Quick Start

```bash
cp .env.example .env
docker compose up -d
pnpm install
pnpm dev
```

See [docs/getting-started.md](./docs/getting-started.md) for full setup.

## Development workflow encoded in the repository

The repository is structured around a build-review-improve loop:

1. Keep the change scoped to one release slice.
2. Update the relevant docs in the same slice.
3. Run the narrowest useful tests first, then broader checks when risk requires it.
4. Have a second agent or reviewer inspect the result before moving to the next slice.
5. Treat review findings as work to resolve, not as optional notes.

Implemented hardening work includes:

- Admin VIP-adjust audit migration drift fixed with a regression test.
- Protected-route rate limits fail closed when Redis is unavailable.
- API container startup runs `alembic upgrade head` before serving traffic.
- Runtime settings fail fast on unsafe secrets, URLs, CORS, Tron, or logging config.
- Withdrawals separate broadcast (`processing`) from confirmed ledger debit.

Open verification/hardening areas include TronGrid provider resilience, frontend design quality, and end-to-end smoke testing.

## License

Proprietary — Kairox Platform
