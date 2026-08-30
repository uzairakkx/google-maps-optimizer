# Google Maps Optimizer

## Production Technical Blueprint

**Status:** Architecture proposal; no application code is included  
**Decision scope:** MVP modular monolith for multi-tenant home-service businesses  
**Core loop:** Measure → Diagnose → Prioritize → Recommend → Act → Measure again

## 1. Executive recommendation

Build a modular monolith with:

- A Next.js web application for the authenticated product experience.
- A FastAPI application as the only public application API.
- PostgreSQL as the system of record.
- Redis as the broker/cache/rate-limit primitive.
- Celery workers for collection, analysis, website fetching, and report jobs.
- Provider adapters behind explicit interfaces; no provider-specific assumptions in the domain layer.
- Deterministic analysis and scoring as the source of truth.
- An AI layer that explains structured evidence and proposes actions, but cannot create facts.

The most important product boundary is this: Google Business Profile management/performance data, Places data, and third-party local-rank data are different data products. They must be represented separately in the schema and UI. The application must never imply that a proprietary “Maps Visibility Score” is an official Google score, or that a correlation is a confirmed ranking factor.

The MVP should prove one narrow promise:

> For one business location, identify a small set of evidence-backed local-visibility opportunities, recommend concrete actions, and preserve a baseline so the user can compare later measurements.

Do not begin with every dashboard, integration, billing flow, or automation. Begin with trustworthy data boundaries and a complete thin slice.

## 2. Exact recommended technology stack

### Runtime and repository

- TypeScript 5.x, strict mode.
- Node.js 22 LTS for the web application and tooling.
- Python 3.12.
- pnpm workspaces for JavaScript packages.
- uv or Poetry for Python dependency locking; use one consistently. Recommendation: `uv`.
- GitHub Actions for CI.
- Docker Compose for local infrastructure.

Pin exact versions in lockfiles during foundation work. “Latest” must not be used in production manifests.

### Frontend

- Next.js App Router, server-rendered where useful.
- React 19-compatible release selected and pinned at implementation time.
- Tailwind CSS.
- shadcn/ui and Radix primitives for accessible UI.
- React Hook Form plus Zod for forms and client validation.
- TanStack Query for server state and cache invalidation.
- Recharts for product charts.
- Mapbox GL JS only for application-owned geographic visualizations. Do not mix Google-attributed content into a Mapbox map without confirming the applicable Google Maps Platform policy.
- Playwright for critical end-to-end flows.
- Vitest and Testing Library for focused frontend tests.
- ESLint and Prettier.

### Backend

- FastAPI.
- Pydantic v2 for API contracts and configuration.
- SQLAlchemy 2.x async ORM.
- `asyncpg` PostgreSQL driver.
- Alembic migrations.
- Celery 5.x with Redis transport/result backend.
- `httpx` for outbound HTTP through provider clients.
- `argon2-cffi` for password hashing if first-party passwords are implemented.
- `PyJWT` is not required if opaque server-side sessions are used; opaque sessions are the recommendation for the MVP.
- Ruff and mypy.
- Pytest, pytest-asyncio, and HTTPX.

### Infrastructure

- PostgreSQL 16 or the managed PostgreSQL version selected for deployment.
- Redis 7.x or managed equivalent.
- Docker Compose locally.
- S3-compatible object storage only when raw exports, reports, or large provider payloads require it.
- OpenTelemetry-compatible tracing and structured JSON logs from the beginning, even if a hosted observability vendor is selected later.

## 3. Monorepo structure

```text
google-maps-optimizer/
├── apps/
│   └── web/
│       ├── app/
│       │   ├── (marketing)/
│       │   ├── (auth)/
│       │   └── (app)/
│       ├── components/
│       │   ├── ui/
│       │   ├── layout/
│       │   ├── charts/
│       │   ├── geo/
│       │   └── opportunities/
│       ├── lib/
│       │   ├── api-client/
│       │   ├── auth/
│       │   ├── query/
│       │   └── validation/
│       ├── public/
│       └── tests/
├── services/
│   └── api/
│       ├── app/
│       │   ├── main.py
│       │   ├── core/
│       │   ├── api/
│       │   │   └── v1/
│       │   ├── auth/
│       │   ├── organizations/
│       │   ├── businesses/
│       │   ├── rankings/
│       │   ├── competitors/
│       │   ├── opportunities/
│       │   ├── recommendations/
│       │   ├── providers/
│       │   ├── jobs/
│       │   ├── db/
│       │   └── common/
│       ├── migrations/
│       └── tests/
│           ├── unit/
│           ├── integration/
│           └── api/
├── packages/
│   ├── contracts/       # generated or manually reviewed API contracts
│   └── config/          # shared non-secret conventions only
├── infra/
│   ├── docker/
│   ├── compose/
│   └── ci/
├── docs/
│   ├── decisions/
│   ├── provider-matrix/
│   ├── data-dictionary/
│   └── runbooks/
├── .env.example
├── compose.yaml
├── package.json
├── pnpm-workspace.yaml
└── README.md
```

