# Service decision sources and verification limits

Last source review: **2026-10-21**. This reference supports [data-and-storage](data-and-storage.md) and [service-decisions](service-decisions.md). It records documentation inspection, not a live integration, load, restore, authorization or production-readiness test.

## Authority and interpretation

1. The user's scope and the repository's actual implemented contract determine the intended change. Inspect current files before applying a remembered address, flag or deployment rule.
2. Compose and scripts establish **declared configuration and implemented provisioning**, not runtime health or achieved guarantees. Verify a live claim separately.
3. Contributor rules establish **local harness policy**, not a universal technical limitation or an instructor statement. For example, the local Stream pattern is narrower than all patterns supported by the vendor.
4. Official upstream documentation establishes capabilities and semantics for its documented versions. It does not establish which capability is enabled here.
5. The new skill's comparisons and worked examples are **engineering recommendations derived from those constraints**. They require project-specific evidence; no language, service or framework is guaranteed to meet a latency target by selection alone.

## Repository sources inspected

| Source | What it establishes | Limits |
| --- | --- | --- |
| [Core compose](../../../td/core-platform/podman-compose.yml) | Eleven services, image tags, ports, aliases, volumes, shared network, Valkey AOF, OpenBao dev mode, Temporal auto-setup, Dozzle socket | Image availability, running config, ACL enforcement and restore success are not proven by YAML |
| [Core README](../../../td/core-platform/README.md) and [requirements](../../../td/core-platform/requirements.md) | Intended local workshop operation, client paths, constraints | Reconcile narrative with current scripts where they differ |
| [App bootstrap](../../../td/core-platform/templates/bootstrap.sh) | Normal PostgreSQL/S3 provisioning; optional LLM, Temporal and analytics flags | Not a universal minimal bootstrap; it must be tailored when those defaults are unnecessary |
| [App onboarding](../../../td/core-platform/onboard-app.sh) | Combined app capability provisioning | Read bundled actions before using it for a single capability |
| [Secrets library](../../../td/core-platform/lib/secrets.sh) | Existing secret helper contract | Does not alone prove scoped runtime policies or production secret persistence |
| [Objectstore library](../../../td/core-platform/lib/objectstore.sh), [admin seed](../../../td/core-platform/objectstore/seed-admin.sh) | Per-app objectstore provisioning and initial identity setup | S3 compatibility, browser signing, CORS, recovery and required feature support need actual checks |
| [Temporal library](../../../td/core-platform/lib/temporal.sh) and [namespace creation](../../../td/core-platform/temporal/ns-create.sh) | App namespace provisioning | Retention semantics come from upstream docs; a namespace name does not authenticate its caller |
| [APISIX OpenAI routes](../../../td/core-platform/apisix/routes.openai.yaml), [Anthropic routes](../../../td/core-platform/apisix/routes.anthropic.yaml), [seed](../../../td/core-platform/apisix/seed-and-deploy.sh) | Task aliases, routing, credentials and configured quota scopes | Do not generalize text-route limits to embeddings/images or monetary budgets |
| [OIDC onboarding](../../../td/core-platform/idp/onboard-oidc.sh), [test users](../../../td/core-platform/idp/seed-test-users.sh) | Client versus persona provisioning | No claim that every latest grant or client type is already enabled |
| [Analytics site helper](../../../td/core-platform/analytics/site-create.sh), [app nginx template](../../../td/core-platform/templates/nginx.conf) | App analytics integration and proxy route contract | Does not establish a tracking purpose, permission, privacy outcome or SLO |
| [CCOE rules](../../../Elyes/CCOE-RULES.md) | Local explicit used/not-used decisions; PostgreSQL durability, S3 bytes, recoverable Valkey state, ownership, retention, queue scope, consistency | Its [audit matrix](../../../Elyes/audit-matrix.yml) is a review plan, not an executable proof |
| [Architecture skill](../../archi/SKILL.md), [ORM rules](../../archi/references/donnees-orm.md), [SLO strategy](../../archi/references/slo-strategy.md) | Language/framework, architecture and ORM decisions; latency-driven design | Do not duplicate or weaken its architectural decision record in this service skill |

