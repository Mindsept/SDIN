# Platform services: when to choose them and how

Use this reference after [scoping](scoping.md), alongside [data-and-storage](data-and-storage.md). It covers the eleven services declared by the current [core compose](../../../td/core-platform/podman-compose.yml). **Available in the platform** does not mean **required by every app**, **already provisioned for this app**, or **ready for production**. Record those states separately.

For every decision, state the business need, selected option, rejected simpler option, runtime consumer, provisioning owner, required configuration, failure behavior, proof, and reconsideration/removal condition. Record services as used, not used, or conditional; an unexplained list of all eleven services fails DVC-001. Sources were reviewed on 2026-10-21; see [service-sources](service-sources.md).

## 1. Choose app components before connecting services

| Situation | Choose | Do not add |
| --- | --- | --- |
| Build-time public content, no secret and no server behavior | Static frontend/artifact | Empty API, PostgreSQL, queue or worker to fill a template |
| Private data, server credentials, authorization or business mutations | API/backend, or server framework selected by [archi](../../archi/SKILL.md) | Direct browser database, OpenBao root, S3 access keys or APISIX virtual key |
| One short operation reliably fits the request SLO | Synchronous application service | A worker merely because an SDK is asynchronous |
| Independent work must survive the response/process restart | A durable job record and one justified worker mechanism | Fire-and-forget request tasks presented as reliable jobs |
| Multi-step process needs persisted progress, timers or human signals | Temporal worker and workflows | A second Stream-based scheduler for the same workflow without a distinct need |
| CPU-heavy processing needs a different runtime/scaling policy | Separate worker if measured or clearly required | A microservice for every controller or platform integration |