Keep the web and API deployable independently, but do not split them into separately deployed microservices. The provider, analysis, and worker modules stay inside the FastAPI service until load or ownership boundaries prove otherwise.

## 4. FastAPI backend structure

The backend should use vertical feature modules with stable internal layers:

```text
services/api/app/
├── main.py
├── core/
│   ├── settings.py
│   ├── logging.py
│   ├── security.py
│   ├── errors.py
│   └── telemetry.py
├── api/v1/
│   ├── router.py
│   ├── dependencies.py
│   └── error_handlers.py
├── auth/
│   ├── models.py
│   ├── schemas.py
│   ├── service.py
│   └── repository.py
├── organizations/
├── businesses/
├── rankings/
├── competitors/
├── opportunities/
├── recommendations/
├── providers/
│   ├── ports.py
│   ├── registry.py
│   ├── google_business_profile/
│   ├── google_places/
│   └── rank_provider/
├── analysis/
│   ├── normalization.py
│   ├── rules.py
│   ├── scoring.py
│   └── evidence.py
├── website/
├── jobs/
│   ├── celery_app.py
│   ├── tasks/
│   └── idempotency.py
├── db/
│   ├── base.py
│   ├── session.py
│   └── models/
└── common/
    ├── enums.py
    ├── pagination.py
    └── clocks.py
```

The API route handler should validate input, resolve the authenticated tenant, call an application service, and serialize a response. It should not contain scoring rules, SQL queries, or provider calls.

The layers are:

1. **API:** HTTP concerns, authentication dependencies, pagination, response schemas.
2. **Application services:** use-case orchestration and transaction boundaries.
3. **Domain/analysis:** normalized facts, rules, evidence, scoring, and invariants.
4. **Repositories:** persistence queries scoped to the organization.
5. **Providers:** outbound API translation and provider-specific error handling.

Version public routes under `/api/v1`. Treat API schemas as contracts and generate or manually maintain the frontend client from the OpenAPI document.

## 5. Next.js frontend structure

Use route groups to keep URL structure independent from layout:

```text
apps/web/app/
├── (marketing)/
│   ├── page.tsx
│   └── pricing/page.tsx
├── (auth)/
│   ├── sign-in/page.tsx
│   ├── sign-up/page.tsx
│   └── verify/page.tsx
└── (app)/
    ├── layout.tsx
    ├── onboarding/
    ├── overview/
    ├── actions/
    ├── competitors/
    ├── rankings/
    └── progress/
```

Use server components for stable layouts and initial reads; use client components only for interactive charts, forms, map controls, and mutations. TanStack Query owns client-side server state. It must not become a second business-logic layer.

Every major screen needs:

- a useful empty state for no measurement yet;
- loading state;
- provider/data freshness state;
- partial-data state;
- error state with a recovery action;
- clear labels distinguishing observed data, derived metrics, and hypotheses.

## 6. PostgreSQL database design

Use UUID primary keys, `timestamptz` in UTC, explicit foreign keys, and append-only measurement tables. All tenant-owned tables should carry `organization_id` directly when practical. This makes authorization queries auditable and prevents accidental cross-tenant joins.

### Identity and tenancy

**users**

- `id`
- `email_normalized` unique
- `password_hash` nullable if another login method is later added
- `display_name`
- `email_verified_at`
- `created_at`, `updated_at`

**organizations**

- `id`
- `name`
- `slug` unique
- `created_at`, `updated_at`

**organization_memberships**

- `organization_id`
- `user_id`
- `role` (`owner`, `admin`, `member`)
- `created_at`
- composite primary key `(organization_id, user_id)`

**sessions**

- `id`
- `user_id`
- `session_token_hash`
- `expires_at`
- `revoked_at`
- `created_at`

### Business configuration

**businesses**

- `id`, `organization_id`
- `name`
- `primary_category`
- `website_url`
- `status`
- `created_at`, `updated_at`