## Contributor handoff sources

These skills supply integration detail after the service-selection decision. Read the relevant one when implementing that integration; their existence does not mean its code has already been installed in every app.

| Service | Contributor source | Relevant boundary |
| --- | --- | --- |
| PostgreSQL | [Elyes PostgreSQL](../../../Elyes/postgresql/SKILL.md) | Ownership, durable records, migrations, parameterized access |
| Valkey | [Elyes Valkey](../../../Elyes/valkey/SKILL.md) | Prefixes, TTL, recoverable jobs, bounded resource use |
| S3 | [Elyes SeaweedFS](../../../Elyes/seaweedfs-s3/SKILL.md) | Private buckets, scoped identities, object authorization and lifecycle |
| OpenBao | [Leandro secrets](../../../leandro/openbao-secrets/SKILL.md) | Provisioning/runtime separation, KV v2, startup and rotation |
| Casdoor | [Leandro OIDC](../../../leandro/casdoor-oidc/SKILL.md) | Client flows, sessions and server-side business authorization |
| APISIX | [Leandro LLM](../../../leandro/apisix-llm/SKILL.md) | Server-only virtual key, task aliases, bounds and failure handling |
| Temporal | [Hugo workflows](../../../hugo/temporal-workflows/SKILL.md), [operations](../../../hugo/temporal-operations/SKILL.md) | Durable process, activity idempotency, authorized signals and diagnosis |
| Umami | [Mathis instrumentation](../../../mathis/sdin-umami-instrumentation/SKILL.md) | Product question, limited events, proxy integration and non-blocking collection |
| Registry | [Mathis delivery](../../../mathis/sdin-registry-delivery/SKILL.md) | Artifact digest, build reuse, retention and rollback |
| Dozzle | [Mathis diagnosis](../../../mathis/sdin-dozzle-diagnostic/SKILL.md) | Structured/redacted logs, bounded diagnosis, real evidence |

## Official technical documentation checked

All links below were consulted on 2026-10-21. Keep this date when the text is unchanged; update it only after rechecking the relevant claim.

