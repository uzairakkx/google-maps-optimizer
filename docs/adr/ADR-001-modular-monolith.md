# ADR-001: Use a modular monolith for the MVP

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

Google Maps Optimizer will eventually combine a web application, API, durable historical measurements, asynchronous provider work, deterministic analysis, and an AI explanation layer. The product is still establishing its domain model and provider boundaries. Splitting these concerns into independently deployed services now would create network, deployment, observability, and data-consistency overhead before there is evidence that separate scaling or ownership is needed.

## Decision

Use a modular monolith for the MVP:

- Next.js is the web application and user-facing shell.
- FastAPI is the public application API and owns application orchestration.
- PostgreSQL is the system of record and migration authority.
- Redis is the broker/cache primitive.
- Celery runs asynchronous and scheduled work.
- Provider adapters are internal modules with explicit capability interfaces.

Feature modules may have their own schemas, repositories, services, and tests, but they remain in one API/worker deployment until a demonstrated operational or scaling need justifies extraction.

## Consequences

### Positive

- One deployable backend keeps local development and early operations simple.
- Transactions and historical-data invariants are easier to reason about.
- Domain boundaries can be tested before they become network boundaries.
- The architecture remains ready for later extraction because provider and feature ports are explicit.

### Negative

- A defect or resource spike in one module can affect the shared process.
- Independent scaling is initially coarser.
- The repository needs discipline to prevent route handlers and modules from becoming coupled.

These costs are acceptable for the MVP. Worker queues provide an initial isolation boundary for expensive provider and analysis operations.