An API or worker has controller/transport, application service, domain and adapter boundaries according to [archi's patterns](../../archi/references/architectures.md). Selecting a service does not force a new language, framework or repository. Both an API and a worker can use the same application-owned database through the same business rules.

## 2. Inventory and dependency roles

The addresses below describe the local workshop contract. Host ports are local operator access, not production public URLs. Check the actual compose, provisioning output and network before use.

| Service | Actual purpose | Typical consumer and endpoint | Select / omit |
| --- | --- | --- | --- |
| `postgres` | Authoritative relational storage; pgvector available in image | API/worker → `postgres.internal:5432`; host `5432` | Select for durable structured app data; omit for stateless/static apps |
| `valkey` | Shared cache, expiring state, recoverable job pattern | API/worker → `valkey.internal:6379` (`redis.internal` alias); host `6379` | Select per measured/shared need; omit by default when simpler storage suffices |
| `openbao` | Service secrets and configuration under app paths | Backend/provisioner → `openbao.internal:8200` (`vault.internal` alias); host `8200` | Select for platform service credentials; no browser dependency or business-data storage |
| `s3` | SeaweedFS S3-compatible object storage | Backend → `http://host.containers.internal:9000`; host `http://localhost:9000` | Select for persistent/shared uploaded or generated files; omit for packaged assets only |
| `apisix` | Shared external LLM/AI gateway in this repo | Backend → `http://llm.internal:9080/v1`; host `9080` | Select when external AI is justified; omit for deterministic/no-AI features |
| `temporal` | Durable workflow orchestration | Backend client/app worker → `temporal.internal:7233`; host `7233` | Select for process durability; omit for ordinary CRUD or simple synchronous work |
| `temporal-ui` | Inspect and operate workflows | Operator browser → `http://localhost:9233` | Operational aid when Temporal is used; never a business runtime API |
| `casdoor` | Shared identity provider, OAuth/OIDC | Backend → `http://idp.internal:8000`; local browser entry `http://localhost:9300` | Select when user login is needed; omit for anonymous public features |
| `umami` | Product usage measurement | App analytics proxy → `http://analytics.internal:3000`; operator host `9400` | Select for explicit product questions; omit unused tracking |
| `registry` | Container artifact publication/distribution | Build/deploy tools → reachable registry; workshop host `localhost:5000` | Operational dependency for this container delivery flow, not a request dependency |
| `dozzle` | Inspect container logs | Operator browser → `http://localhost:9999` | Operational aid for container diagnostics; no application SDK or business dependency |

The three data services have detailed choose/refuse/integration rules in [data-and-storage](data-and-storage.md). PostgreSQL's use **by** Casdoor, Temporal and Umami does not imply an application needs its own PostgreSQL database. Dozzle and Registry are operational tools; exclude them from application request dependency graphs and readiness probes unless a genuine application function has been separately designed to depend on them.

## 3. OpenBao versus environment variables or no secret service

**Choose OpenBao** when the backend consumes platform database/objectstore/identity/gateway credentials. It is the platform's configured secret source. **Choose ordinary configuration** for non-secret values such as an app name, timeout or feature flag; not every setting needs a vault lookup. **Choose no app integration** for a public static app with no server-side credential. Do not add OpenBao to the browser because the frontend uses an authenticated API.

How to integrate:

1. Separate a privileged provisioning identity from the app runtime identity. Limit runtime access to the required `secret/<app>/...` paths and operations. App name/path prefixes alone do not enforce this policy; verify an out-of-scope read is denied.
2. Supply the initial authentication mechanism from the deployment's credential channel. The token needed to read OpenBao cannot be recovered solely from the locked OpenBao instance itself. Do not bake it into images, source, frontend variables or logs.
3. The current dev server exposes KV v2 at `secret/`; use the KV v2 data path/envelope. Read and validate required credentials during initialization or controlled refresh, then manage clients/pools. Do not fetch every secret on every HTTP request.
4. Distinguish denied access, missing secret, malformed data and unavailable OpenBao. Fail startup/readiness for a missing essential credential; an existing valid credential may continue according to a stated expiry/rotation policy. Never silently use a workshop default password as fallback.
5. Coordinate rotations with the target service and connection pools. Restoring an older KV value does not restore a PostgreSQL password or revoke an issued S3 credential. Dynamic leases exist only when their secret engine/authentication configuration actually issues them.
6. Treat the current OpenBao container as **dev, in-memory secret storage**. Its audit volume does not preserve secrets across restart. Record reseeding and credential recovery for the workshop; durable storage, TLS, scoped authentication and a tested recovery design are requirements for a production topology, not properties proven by this compose.

Reconsider the integration if the app ceases to need server credentials; remove obsolete credentials after consumers have migrated. Alternative enterprise secret managers require an explicit platform contract change, not parallel secret copies. Evidence: required read succeeds, unrelated app/core paths fail, no frontend/image/log exposure, startup and rotation/outage cases behave as designed. Handoff: [OpenBao integration skill](../../../leandro/openbao-secrets/SKILL.md). Vendor details: [KV v2](https://openbao.org/docs/secrets/kv/kv-v2/) and [dev server](https://openbao.org/docs/concepts/dev-server/).

## 4. Casdoor versus local authentication or anonymous use

**Choose Casdoor** when users must log in, ownership is private, roles distinguish access, or shared identity/SSO is required. **Omit login** for intentionally public, anonymous read-only content. An anonymous app may still need abuse controls and server credentials. **Do not create a local password table** to replace the shared provider simply because the framework has an authentication module. The framework may manage the application session while Casdoor supplies identity.

Choose the flow by client type:

| Client | Selected approach | Rejected shortcut |
| --- | --- | --- |
| Web app with backend | Authorization Code with PKCE, backend token handling and protected session cookie | Client secret in JavaScript; direct collection of Casdoor passwords |
| Browser-only SPA or native app | Public-client Authorization Code with PKCE if supported and correctly provisioned; evaluate whether a backend is actually required for app secrets | Reuse a confidential client secret in a downloadable bundle |
| Machine job with no human user | A specifically provisioned machine identity and supported grant/credentials | Log in as a fabricated human administrator or reuse a browser session |
| Fully public content | No OIDC flow | Login merely to make every service appear in the diagram |

How to integrate:

1. Provision a separate app client with [onboard-oidc](../../../td/core-platform/idp/onboard-oidc.sh); test personas come from a separate helper. Read app-scoped OIDC configuration from OpenBao. Do not use provider administration credentials in the app.
2. Set fixed allowed redirect/logout origins. Ensure the browser can reach the login origin and the backend can reach discovery/token endpoints while validating the expected issuer consistently. Do not invent public/internal issuer equivalence or derive redirects from an untrusted Host header.
3. Use a maintained OIDC library and validate signature, issuer, audience, expiry and flow-specific state/nonce/PKCE. Verify behavior against the pinned Casdoor version; latest online docs may describe newer grants or options.
4. Define cookie attributes, CSRF handling, session lifetime, refresh, logout and revocation. Choose PostgreSQL versus Valkey session state using actual durability/scale needs, not because authentication automatically needs Valkey.
5. Map the authenticated subject to business permissions on the server. Check object/tenant access on reads, writes, uploads, jobs and workflow signals. OIDC identity, app session, API access token and APISIX virtual key serve different purposes.
6. Define provider-outage behavior: new login can fail while already valid sessions may remain usable under the documented policy. Never bypass authorization or create an emergency anonymous admin path.

Evidence: allowed user succeeds; another user/tenant, expired token, wrong issuer/audience and tampered callback fail; logout works according to the declared session policy. Reconsider only when client type, identity federation or deployment constraints change; a different identity provider requires a documented platform exception and account migration plan. Handoff: [Casdoor integration](../../../leandro/casdoor-oidc/SKILL.md). Prefer the [OAuth security BCP](https://www.rfc-editor.org/rfc/rfc9700.html) over choosing a legacy grant merely because [Casdoor lists it](https://casdoor.ai/docs/how-to-connect/oauth/).

## 5. APISIX versus direct AI calls or no AI

**Choose deterministic code, ordinary search or a template** when it adequately answers the requirement. **Choose APISIX** when an external AI capability has a defined value and quality acceptance criteria. The repository uses APISIX as its LLM gateway; it is not already configured as a general application ingress or as the application's user-authentication layer.

How to integrate:

1. Provision an app virtual key with the existing onboarding flow and retrieve `secret/<app>/llm`. Keep provider keys in the platform's control. Only the backend/worker sends the app virtual key; never expose it to a browser or arbitrary client.
2. Expose an authorized business operation, such as summarizing an owned document, instead of an unrestricted proxy accepting arbitrary provider URL, model, headers and messages. Use the configured base URL and `task:*` aliases.
3. Prefer the cheapest task/model that passes a documented quality evaluation; promote to a stronger task only for demonstrated failures. Bound input size, output tokens, calls per operation, agent loops, retries, concurrency and user/app budgets.
4. Validate the actual provider and route capabilities. In current templates, embeddings route to OpenAI even when the text provider is Anthropic; images are OpenAI-only. The image path and embedding path do not necessarily inherit the text route's per-app token limit. Inspect the rendered routes and credentials instead of assuming one successful chat call validates all modalities.
5. Treat token/window limits as their configured mechanism, not as proof of a global monetary budget. Account for embeddings, images, repeated attempts and other routes. Keep rendered credential-bearing configuration out of source control.
6. Classify denied credentials, quota rejection, upstream failure and timeout separately. Retry only when appropriate and bounded; an unknown outcome may already have incurred cost. Never fail over directly to a provider to evade the platform gateway.
7. Use the SLO to choose synchronous streaming versus durable asynchronous work. Measure first-byte/first-token, total completion, failure rate and cancellation separately. Streaming is not a guarantee of final-response latency.
8. Treat documents, prompts, model output and tool arguments as untrusted input. Authorize tools independently, validate structured output and protect data boundaries. Log identifiers, timing, usage and error class without secret keys or sensitive full prompts.

Evidence: the intended task alias works through APISIX; unauthorized calls and cross-tenant input fail; provider/quota failure is bounded; quality/cost/latency match the chosen route. If deterministic behavior becomes sufficient, remove the AI call and associated key. A locally hosted model is a new capacity/platform proposal, not an automatic bypass. Handoff: [APISIX integration](../../../leandro/apisix-llm/SKILL.md). [APISIX key-auth](https://apisix.apache.org/docs/apisix/plugins/key-auth/) explains gateway credentials; local route templates determine actual enabled behavior.

## 6. Temporal versus a worker queue, cron or synchronous work

| Requirement | Choose | Why the alternatives are insufficient or unnecessary |
| --- | --- | --- |
| Short bounded request with one result | Synchronous application service | Workflow history and worker lifecycle add no required capability |
| Independent recoverable thumbnail/export job | Stream worker, or a justified existing database queue | Temporal is optional complexity if there are no process-level waits or dependencies |
| Durable multi-step processing with retries/compensations | Temporal | A queue entry alone does not preserve the process's decisions and progress |
| Wait hours/days for a human decision or external callback | Temporal durable wait/signal with authorization | A process sleep or open HTTP request does not survive normal replacement |
| Simple periodic housekeeping with safe repeated runs | Existing deployment scheduler if adequate | Temporal is not required merely because a job runs periodically |
| Scheduled durable business process with overlap/catch-up/cancellation semantics | Temporal schedule plus defined workflow policy | An unspecified timer/cron cannot demonstrate those semantics |

How to integrate:

1. Provision the per-app namespace and select app-owned task queues. Deploy an app worker: the core Temporal server does not run application activities by itself. A namespace or task queue name is not an authorization credential.
2. Use stable business workflow IDs, an explicit duplicate-start/reuse policy and authenticated ownership checks for status, signals and cancellation. Put sensitive authorization in the application boundary before calling Temporal.
3. Keep workflow logic deterministic; place I/O and side effects in activities. Use activity timeouts, bounded retries and heartbeats where suitable. Make external effects idempotent, record outcomes and define compensations; workflow durability is not automatic exactly-once execution of external systems.
4. Keep payloads small and pass references to PostgreSQL/S3 records. Avoid putting full private documents or long-lived credentials in history. Bound history growth and use supported history-management patterns when necessary.
5. Define worker deployment compatibility and replay checks before changing running workflow code. Select SDK/version mechanisms actually compatible with the pinned server and worker SDK; do not copy a newly documented feature without checking support.
6. Set business deadlines, queue-age/completion targets, cancellation semantics and operator procedures. Namespace retention controls how long **closed workflow history** is kept; it is not the maximum running-workflow duration and need not be copied from that duration.
7. The local server uses an auto-setup image and shared PostgreSQL. The compose does not configure authentication/mTLS or production HA. Namespace separation does not prove access isolation, disaster recovery or production availability.

Evidence: worker restart resumes the intended process; duplicate starts/signals and repeated activities do not duplicate business effects; unauthorized actors cannot signal another user's process; migration/replay and recovery procedures are demonstrated. If the process collapses to one independent job, reassess the orchestration cost. Handoff: [workflow skill](../../../hugo/temporal-workflows/SKILL.md) and [operations skill](../../../hugo/temporal-operations/SKILL.md). Vendor references: [workflow execution](https://docs.temporal.io/workflow-execution) and [namespace retention/security](https://docs.temporal.io/self-hosted-guide/namespaces).

## 7. Temporal UI: operator interface, not application state

**Use Temporal UI** to inspect a selected workflow's state/history and support bounded diagnosis. **Do not query/scrape it** to drive the product, store business data, or decide API readiness. An app uses Temporal's client API behind its own authorization boundary.

Limit access to authorized operators and namespace/task scope; workflow payloads may contain sensitive information. Verify namespace, workflow/run identifiers, time range and retention before concluding a missing item never ran. Starting, signaling, terminating or deleting is a separate operational action from viewing. UI unavailability must not fail business operations that can still reach Temporal. Remove the app's UI dependency from the plan if Temporal is no longer selected; the shared UI may still serve other apps.

## 8. Umami versus logs, audit records or no analytics

**Choose Umami** only to answer stated product questions such as funnel abandonment or feature adoption. **Choose operational measurements** for latency/error/queue SLOs. **Choose durable business/audit records** for accepted commands, permissions or required traceability. These are different purposes; Umami is not a source of truth for completed orders or an audit guarantee. **Omit tracking** if no useful question, owner or review cadence exists.

How to integrate:

1. Provision one app site and configuration through [site-create](../../../td/core-platform/analytics/site-create.sh); never give the browser the administration token.
2. Follow the app's proxy pattern: browser → `/api/v1/_a/t.js` or `/api/v1/_a/send` → app API proxy → `analytics.internal:3000`. A browser cannot normally resolve the private service hostname. Do not add an otherwise empty API without comparing the value and cost of tracking.
3. Define event name, single emitter, exact trigger, properties, retention and product owner. Emit a business success only after authoritative confirmation; prevent duplicate automatic/manual events.
4. Exclude secrets, personal content, sensitive URL/query/referrer data and unbounded labels. Handle applicable user choice requirements in the actual product context. Trust forwarded network headers only from the known proxy chain.
5. Let tracking failure drop/skip collection with bounded effort; it must not fail checkout or navigation. Do not add a durable tracking queue or Valkey merely because analytics exists. This platform does not configure Umami's Valkey dependency.

Evidence: one known user journey produces the intended limited event set; blocked/unavailable analytics does not break it; unexpected payload data is absent. Retire events/site access when the product question or app ends. Handoff: [Umami instrumentation](../../../mathis/sdin-umami-instrumentation/SKILL.md).

## 9. Registry versus a runtime service or external registry

**Use the shared Registry** for the repository's container publication and delivery flow. The application process does not call Registry to serve normal requests. **Do not publish an image for a nonexistent component**; a frontend-only app needs only its actual artifact. A different registry is an explicit delivery/platform choice when runner reachability, authentication, governance or retention demands it; do not silently maintain two unowned artifact stores.

How to integrate:

1. Build the necessary components, publish traceable `<registry>/<app>/<service>:<version>` references, record the published manifest digest and deploy that same artifact. Pin release identity and preserve rollback references.
2. In the local workshop, `localhost:5000` addresses the registry only from the machine where it is exposed. A GitHub-hosted runner's localhost is a different machine. Select an authorized reachable runner/registry design using [delivery-github](delivery-github.md).
3. Keep secrets out of layers/build arguments. Verify target architecture, required runtime files, provenance and startup compatibility; image size alone is not a release-quality test.
4. Treat the current HTTP local registry as a development arrangement. TLS, authorization, backups, scanning policy and retention must be configured before asserting production controls.
5. Retain deployed and rollback digests plus their required schema/workflow compatibility. Plan deletion and garbage collection separately; use the appropriate registry procedure and protect concurrent writes. [Distribution garbage collection](https://distribution.github.io/distribution/about/garbage-collection/)

Evidence: published digest equals deployed artifact, restart succeeds, retained rollback is usable with current data. Registry downtime can block deployment/new image pulls while already running apps continue; do not add it to API readiness. Handoff: [Registry delivery](../../../mathis/sdin-registry-delivery/SKILL.md).

## 10. Dozzle versus observability backends or no extra collector

**Use Dozzle** for targeted inspection of container stdout/stderr during local operation. Emit structured logs with request/job IDs, service, route template, status, duration and error class. Reuse the app's logger; no Dozzle SDK is required.

**Do not choose Dozzle alone** for durable audit retention, SLO alerting, metrics history, distributed tracing or guaranteed forensic preservation. If those requirements exist, identify the missing collector/store/alerting capabilities, compare existing facilities, and propose the minimum necessary platform extension. Do not add a full monitoring stack merely because Dozzle displays logs.

How to integrate: produce redacted structured output; configure runtime rotation/retention; correlate a bounded scenario; limit operator access; time-box diagnostic verbosity. The compose mounts a rootless Podman socket with a read-only filesystem mount; that mount does **not** prove the socket API has read-only authority. Verify configured Dozzle capabilities and socket exposure. Its current image tag is `latest`, so do not assume reproducible feature/security behavior without recording the resolved version/digest.

Evidence: trace an API request through its actual worker where present; confirm secrets/private payloads are absent; verify retention/rotation and log-volume limits. Dozzle failure must not break app readiness. Do not sample only slow requests and then claim the resulting percentile represents all requests. Handoff: [Dozzle diagnosis](../../../mathis/sdin-dozzle-diagnostic/SKILL.md).

## 11. Provisioning is a separate decision from feature selection

Read the actual helpers before executing them. The [bootstrap template](../../../td/core-platform/templates/bootstrap.sh) currently provisions PostgreSQL and S3 in its normal path; it is not a universal minimal bootstrap for every application. Tailor the app bootstrap to its selected services. Do not claim an optional database/bucket flag exists unless it is implemented.

| Desired capability | Existing provisioning mechanism | Boundary to preserve |
| --- | --- | --- |
| App relational data | Bootstrap and secret helpers | App DB/role; no access to other service databases |
| Persistent objects | Objectstore helpers; `PUBLIC_BUCKET` only for intentionally public assets | App identity/bucket; first core identity must be seeded before relying on access restrictions |
| External AI | `LLM_VKEY` feature flag and onboarding | App virtual key versus platform provider keys; onboarding may bundle other capabilities |
| Workflow orchestration | `TEMPORAL_NS` flag and namespace helper | App namespace/task queues; auth remains a separate capability |
| Product analytics | `ANALYTICS_SITE` flag and site helper | App site versus administration token |
| Login and test actors | Separate OIDC onboarding and test-user seeding helpers | Real app client versus personas and provider administrator |

The combined [onboard-app helper](../../../td/core-platform/onboard-app.sh) provisions more than one capability; it is not automatically appropriate for an app needing only one. Shared core seeding is an operator responsibility. In particular, initial objectstore identity seeding closes its initial anonymous state, and identity/analytics initialization order matters because both use shared PostgreSQL. Never reset shared core services to fix an app's configuration.

Use [operations](operations.md) for app-scoped lifecycle and recovery. Disable a feature only after determining how existing data, sessions, jobs/workflows, keys and retained artifacts are handled. Disabling an app feature does not authorize deleting a shared service or another app's resources.

## 12. Consumer paths and failure boundaries

| Application type | Main consumer path | Explicitly conditional or omitted |
| --- | --- | --- |
| Static public site | Browser → frontend artifact | No server secrets, database, worker or identity; Umami only if useful and justified |
| Authenticated CRUD app | Browser → app API → PostgreSQL; browser/backend ↔ Casdoor; backend → OpenBao | Valkey only for a justified cache/session need; no S3 without files |
| Private file portal | Browser → authorized API → PostgreSQL/S3; optional scoped direct transfer | Processing worker only if needed; no Temporal for simple upload |
| Fast shared read API | Client → API → authoritative PostgreSQL; optional measured Valkey cache | Freshness and fallback determine cache eligibility; no automatic second database |
| AI document tool | Browser → API → owned data/S3; API or worker → APISIX; PostgreSQL/pgvector when retrieval is needed | One justified ingestion/job mechanism; Temporal only for durable process semantics |
| Approval/business workflow | Browser → API → Temporal; worker → business PostgreSQL/external effects | UI is operator-only; Valkey not required to make Temporal function |

For each arrow, identify caller identity, allowed operation, reachable URL, timeout, retry/idempotency, data sensitivity and ownership. Internal names are for the container network; browser addresses and CI runner addresses require separate reachability. Application port blocks are 8000–8999 in blocks of ten, excluding 8200–8209 reserved around OpenBao; use only the slots for components actually present.

Define `/health` for process health and `/ready` for essential capability readiness with bounded checks. An optional analytics outage, missing diagnostic UI or unavailable Registry must not make an otherwise functioning business API unready. If a database, required queue, identity function or AI route is essential only to some endpoints, describe route-level degraded behavior instead of masking it as universal health. Stop accepting work and drain safely on SIGTERM within the local shutdown contract.

For production or stronger SLOs, compare required isolation, TLS, secret persistence, backups, capacity, failover and operator access with what is **actually configured**. A shared network, app prefix, bucket name or Temporal namespace is not proof of authorization isolation. Mark gaps and choose a justified platform evolution; do not promise that these development defaults meet an untested SLO.
