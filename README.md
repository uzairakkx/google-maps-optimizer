# Google Maps Optimizer

Google Maps Optimizer is an architecture-first SaaS foundation for turning local visibility data into evidence-backed actions for home-service businesses.

This repository currently contains **Project Foundation v1 only**. It deliberately does not contain authentication, Google integrations, ranking collection, competitor discovery, AI, billing, product models, or fake data.

## Architecture

```text
Next.js web
    ↓
FastAPI API
    ↓
Application/domain layers (to be added by milestone)
    ↓
SQLAlchemy + PostgreSQL

FastAPI → Celery worker → Redis
```

The MVP uses a modular monolith so domain boundaries remain explicit without the operational cost of microservices. External systems will be added behind provider adapters after their capabilities, terms, quotas, pricing, and data-retention rules are reviewed.

## Prerequisites

- Docker and Docker Compose
- Node.js 22 LTS
- pnpm 10+
- Python 3.12+ for running backend tooling outside Docker

## Local setup

```bash
cp .env.example .env
pnpm install
docker compose up --build
```

The development services are then available at:

- Web: http://localhost:3000
- API docs: http://localhost:8000/docs
- Liveness: http://localhost:8000/health/live
- Readiness: http://localhost:8000/health/ready

The Compose file uses development-only local PostgreSQL and Redis credentials from the example configuration. Do not reuse them in a deployed environment.

## Environment configuration

`.env.example` documents the current foundation variables. The API validates database and Redis URLs at startup. Credentials for future providers must be supplied through the deployment secret manager and must not be committed.

## Backend commands

Run the API locally after installing backend dependencies:

```bash
cd apps/api
python -m uvicorn app.main:app --reload
```

Run checks:

```bash
pnpm api:test
pnpm api:lint
pnpm api:typecheck
```

Run migrations:

```bash
cd apps/api
alembic upgrade head
```

The current Alembic revision is an empty baseline by design. Product tables will be added only after the database proposal is separately reviewed.

## Frontend commands

```bash
pnpm --dir apps/web dev
pnpm --dir apps/web check
pnpm --dir apps/web build
pnpm --dir apps/web test
```

## Celery

The Compose worker is started with:

```bash
celery -A app.worker.celery_app:celery_app worker --loglevel=INFO
```

The only task currently included is a foundation `ping` task for worker plumbing. Product jobs must not be added in this milestone.

## Documentation

- `docs/adr/ADR-001-modular-monolith.md` records the modular monolith decision.
- `Google-Maps-Optimizer-technical-blueprint.md` contains the approved architecture blueprint.

## Scope boundary

The next milestone is the reviewed database design and authentication boundary. Do not add product features automatically.