**business_locations**

- `id`, `organization_id`, `business_id`
- `name`
- `address_line_1`, `address_line_2`
- `city`, `region`, `postal_code`, `country_code`
- `latitude`, `longitude`
- `service_area_description`
- `provider_place_id` nullable and provider-qualified
- `created_at`, `updated_at`

**services**

- `id`, `organization_id`, `business_id`
- `name`
- `normalized_name`
- `is_active`

**location_services**

- `location_id`, `service_id`
- composite primary key

**keywords**

- `id`, `organization_id`, `business_id`
- `term`
- `normalized_term`
- `locale`
- `active`
- `created_at`

Add a unique constraint preventing duplicate normalized keywords per business.

### Provider and collection records

**provider_connections**

- `id`, `organization_id`
- `provider_type`
- encrypted provider reference, never a frontend secret
- connection status
- last successful sync
- created/updated timestamps

Tokens belong in a managed secret store or encrypted server-side storage, not in ordinary application rows or logs.

**analysis_runs**

- `id`, `organization_id`, `business_id`
- `run_type`
- `status`
- `requested_at`, `started_at`, `finished_at`
- `failure_code`, `failure_message_safe`
- `idempotency_key`
- `rule_version`
- `scoring_version`

**data_sources**

- `id`, `organization_id`
- provider type
- source purpose
- terms/retention classification
- last observed freshness

### Competitor intelligence

**competitors**

- `id`, `organization_id`, `business_id`, `location_id`
- provider type and provider place/reference ID
- display name
- address summary
- website URL
- discovery source
- active flag

**competitor_snapshots**

- `id`, `organization_id`, `competitor_id`
- `analysis_run_id`
- observed rating nullable
- observed review count nullable
- observed photo count nullable where legitimately available
- observed categories/services JSONB
- observed website URL
- `collected_at`
- `freshness_expires_at`
- raw payload reference, if retention is allowed

Do not use zero to mean “not available.” Use nullable fields plus a data-quality status.

### Geo-rank tracking

**ranking_grids**

- `id`, `organization_id`, `location_id`
- name
- center latitude/longitude
- grid dimensions
- radius or point spacing
- active
- created/updated timestamps

**ranking_points**

- `id`, `organization_id`, `grid_id`
- latitude/longitude
- row/column coordinates
- label
- unique `(grid_id, row_index, column_index)`

**ranking_measurements**

- `id`, `organization_id`, `analysis_run_id`
- `ranking_point_id`, `keyword_id`
- provider type
- measured timestamp
- observed position nullable
- position status (`found`, `not_found`, `unavailable`, `not_measured`)
- target place reference nullable
- competitor positions JSONB only if the provider legally returns them
- raw response reference
- freshness and confidence fields

Never update a prior measurement. A new collection creates new rows.

### Reviews, evidence, and recommendations

**review_snapshots**

- `id`, `organization_id`, `location_id`
- provider type
- measured timestamp
- review count nullable
- rating nullable
- review activity window nullable
- data quality status

**evidence_items**

- `id`, `organization_id`, `analysis_run_id`
- evidence type
- subject type and subject ID
- observed/derived/hypothesis classification
- structured payload
- source reference
- collected timestamp
- confidence

**opportunities**

- `id`, `organization_id`, `business_id`, `location_id`
- `analysis_run_id`
- opportunity type
- title
- description
- impact, confidence, relevance, gap, effort, data_quality
- priority score
- scoring version
- status
- evidence summary
- recommended action
- created/updated timestamps

**recommendation_actions**

- `id`, `organization_id`, `opportunity_id`
- action text
- owner
- status
- due date nullable
- started/completed timestamps
- completion note

**ai_explanations**

- `id`, `organization_id`, `opportunity_id`
- model/provider identifier
- prompt/template version
- validated structured output
- cited evidence item IDs
- safety/validation status
- created timestamp

### Audit and job operations

**jobs**

- `id`, `organization_id` nullable for system jobs
- job type
- idempotency key
- status
- attempt count
- scheduled/started/finished timestamps
- safe error code

**audit_events**

- `id`, `organization_id`, `actor_user_id` nullable
- action
- resource type and ID
- metadata with sensitive values removed
- request ID
- created timestamp

Recommended indexes include `(organization_id, created_at)`, `(organization_id, business_id)`, `(organization_id, location_id, measured_at)`, and active/status indexes used by dashboard queries. Add indexes based on query plans rather than indexing every column.

