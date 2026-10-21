# Contracts with the SDI platform

State analyzed on 2026-10-14. Local sources to reread before generating an application: [compose](../../../td/core-platform/podman-compose.yml), [README](../../../td/core-platform/README.md), [app template](../../../td/core-platform/templates/podman-compose.yml), [bootstrap](../../../td/core-platform/templates/bootstrap.sh), [app pipeline](../../../td/core-platform/templates/gitlab-ci.yml). Relative links assume this skill is in the repository's `skills/archi` directory; if copied elsewhere, locate the equivalents in the target platform.

## 1. The 11 services and their consumers

| JSON contract ID | Function / when to choose it | Backend address | Host access | Per-app resource / cost to consider |
|---|---|---|---|---|
| `postgres` | Durable relational state, queries, transactions; pgvector for RAG | `postgres.internal:5432` | 5432 | DB + user; connections, indexes, I/O and volume |
| `valkey` | Justified caching, pub/sub, Streams for independent jobs | `valkey.internal:6379`; alias `redis.internal` | 6379 | `<app>:` prefix; memory, TTL, Streams retention and AOF |
| `s3` | Documents, media, large files | `host.containers.internal:9000` | 9000 API; 9001 file browser | Bucket + scoped key; storage, transfer, listing and cleanup |
| `openbao` | Backend secrets and provisioned configuration | `openbao.internal:8200`; alias `vault.internal` | 8200 | `secret/<app>/`; read at startup; in-memory secrets in this dev mode |
| `casdoor` | Centralized OIDC authentication | `idp.internal:8000` / `casdoor.internal:8000` | 9300 | OIDC client per app; data in Postgres |
| `apisix` | LLM and embedding calls through the gateway | `llm.internal:9080/v1` | 9080 | Virtual key/app, `task:*` aliases, budgets and limits below |
| `temporal` | Workflows with steps/waits/resumption | `temporal.internal:7233` gRPC | 7233 | Namespace/app; application workers; Postgres for state |
| `temporal-ui` | Operator console for workflows | `temporal-ui.internal:8080` | 9233 | Depends on Temporal; not an end-user business interface |
| `umami` | Navigation/event measurement useful to the product | `analytics.internal:3000` | 9400 dashboard | Site/app; Postgres persistence; no Valkey configured |
| `registry` | Publishing and pulling OCI images | `registry.internal:5000` | `localhost:5000/<app>/<service>:<tag>` | Image storage, tag policy and cleanup |
| `dozzle` | Operator access to container logs | `dozzle.internal:8080` | 9999 | Podman socket; neither a metrics engine nor tracing |

Host addresses refer to the local workshop, not production URLs. A phone cannot reach the workstation through its own `localhost`. Publishing on another host requires appropriate DNS/public URLs, ports, TLS and OIDC settings.

## 2. Network and identity boundaries

- App containers: shared external network `core-network`. `.internal` resolution is reserved for backend components in this context.
- Browser: the app's public UI and API; public Casdoor for sign-in. SPA JavaScript does not run in the nginx container.
- S3: although the service is connected to the network in compose, the **access contract** models it as external. Do not invent `s3.internal`.
- Umami: browser → app paths `/api/v1/_a/t.js` and `/api/v1/_a/send` → API → `analytics.internal:3000`. The application proxy still needs to be implemented; the scripts do not generate it. Preserve the required headers, including the client IP according to the trusted proxy setup; do not trust an arbitrary `X-Forwarded-For` supplied from the internet.
- OIDC: internal/public issuer, callback, state/nonce, token validation and session handling are integration responsibilities. Casdoor authenticates; the app authorizes operations and object access.

**PLAT-001 — MUST, declarative check:** no direct frontend/native-client access to OpenBao, Postgres, Valkey, private APISIX, Temporal or Umami. Why: protect secrets and boundaries; the browser cannot resolve this network. Compute: prevent bypassing backend limits; security takes priority. The script checks declared services, not actual calls or bundles: a code audit is required.