| Primary source | Claim used in the decision references | Version/interpretation caveat |
| --- | --- | --- |
| [PostgreSQL 17 constraints](https://www.postgresql.org/docs/17/ddl-constraints.html) | Constraints express database integrity rules | App schema and tenant authorization still need design and tests |
| [PostgreSQL 17 explicit locking](https://www.postgresql.org/docs/17/explicit-locking.html) | Row/table/advisory coordination has defined transaction semantics | An available lock primitive does not prove a business invariant |
| [PostgreSQL 17 full-text search](https://www.postgresql.org/docs/17/textsearch.html) | Built-in lexical search, configuration and indexing | Measure the actual language and query requirements |
| [PostgreSQL 17 backup approaches](https://www.postgresql.org/docs/17/backup.html) | SQL dump, filesystem backup and continuous archiving are distinct approaches | Choose only configured mechanisms and demonstrate a restore against RPO/RTO |
| [pgvector repository](https://github.com/pgvector/pgvector) | Exact and approximate vector search; indexing and filtering considerations | The `pg17` image tag is not an exact pgvector extension version; inspect installed extension/version |
| [Valkey persistence](https://valkey.io/topics/persistence/) | AOF/RDB and persistence-policy tradeoffs | `appendonly yes` alone does not prove loss window, backup or high availability |
| [Valkey eviction](https://valkey.io/topics/lru-cache/) | Memory limit/eviction policy versus expiry; no-eviction can reject writes | Compose does not explicitly configure the required memory policy or app quotas |
| [Valkey Pub/Sub](https://valkey.io/topics/pubsub/) | At-most-once, transient delivery | Never use it as the only record of mandatory work |
| [Valkey Streams](https://valkey.io/topics/streams-intro/) | Consumer groups, pending work and acknowledgement/recovery concepts | R-3-04 selects a narrower local competing-job pattern; persistence configuration still matters |
| [Valkey distributed locks](https://valkey.io/topics/distlock/) | Lease/token pitfalls and vendor discussion | The page is explicitly under technical review; no correctness claim or default adoption of its distributed-lock algorithm is inferred |
| [SeaweedFS Amazon S3 API](https://github.com/seaweedfs/seaweedfs/wiki/Amazon-S3-API) | S3 gateway/filer relationship and compatibility documentation | Wiki describes evolving upstream; verify needed operations on pinned 4.44 rather than assuming complete AWS equivalence |
| [OpenBao dev server](https://openbao.org/docs/concepts/dev-server/) | In-memory dev storage, initial KV v2 mount and dev-only assumptions | Current docs show 2.7.x; compose uses 2.6. Core dev-mode property is corroborated by local command/config |
| [OpenBao KV v2](https://openbao.org/docs/secrets/kv/kv-v2/) | Versioned secrets, data paths and policy separation | Validate the 2.6 endpoint/permissions; storing a rotated value is distinct from rotating the target service |
| [IETF RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html) | Current OAuth security guidance, code/PKCE and deprecated insecure patterns | Apply with OIDC validation and the actual supported client configuration |
| [Casdoor OAuth documentation](https://casdoor.ai/docs/how-to-connect/oauth/) | Provider endpoints and available grant concepts | `casdoor.org` redirects here; current docs can describe versions newer than pinned v1.858.0. A listed grant is not a recommendation to use it |
| [APISIX key-auth](https://apisix.apache.org/docs/apisix/plugins/key-auth/) | Consumer credential mechanism | Latest documentation displayed 3.19.0; compose pins 3.17.0. Actual headers/routes/limits come from repository templates |
| [Temporal workflow execution](https://docs.temporal.io/workflow-execution) | Durable execution, replay and worker/activity roles | External side effects still need idempotency; no achieved availability is inferred |
| [Temporal namespace management](https://docs.temporal.io/self-hosted-guide/namespaces) | Retention of closed history and explicit authorizer requirement | Namespace naming is not an authentication policy; current docs may exceed server 1.29 capabilities |
| [Distribution garbage collection](https://distribution.github.io/distribution/about/garbage-collection/) | Mark/sweep cleanup and concurrency requirements | Use the deployed Registry 2 procedure, preserve rollback references, and separate cleanup from publication |
| [Dozzle getting started](https://dozzle.dev/guide/getting-started) | Socket-based operation and separately configurable access/actions | Current docs showed 11.3.4; the repo uses floating `latest`. Do not infer enabled features or restricted socket authority from a read-only mount |
| [Umami introduction](https://docs.umami.is/docs) | Product analytics role and v3 documentation | Actual events/proxy/optional cache behavior come from local integration; no blanket privacy or legal guarantee is inferred |

## Version baseline observed in compose

| Service | Declared image tag |
| --- | --- |
| PostgreSQL/pgvector | `pgvector/pgvector:pg17` |
| Valkey | `valkey/valkey:9-alpine` |
| OpenBao | `openbao/openbao:2.6` |
| SeaweedFS | `chrislusf/seaweedfs:4.44` |
| APISIX | `apache/apisix:3.17.0-debian` |
| Temporal server | `temporalio/auto-setup:1.29` |
| Temporal UI | `temporalio/ui:2.53.3` |
| Casdoor | `casbin/casdoor:v1.858.0` |
| Umami | `umami-software/umami:3.3.1` |
| Registry | `library/registry:2` |
| Dozzle | `amir20/dozzle:latest` |

These tags are observations, not upgrade recommendations, immutable digests, or confirmation that an image was pulled. Before using a version-specific feature, inspect the deployed version and relevant official version documentation. Pin and verify delivery identity according to [delivery-github](delivery-github.md).

## What a project still has to verify

Record each claim as observed in files, planned, actually tested, or blocked. Minimum relevant evidence includes authorized and denied data access, actual service reachability from each client class, secret isolation, intended operations, failure/retry behavior, cold and loaded latency, backup restoration, and image/workflow/schema rollback compatibility. Run only the checks appropriate to selected services; a static site should not acquire eleven integration dependencies merely to satisfy a template.

No live platform mutation, external provider call, load run, backup restore or production deployment is established by this source review.