### Historical strategy

Current configuration tables hold the current state. Snapshot and measurement tables hold history. A profile change is not a substitute for a snapshot. Analysis runs tie facts, derived metrics, opportunities, and AI explanations to the exact input state and rule/scoring versions used.

## 7. Entity relationships

```text
User ──< OrganizationMembership >── Organization
Organization ──< Business ──< BusinessLocation
Business ──< Service
BusinessLocation >──< Service
Business ──< Keyword
BusinessLocation ──< RankingGrid ──< RankingPoint
Keyword ──< RankingMeasurement >── RankingPoint
BusinessLocation ──< ReviewSnapshot
BusinessLocation ──< Competitor
Competitor ──< CompetitorSnapshot
AnalysisRun ──< EvidenceItem
AnalysisRun ──< RankingMeasurement
AnalysisRun ──< Opportunity ──< RecommendationAction
Opportunity ──< AIExplanation
Organization ──< AuditEvent
```

The authorization root is always the organization. A request must resolve membership before accessing a business, location, ranking, competitor, or opportunity. IDs supplied by a client are never authorization evidence.

## 8. Authentication architecture

For the MVP, use first-party email/password authentication with:

- Argon2id password hashing.
- Server-side opaque sessions stored as a hash in PostgreSQL or Redis-backed session storage.
- Secure, HttpOnly, SameSite cookies.
- Secure flag in production.
- Session rotation after sign-in and privilege changes.
- Short inactivity timeout plus longer absolute expiry.
- Email verification before external provider connection.
- Password reset tokens that are single-use, short-lived, hashed at rest, and never logged.
- Generic responses for account-existence-sensitive flows.

If social login or enterprise SSO becomes a near-term requirement, replace the login mechanism behind an auth port rather than spreading provider assumptions through the domain. Authentication and organization authorization are separate concerns.

Use CSRF protection for cookie-authenticated state-changing routes. Apply rate limits to sign-in, password reset, onboarding, and analysis-start endpoints.

## 9. Multi-tenant architecture

Enforce tenant isolation in three places:

1. **API dependency:** resolve the session, user, organization, and membership role.
2. **Application service:** pass a typed tenant context into every use case.
3. **Repository query:** include organization scope in every tenant-sensitive query and write.

Use composite foreign keys or explicit ownership checks to prevent linking a location from one organization to a keyword, grid, competitor, or opportunity from another. Add automated negative authorization tests for every resource family.

PostgreSQL Row-Level Security can be added as defense in depth once the connection/session model supports safely setting a transaction-local organization ID. It must not be the only control, and it must not be enabled casually without tests for background workers and migrations.

## 10. External provider architecture

Define ports around product capabilities, not vendor endpoints:

```text
BusinessProfileProvider
  - list_owned_locations()
  - get_location_profile()
  - list_reviews()
  - get_performance_metrics()

PlaceDiscoveryProvider
  - resolve_place()
  - search_places()
  - get_allowed_place_details()

RankProvider
  - discover_competitors()
  - collect_local_rankings()
  - get_rank_capabilities()

WebsiteAnalysisProvider
  - fetch_public_page()
  - analyze_document()
```

Every adapter must return normalized records containing provider, provider reference, collection time, freshness, confidence, and capability metadata. Provider errors map to internal error categories such as authentication, quota, invalid request, unavailable, and policy/permission restriction.

Provider selection is a gate before ranking implementation. Record, for each candidate provider:

- exact endpoints and returned fields;
- account and authorization requirements;
- quotas and rate limits;
- per-request and subscription costs;
- storage/display rights;
- freshness guarantees;
- geographic coverage;
- ranking definition and accuracy limitations;
- deletion/retention requirements;
- terms of service and acceptable-use review;
- fallback behavior.

No provider client should be called directly from a route or analysis rule.

## 11. Google-related limitations

The official Google Business Profile APIs are appropriate for authorized management and performance workflows around a business’s own profiles. Google documents separate APIs for account management, business information, reviews, posts, notifications, verifications, and performance insights. They are not a general-purpose API for competitor local-pack rankings.

Google Places API can support place discovery and allowed place details, subject to field selection, billing, attribution, storage, and caching rules. A place ID has special storage treatment, but other Google content may have restrictions. Billing is pay-as-you-go and depends on requested SKUs; the implementation must use current official pricing rather than hard-coding an old estimate.

The product must not claim that official Google APIs provide:

- arbitrary competitor rankings on a geographic grid;
- a universal “Google Maps rank” for every query and point;
- all competitor review activity or historical profile changes;
- unrestricted storage of all returned Google content;
- guaranteed or causal ranking explanations.

Do not scrape Google Search or Maps, automate consumer interfaces, bypass rate limits, or build around undocumented endpoints. For local-rank measurements, use a licensed provider whose contract explicitly permits the intended collection, storage, display, and customer use. If no provider meets those requirements, ship the rest of the product with ranking data marked unavailable rather than fabricate it.

The UI should show a provider/source label and freshness timestamp wherever data may be mistaken for official Google data. The internal score should be named exactly something like **Google Maps Optimizer calculated score**, never “Google score.”

Reference documents to verify again at implementation time:

- Google Business Profile API overview: https://developers.google.com/my-business/ref_overview
- Google Business Profile API limits: https://developers.google.com/my-business/content/limits
- Places API usage and billing: https://developers.google.com/maps/documentation/places/web-service/usage-and-billing
- Places API policies: https://developers.google.com/maps/documentation/places/web-service/policies

## 12. Geo-ranking architecture

A ranking configuration consists of:

- business location;
- one or more keywords;
- grid center;
- grid points;
- geographic coordinate system;
- provider;
- schedule;
- maximum result depth;
- measurement timezone.

A collection job creates an analysis run, captures a request manifest, measures each point, and writes immutable ranking measurements. A rank not found is represented as a status, not as a fabricated large position. Provider responses are retained only when contractually permitted; otherwise retain normalized facts and a provider reference.

Derived metrics should include:

- coverage: percentage of measured points where the target was found;
- mean/median position among found points;
- position distribution;
- visibility index with a documented transformation;
- period-over-period delta;
- data quality and coverage.

Do not collapse the grid into a single number in the primary experience. Show the map, point-level results, distribution, and trend first. A summary score is secondary and explicitly proprietary.

Use Mapbox only for the application’s own grid and derived visualization unless the legal/policy review supports another arrangement. Keep map rendering and provider data attribution in the frontend boundary.

## 13. Competitor intelligence architecture

Competitors should be discovered by a permitted rank/place provider or selected by the user. Store the discovery method and confidence. A competitor snapshot is a point-in-time observation, not current truth forever.

Display three layers:

- **Observed data:** “This snapshot returned 4.7 rating and 312 reviews.”
- **Derived metric:** “The observed review count changed by 22 between snapshots.”
- **Hypothesis:** “Higher review activity may correlate with stronger local visibility in this dataset.”

Hypotheses require cautious language, a source window, and enough data. They must never be rendered as confirmed Google ranking factors. Competitor comparisons should be scoped to the selected location, keyword set, and measurement window.

## 14. Opportunity engine

The engine is deterministic and versioned:

```text
Provider facts
  → normalized facts
  → evidence items
  → analysis rules
  → competitive gaps
  → opportunities
  → explainable score
  → AI explanation
  → recommendation action
```

Initial rule families:

- service coverage gap;
- review-count or review-activity gap, only where observations are reliable;
- website/service-page coverage gap;
- ranking gap;
- geographic visibility gap;
- profile-data completeness observation;
- content opportunity.

Each rule must declare required evidence, missing-data behavior, output type, and confidence calculation. If required evidence is absent, produce “insufficient evidence” rather than an opportunity with guessed values.

### Scoring model v1

Use 0–100 dimensions:

- `impact`: plausible business importance;
- `relevance`: match to the business’s configured services/location;
- `gap`: size of observed competitive or geographic difference;
- `confidence`: reliability and consistency of the evidence;
- `data_quality`: completeness/freshness/provider quality;
- `effort`: estimated implementation effort, where 100 is hardest.

Versioned score:

```text
base =
  0.30 * impact +
  0.20 * relevance +
  0.20 * gap +
  0.15 * confidence +
  0.15 * data_quality

effort_factor = 0.60 + 0.40 * (1 - effort / 100)

priority_score = round(base * effort_factor)
```

The weights are an explicit v1 product decision, not a claim about Google’s algorithm. Store the scoring version and each component so the UI can answer “Why is this #1?” Calibrate the weights using completed-action and user-feedback data later; do not silently change historical scores.

## 15. AI architecture

AI receives a bounded evidence pack generated by the application:

- business/location configuration;
- normalized observations;
- derived metrics;
- opportunity score and components;
- evidence IDs and freshness;
- applicable product language rules.

The model may:

- explain a gap in plain language;
- summarize evidence;
- draft a specific, truthful action;
- explain a trend;
- identify insufficient evidence.

The model may not:

- create rankings, reviews, competitors, or business facts;
- substitute a guessed value for null;
- cite evidence IDs not present in the input;
- claim guaranteed improvement or causation;
- call external providers directly.

Use structured JSON output validated by Pydantic. Validate that every factual claim maps to an evidence item and reject or regenerate invalid output. Store the prompt/template version, model identifier, evidence IDs, validation result, and generated text. Avoid sending unnecessary personal data or provider payloads to an AI provider.

Use provider abstraction for the model. Add a fallback explanation template so the product remains useful when AI is unavailable.

## 16. Celery and Redis architecture

Use Celery for:

- provider synchronization;
- ranking collection;
- competitor discovery;
- website analysis;
- deterministic analysis;
- AI explanation;
- scheduled monitoring;
- report generation.

API requests should create an `analysis_run` and enqueue work, then return a status resource. They should not block on provider or AI calls.

Every task needs:

- an idempotency key;
- bounded retries with exponential backoff;
- provider-aware rate limiting;
- a terminal failure state;
- safe error details for users and detailed structured logs for operators;
- correlation ID and analysis-run ID;
- timeout;
- cancellation behavior where practical.

Use a chain or explicit state machine for dependent steps:

```text
collect → normalize → analyze → score → explain → publish
```

Use unique database constraints and upsert-like logic to make retries safe. Do not treat a Celery retry as proof that the earlier external write did not happen.

## 17. Website analysis

Make website analysis a later MVP slice or optional first release capability. It is useful, but it expands security and legal surface area.

The fetcher must:

- accept only `http` and `https`;
- reject localhost, loopback, link-local, private, reserved, and metadata IP ranges;
- resolve DNS and re-check every redirect;
- cap redirects, response size, total time, and page count;
- allow only expected content types;
- avoid executing arbitrary page JavaScript;
- use a clear user-agent;
- respect applicable restrictions and a documented crawl policy;
- prevent cross-tenant cache leakage.

Analyze deterministic observations such as title, headings, contact information, location references, service terms, internal links, and accessible service pages. Store page URL, fetched timestamp, HTTP status, content hash, and parser version. Keep website observations separate from Google ranking conclusions.

## 18. Historical and time-series design

Every measurement has:

- the time requested;
- the time collected;
- provider;
- provider reference;
- freshness;
- confidence;
- analysis-run link;
- rule/scoring version where derived.

Snapshots are append-only. Current configuration may be updated, but prior measurement rows remain. For “what changed?” queries, compare adjacent snapshots in the same scope and clearly identify gaps in collection. For “what happened after an action?”, show temporal association and use wording such as “visibility improved after this action was completed,” not causal proof.

Partitioning is not needed initially. Revisit it when ranking measurements and raw observation tables become large enough to affect query plans or vacuum behavior.

## 19. Security architecture

Required controls:

- backend tenant authorization on every protected resource;
- Pydantic validation and strict allowlists;
- parameterized SQL through SQLAlchemy;
- escaped/render-safe user content;
- CSP and security headers;
- CSRF defenses for cookie-authenticated mutations;
- secure cookies and session rotation;
- request and provider rate limiting;
- secret management outside source control;
- redaction of tokens, cookies, addresses where sensitive, and raw provider responses from logs;
- webhook signature verification if webhooks are introduced;
- audit events for authentication, provider connection changes, analysis runs, recommendation completion, and destructive actions;
- safe, stable public errors with internal correlation IDs.

Use SSRF protection for website analysis. Apply least privilege to database, Redis, object storage, and provider credentials. Add dependency and container image scanning in CI.

## 20. Testing strategy

### Backend

- Unit tests for normalizers, evidence classification, rule behavior, scoring, null/missing-data handling, and provider error mapping.
- Repository tests against PostgreSQL for constraints, tenant scoping, historical immutability, and indexes used by important queries.
- API tests with HTTPX for authentication, authorization, validation, pagination, and predictable errors.
- Provider contract tests using recorded sanitized fixtures or provider-approved sandbox responses.
- Worker tests for idempotency, retries, state transitions, and failure recovery.

### Frontend

- Component tests for empty/loading/error/partial-data states.
- Form tests for onboarding and validation.
- Interaction tests for completing an action and filtering rankings.
- Playwright coverage for:
  - sign up/sign in;
  - create organization;
  - create business and location;
  - configure service and keyword;
  - start analysis;
  - see provider/data freshness state;
  - inspect opportunity evidence;
  - complete recommendation;
  - view a later historical comparison.