The compatibility aliases `redis.internal` and `vault.internal` are not reliable container names for `podman exec`. Use the repository's shims rather than copying historical commands.

## 3. Ports, processes and health checks

One block of ten ports/app in `8000–8999`, with a base that is a multiple of ten: frontend `+0`, API `+1`, worker health `+8`. Unreserved example: base 8500 → 8500/8501/8508. **Check other apps and the workstation before allocating ports.** The validator does not scan occupied ports.

**PLAT-002 — MUST:** do not allocate the `8200–8209` block: OpenBao already publishes 8200, despite the README statement placing the platform outside the application range. Why: guaranteed collision. Compute: avoid restart loops and an unusable deployment.

Multiple APIs/workers with exposed ports require explicit allocation of free offsets and a contract extension; do not copy the same offset everywhere. The v1 schema describes only the canonical offsets.

**OPS-001 — MUST for API/worker/upstream servers:** `/health` for process liveness, `/ready` for actual readiness; on SIGTERM, stop accepting work, complete/abandon it cleanly and exit in less than 10 seconds under the workshop contract. Why: deterministic deployment and resumability. Compute: avoid stuck processes and work being retried incorrectly. Long jobs must support checkpoints/resumption; completing them in full before shutdown is not always possible. A CLI that terminates does not need to expose HTTP.

Liveness must not fail because an unavailable external provider would cause a restart loop. Readiness: check the service's essential dependencies, not all 11 building blocks. The worker is not a user-facing endpoint.

## 4. Provisioning: who creates what?

| Operation | Script / responsibility | Points to watch |
|---|---|---|
| Start the platform | Platform pipeline `.gitlab-ci.yml`, `ACTION=start` | Prepares the network, starts containers and seeds; do not run it for an analysis alone |
| DB + user, bucket + key, app secrets | `templates/bootstrap.sh` copied/adapted by the app | The template creates them **by default**. Remove unnecessary steps for frontend-only apps or apps without files |
| LLM + Temporal | `onboard-app.sh <app>` | Creates both and regenerates the gateway; not automatically enabled for every app |
| Optional bootstrap LLM | `LLM_VKEY=1` | Publishes key/config; check whether the gateway needs reseeding after creation, do not assume the runtime consumer is already active |
| Temporal namespace | `temporal/ns-create.sh <app>` or bootstrap option | `ns-create.sh` alone does not write connection details to OpenBao; bootstrap/onboard do |
| OIDC client | `idp/onboard-oidc.sh <app> <redirect_uri>` | Must be created separately; secret/config under `secret/<app>/oidc` |
| Test identities | `idp/seed-test-users.sh <app> [personas]` | Actual business personas from the specification; not platform admin for app tests |
| Analytics | `analytics/site-create.sh` or `ANALYTICS_SITE=1` | One site/app; application proxy and events must be implemented |
| pgvector | App migration | `CREATE EXTENSION IF NOT EXISTS vector` in the selected DB with appropriate privileges; not enabled by the generic bootstrap |

**PLAT-003 — MUST (human review):** adapt provisioning to declared needs and keep it idempotent. Why: avoid unused resources and ensure reproducibility after state loss. Compute: no unnecessary DB/bucket/namespace or keys. Do not modify the platform to hard-code an app's name into it.

Real secrets must not be written into the JSON contract, ADRs or examples. Development credentials and tokens published by the repository are not a model for production.

## 5. Choosing a non-canonical stack

The platform exposes protocols; it does not technically enforce TypeScript. The course's strict profile is a **policy**, separate from this interoperability.

For Python/Java/Go/.NET/etc.:

1. Check clients for Postgres, S3-compatible endpoint/path style, Valkey/Streams, OIDC, OpenBao and the OpenAI-compatible API according to the services used.
2. Check the Temporal SDK, its version and its target runtime **if Temporal is selected**. Do not assume the TypeScript SDK supports Bun because the API app does. Use an officially supported runtime and document the departure from the strict profile if necessary. For an unsupported language, design a compatible worker or choose another solution with justification.
3. Replace `bun install`, `tsc`, `bun test`, `bun audit` jobs with appropriate, pinned commands; retain the quality guarantees, not the command names.
4. Adapt images, non-privileged user, signals, build assets, health checks, native dependencies and CPU architecture. An Alpine/musl image is not compatible with every Python wheel, native extension or SDK; document Debian/glibc or multistage builds if necessary.
5. Keep shared API/event schemas and contract tests; sharing TS types between frontend/backend is no longer available by default.

**STACK-001 — MUST in `strict-typescript`:** justify and obtain approval for a language exception for the checked roles. Why: maintain consistent policy and manageable tooling. Compute: avoid multiple runtimes without a benefit. The validator checks the declared language, **not** all Bun/Vite/image requirements: check those during review. In `platform-compatible`, choosing Python with a real justification does not require a language waiver.

## 6. LLM: capabilities and limits actually delivered

APISIX is an **AI gateway**, not the application's general ingress. The app uses a virtual key and the contract's aliases, not a provider key or model names embedded in business logic.

- Chat: `task:cheap`, `task:quality`, `task:vision`, `task:reasoning` according to active routes.
- Embeddings: `task:embed`, `/v1/embeddings`, routed to OpenAI in both repository variants.
- Images: `task:image` in the OpenAI variant only; do not promise availability after switching to Anthropic.
- The selected provider and real keys are provisioned on the platform side; routes/consumers are generated from OpenBao. This is not evidence of an OpenBao call on every request.
- Token limits per window, not a guaranteed cumulative monetary quota. In Anthropic mode, the per-app budget override does not target the OpenAI embedding route: the repository notes a shared route limit. The image route does not declare the same token-limiting plugin.
- The repository notes that embeddings have not been exercised on a live instance; run the integration test before declaring the capability validated.

References: [OpenAI routes](../../../td/core-platform/apisix/routes.openai.yaml), [Anthropic routes](../../../td/core-platform/apisix/routes.anthropic.yaml), [seed](../../../td/core-platform/apisix/seed-and-deploy.sh). Do not present the repository's model names as the provider's current catalog.

## 7. Isolation and persistence

**DATA-001 — MUST, declarative check:** `vector_enabled` requires Postgres. **DATA-002 — MUST, v1 contract:** ORM/query-builder/SQL requires Postgres in the component's services. These rules check minimal consistency, not extension creation or actual connections. Why: avoid a decision that cannot be provisioned; compute: avoid an unjustified new vector database or SQL engine.

App resources are logically separated (DB/user, bucket/key, Valkey prefix, namespace, OIDC client, analytics site). The shared network and dev mode do not provide strong isolation between hostile tenants. A Valkey prefix is not an ACL, and a Temporal namespace is not authentication.

Temporal, Casdoor and Umami use shared Postgres: size the overall connection and I/O budget, rather than assigning all its capacity to a single app. The app's DB must not read these services' internal tables directly.

Postgres, Valkey, S3, Registry and OpenBao audit data have volumes. **OpenBao secrets are in memory**: restore/provision them after state loss. A volume is neither a verified backup nor replication.

## 8. What the platform does not provide

No business code, complete API, RAG pipeline, ready-to-use private upload, app analytics proxy, GPU, dedicated search engine, mail server or complete production observability. An `upstream` component for third-party flows is described as a contract, not implemented in the app compose.

A production context requires a separate deployment design: durable secrets, workload identity, TLS, least privilege, console authentication, backup/restore, availability and capacity. A passing skill check does not attest to these. Do not add Kafka, Kubernetes, a parallel Redis instance or a vector database to the workshop simply to claim a pattern; every addition requires a need, a cost assessment and platform adaptation.
