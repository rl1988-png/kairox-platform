# Kairox Platform v2

Professional crypto trading and wallet platform — rebuild of [kairox.cc](https://kairox.cc).

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

## High-End Delivery Standard

Every production-facing change follows a build-review-improve loop:

1. Keep the change scoped to one release slice.
2. Update the relevant docs in the same slice.
3. Run the narrowest useful tests first, then broader checks when risk requires it.
4. Have a second agent or reviewer inspect the result before moving to the next slice.
5. Treat review findings as work to resolve, not as optional notes.

Completed hardening slices:

- Admin VIP-adjust audit migration drift fixed with a regression test.
- Protected-route rate limits now fail closed when Redis is unavailable.
- API container startup now runs `alembic upgrade head` before serving traffic.
- Production runtime settings fail fast on unsafe secrets, URLs, CORS, Tron, or logging config.
- Withdrawals now separate broadcast (`processing`) from confirmed ledger debit.

Current hardening focus: TronGrid provider resilience, frontend design quality, and
end-to-end smoke tests.

## License

Proprietary — Kairox Platform