### Security and quality gates

- Ruff, mypy, ESLint, Prettier check, TypeScript check.
- Migration upgrade test from an empty database.
- Cross-tenant negative tests for every organization-owned resource.
- Secret scanning.
- Dependency audit.
- Docker Compose smoke test.

## 21. Docker development architecture

Initial Compose services:

- `web`
- `api`
- `worker`
- `postgres`
- `redis`

Keep the first Compose file simple. Add a beat/scheduler process only when scheduled monitoring is implemented. Use health checks and dependency readiness rather than arbitrary sleep commands.

The API container runs migrations explicitly as a development command, not implicitly on every production startup. Production deployment should use a separate migration job with reviewed migration files.

## 22. Environment configuration

Create `.env.example` with only variables actually used:

```text
APP_ENV=development
APP_URL=http://localhost:3000
API_URL=http://localhost:8000
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
SESSION_COOKIE_NAME=gmo_session
SESSION_TTL_SECONDS=...
CSRF_SECRET=...
LOG_LEVEL=INFO
```

Later additions should be provider-specific and documented:

```text
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
MAPBOX_PUBLIC_TOKEN=...
RANK_PROVIDER_API_KEY=...
AI_PROVIDER_API_KEY=...
OBJECT_STORAGE_ENDPOINT=...
```

Never commit `.env`, tokens, provider keys, database credentials, or private certificates. Validate configuration at startup and fail clearly if a feature is enabled without its required configuration.

## 23. MVP boundaries

### In scope

- Account creation and session authentication.
- One organization per initial onboarding flow, with the schema ready for more.
- Business and location setup.
- Services and target keywords.
- Provider abstraction and one approved data source.
- Basic competitor discovery where legally and technically supported.
- Basic geo-rank grid collection through a selected licensed provider, or an explicit unavailable state if provider selection is not complete.
- Deterministic opportunity rules.
- Explainable scoring.
- AI explanation with structured validation.
- Action status and completion.
- Baseline and historical comparison.
- Focused action-oriented dashboard.

### Explicitly deferred

- Advanced billing and metering.
- White labeling.
- Enterprise permission granularity.
- Autonomous agents.
- Large integration catalog.
- Bulk profile editing.
- Complex workflow automation.
- Full website crawler.
- Predictive ranking claims.
- Unreviewed provider scraping.

## 24. Development phases

1. **Requirements and decisions:** clarify target customer, initial geography, provider requirements, retention, and success metrics.
2. **Architecture and provider gate:** approve this blueprint; complete provider capability/cost/terms matrix.
3. **Database design:** finalize ERD, constraints, indexes, migration strategy, and data dictionary.
4. **Foundation:** monorepo, Compose, config, logging, health checks, Alembic, CI.
5. **Authentication:** sessions, verification/reset boundaries, organization membership.
6. **Onboarding:** organization, business, location, services, keywords.
7. **Provider ports:** interfaces, normalized models, provider error taxonomy, fixture tests.
8. **First collection:** one real provider capability with freshness and failure states.
9. **Competitor intelligence:** permitted discovery, snapshots, observed/derived/hypothesis UI.
10. **Geo-rank tracking:** grid configuration, immutable measurements, map and history.
11. **Opportunity engine:** evidence, deterministic rules, versioned score, tests.
12. **AI recommendations:** bounded context, schema output, validation, fallback copy.
13. **Action dashboard:** priorities, evidence, action status, empty/partial/error states.
14. **Historical progress:** before/after views and association language.
15. **Hardening:** security review, tenant tests, rate limits, SSRF tests, load tests.
16. **Deployment and monitoring:** managed services, migration job, backups, alerts, runbooks.

Each phase ends with a demonstrable acceptance criterion, not merely a merged branch.

## 25. Technical risks

