# Contributing to Kairox Platform v2

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`

Examples:

- `feat(auth): add refresh token rotation`
- `fix(trade): enforce state machine on server side`
- `docs(api): document recharge webhook flow`

## Development Workflow

1. Copy `.env.example` to `.env`
2. `make docker-up` — start PostgreSQL + Redis
3. `make install` — install dependencies
4. `make migrate && make seed` — prepare database
5. `make dev` — run web + api

## Code Quality Gates

Before opening a PR, ensure:

- [ ] `make lint` passes
- [ ] `make typecheck` passes
- [ ] `make test` passes (≥80% coverage on services/repositories)
- [ ] No file exceeds ~300 lines
- [ ] `docs/` updated for user-facing or architectural changes
- [ ] `.env.example` updated if new env vars added

## Architecture Rules

- Business logic lives in **services**, not routes or React components
- Database access only through **repositories**
- Shared API contracts in `packages/shared`
- No secrets in code — use environment variables

## Pull Requests

- One feature or fix per PR when possible
- Include test plan in PR description
- Link related issues if applicable