- **Provider capability mismatch:** official Google APIs may not support the desired rank data. Mitigation: provider gate before ranking code; capability matrix and unavailable states.
- **Terms and retention restrictions:** some data cannot be stored or displayed as originally imagined. Mitigation: data classification, provider-specific retention policies, separate raw/normalized storage.
- **Ranking reproducibility:** local results vary by time, device, language, and provider methodology. Mitigation: preserve measurement context and communicate limitations.
- **Over-scoring:** a proprietary score can look authoritative. Mitigation: show components, version, source, and label it as calculated.
- **AI hallucination:** explanations can overstate evidence. Mitigation: structured output, evidence IDs, validation, deterministic fallback.
- **Tenant leakage:** one unscoped repository query can expose data. Mitigation: tenant context, composite ownership constraints, negative tests, optional RLS.
- **Website SSRF:** user-supplied URLs can reach internal services. Mitigation: strict URL/IP/redirect controls and isolated worker.
- **Job duplication:** retries can duplicate collection or analysis. Mitigation: idempotency keys and database uniqueness.
- **Cost spikes:** grid collection and AI explanations scale with locations, keywords, and points. Mitigation: quotas, previews, batching, schedules, usage metering.
- **Schema drift:** providers change fields and semantics. Mitigation: adapters, normalized contracts, capability versions, fixture/contract tests.

## 26. Data-provider risks

Do not select a ranking provider on brand recognition alone. Score candidates against:

| Criterion | Required decision |
|---|---|
| Geographic coverage | Initial markets and service-area behavior |
| Measurement definition | What “rank” means and what is actually returned |
| Grid support | Point count, radius, schedule, depth |
| Competitor output | Whether competitor identity/rank is returned lawfully |
| API reliability | Quotas, latency, retries, status behavior |
| Commercial model | Per lookup, per grid point, subscription, minimums |
| Storage rights | Raw response retention and customer display |
| Compliance | Terms, privacy, deletion, attribution |
| Freshness | Collection timing and stale-data semantics |
| Accuracy | Known limitations and support process |

The chosen provider should be documented in `docs/provider-matrix/` before implementation. Until then, provider interfaces and fixtures are the maximum safe implementation.

## 27. Cost considerations

Primary cost drivers:

- rank-provider calls multiplied by locations × keywords × grid points × schedule;
- Places or profile API request fields and SKU tiers;
- AI tokens for explanations;
- PostgreSQL storage and query volume;
- Redis and worker concurrency;
- website fetch bandwidth and parser workload;
- observability retention.

Control costs with:

- analysis previews showing estimated provider usage;
- per-organization quotas;
- configurable schedules;
- deduplicated collection requests;
- result caching only where the provider permits it;
- smaller default grids;
- generating AI explanations only for the top opportunities;
- storing normalized facts rather than prohibited/raw payloads;
- monitoring cost per completed analysis.

Do not promise a fixed customer price until real provider quotes, billing SKUs, and expected usage are known.

## 28. Scalability considerations

The modular monolith is sufficient for the MVP. Scale in this order:

1. Add worker concurrency and provider-specific queues.
2. Add database indexes based on query plans.
3. Separate read-heavy dashboard queries or materialized summaries.
4. Partition append-only measurements when volume justifies it.
5. Move raw payloads/reports to object storage.
6. Add a dedicated analytics store only when PostgreSQL is demonstrably insufficient.
7. Split a provider or worker into a service only when independent scaling, reliability, or ownership makes the boundary worthwhile.

Use cursor pagination for measurements and opportunities. Avoid fetching full history into the browser. Precompute dashboard summaries for common windows while retaining raw immutable measurements.

## Exact first implementation task

**After architecture approval, implement “Project Foundation v1” and nothing else.**

Acceptance criteria:

1. Monorepo with `apps/web` and `services/api`.
2. Next.js app boots with a minimal shell and no product data.
3. FastAPI app boots with `/health/live` and `/health/ready`.
4. Docker Compose starts PostgreSQL, Redis, API, worker, and web.
5. Pydantic settings load from environment and fail on invalid required configuration.
6. SQLAlchemy session wiring and Alembic baseline exist, with no speculative product tables.
7. Structured request IDs and JSON logs exist in the API and worker.
8. A minimal CI workflow runs formatting, lint, type checks, and the foundation smoke test.
9. `.env.example` exists and no secrets are committed.
10. A short ADR records the modular-monolith decision, session-auth decision, tenant-scoping rule, and provider-adapter rule.

Do **not** implement Google OAuth, ranking collection, fake seed metrics, competitor discovery, AI calls, or dashboard charts in this task. The next milestone after foundation is the reviewed database design and authentication boundary, followed by onboarding.

## Final architectural decision

The product’s defensibility should come from trustworthy measurement context, explicit evidence, explainable opportunity prioritization, and a useful action loop—not from pretending to have privileged access to Google’s ranking algorithm. Build the data contracts and tenant boundaries first; choose the ranking provider before promising ranking functionality; then let the product grow one validated milestone at a time.