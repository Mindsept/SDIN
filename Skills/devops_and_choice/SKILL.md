---
name: devops-and-choice
description: "Choose the smallest sufficient set of SDI services and adapt delivery to the repository's actual CI and artifacts. Use for service decisions, provisioning plans, CI/CD and operating reviews; planning does not authorize deployment or platform changes."
---

# SDI service choices and DevOps

Make an **explicit, justified service and operating decision** for the requested application. State when to use a technology, when not to use it, how to integrate it, and what evidence could change the choice. Keep all skill documents and generated templates in English unless the user requests another language.

This is an upstream decision skill and an operating guide. It does not make every available service mandatory, install itself globally, register a runner, authorize publication, or change the agent's global rules.

## Sources, boundaries, and authority

- Locate the actual repository and inspect `td/core-platform/`; never assume the current directory. This skill's repository root is `../..`. When copied elsewhere, locate that root and distinguish the recorded contract from a live deployment.
- Distinguish **observed repository configuration**, **local team rules**, **this skill's proposed policy**, **user choices**, and **measured results**. Do not attribute an invented approval to the instructor.
- Apply the relevant rules from [Skills/CCOE-RULES.md](../CCOE-RULES.md) when that policy governs the project. Record which rules apply. Service-specific rules are N/A when the service is not selected; explain why. Resolve a real conflict explicitly instead of silently changing a MUST into a preference.
- Preserve viable existing decisions and explicit authorizations. Do not ask again for a supplied answer. A proposal to consume a service does not authorize changing a shared platform.
- For language, framework, internal code organization, and full architecture design, use [the architecture skill](../archi/SKILL.md) when available. Its response-time SLO contract remains applicable. This skill adds service and delivery choices, not a second competing stack policy.

## Working modes

**Choose:** compare candidate services for a concrete need, including no additional service. **Design:** produce a minimal service-use and operations plan. **Review:** compare declared decisions to code/configuration and evidence. **Implement:** make the explicitly requested local changes and verify them; execution against an environment remains within the user's authorized scope. A focused “Postgres or Valkey?” question needs a focused answer, not every artifact below.

## Reference routing: when to read what

Route from the user's decision and facts already supplied, not merely from a technology name. For a focused question, start with the matching row below and read the indicated sections. Follow the next reference only if its condition applies. Do not load the entire catalog, repeat an answered questionnaire, or generate a full plan for a narrow comparison.

| Situation or missing decision | Read first | Follow-up condition and expected result |
|---|---|---|
| Ownership, loss tolerance, SLO, trust or deployment target is unclear | [Scoping](references/scoping.md), relevant first-round/conditional questions | Ask only questions that change the choice, then return to the matching row below. Keep the affected decision provisional |
| Does this app need a backend or any platform service? | [Service decisions §1–2](references/service-decisions.md#1-choose-app-components-before-connecting-services) | Read [data and storage §1](references/data-and-storage.md#1-decide-by-the-meaning-of-the-data) only if state/files are needed. Output retained components and explicit service omissions |
| PostgreSQL versus Valkey, local memory, SQLite, ORM, or no database | [Data and storage §1–3](references/data-and-storage.md#1-decide-by-the-meaning-of-the-data) | For ORM implementation, use [archi's ORM guide](../archi/references/donnees-orm.md); for a performance claim, follow the SLO row. Decide authority, cache eligibility and the simpler rejected option |
| Uploads, generated files, object access or partial cross-store writes | [Data and storage §4–5](references/data-and-storage.md#4-s3-versus-database-bytes-versus-the-filesystem) | Read [operations §3–4](references/operations.md#3-migrations-and-cross-store-consistency) when persistence needs migration/recovery. Decide bytes/metadata ownership, authorization and reconciliation |
| Pub/Sub, Stream, database job table, cron or workflow engine | [Data and storage §3](references/data-and-storage.md#3-valkey-decide-separately-for-each-use-case), queue subsection | Read [Temporal decisions §6](references/service-decisions.md#6-temporal-versus-a-worker-queue-cron-or-synchronous-work) when durable waits/stages/signals are present. Decide delivery/recovery semantics and one justified processing mechanism |
| A response deadline, cache or deferred result could change the design | [SLO questions](references/scoping.md#slo-follow-up-without-jargon-overload), then [archi's SLO strategy](../archi/references/slo-strategy.md) | Read [data and storage §7](references/data-and-storage.md#7-let-latency-availability-and-recovery-change-the-choice) for the service consequence. State complete-result versus acknowledgment targets before choosing cache/jobs/streaming |
| Secret storage, runtime credentials or user login | [Service decisions §3–4](references/service-decisions.md#3-openbao-versus-environment-variables-or-no-secret-service), only the applicable service | Read [operations §5](references/operations.md#5-identity-secrets-networking-and-rotation) for rotation/access behavior. Decide OpenBao versus ordinary config and Casdoor versus anonymous use; keep user identity and workload secrets distinct |
| Search, embeddings, RAG or an LLM feature | [Data and storage §6](references/data-and-storage.md#6-search-none-sql-full-text-pgvector-or-a-separate-engine) for retrieval; [service decisions §5](references/service-decisions.md#5-apisix-versus-direct-ai-calls-or-no-ai) for model calls | Follow the SLO/queue rows only if latency or ingestion requires them. Decide lexical/vector/model necessity, data ownership and limits; do not add RAG to every AI feature |
| Product analytics, logs, workflow inspection or SLO monitoring | [Service decisions](references/service-decisions.md), §7 Temporal UI, §8 Umami or §10 Dozzle according to the question | Read [operations §6](references/operations.md#6-observability-choose-the-signal-for-the-question) when durable measurements, audit or alerts are needed. Select the signal/tool and identify missing capabilities |
| Which resources should bootstrap create, or which endpoint can each consumer reach? | [Service decisions §11–12](references/service-decisions.md#11-provisioning-is-a-separate-decision-from-feature-selection) | Inspect the linked repository helper/Compose file before implementation. Decide the exact app resources and caller endpoints; service selection alone does not execute provisioning |
| GitHub checks, runner location, build gates, registry or deployment | [GitHub delivery](references/delivery-github.md), §1–2 entry points/runners, §4 gates, §6 registry or §7 deployment as relevant | Read [operations §3](references/operations.md#3-migrations-and-cross-store-consistency) for schema changes and [§7](references/operations.md#7-stop-purge-deletion-rollback-and-incident-branches) for recovery. Output the selected execution path, gates and required setup |
| Health, overload, migration, backups, rotation, rollback or an incident | [Operations](references/operations.md), matching §1–7 | Reopen service selection only if the operating requirement cannot be met by the chosen service. Output a scoped procedure, owner, failure behavior and evidence |
| A platform fact, vendor capability, version or contributor handoff needs verification | [Service sources](references/service-sources.md), repository sources / official documentation / contributor handoffs as appropriate | Follow the specific source for the disputed claim; recheck version-sensitive documentation. Do not treat the source index as runtime proof or read every contributor skill |
| Language, framework or internal code organization is the real question | [Architecture skill](../archi/SKILL.md), its matching reference route | Carry existing facts and SLOs across. Return here only for an unresolved service/delivery decision; do not cycle between skill entry points |
| An applicable rule conflicts with the proposed technology | This skill's **Exceptions** section, then [archi's waiver guide](../archi/references/derogations.md) if needed | Produce the concrete rule/evidence/authority/expiry record; a permitted alternative needs no invented waiver |
| A full service plan or operating handoff is requested | [Service plan](assets/service-plan.md) and, for operating procedures, [runbook](assets/operations-runbook.md) | Use after relevant choices are made. For an existing architecture JSON, read [its contract](../archi/references/contrat-machine.md) only when editing/validating it; templates are output assets, not extra prerequisite reading |

For a complete design, read in stages: scoping → relevant service/data choices → SLO implications → delivery → selected operating procedures → deliverable assets. For example, “Valkey for faster reads?” routes to data/storage §3, then SLO strategy if performance is the reason; it does not require the GitHub runner guide. “Deploy to my local Podman host from GitHub” starts with delivery §1–2, then the applicable deployment/recovery sections.

If a new answer changes a constraint (for example, no stale reads, human approval, or a remote target), reroute that decision and revisit its dependents. Reuse prior conclusions and already loaded references. A cross-skill handoff carries the known facts, chosen policy and unresolved question; it does not restart the entire process. Stop expanding references once the requested decision and its material dependencies are supported.

## Required decision process

### 1. Clarify the facts that change the choice

Read the relevant [scoping](references/scoping.md) questions. Inspect the brief and code first; reuse known service choices and ask only decision-changing questions. A cache choice needs freshness and workload facts, not automatically a delivery plan. For a full design, cover the user outcome, data/loss tolerance, targets, trust and environment. Keep critical unknowns visible without blocking unrelated work.

Do not ask the user to select a product name before understanding its purpose. In “psql or Valkey?”, distinguish PostgreSQL, the database, from `psql`, its command-line client.

### 2. Choose services from conditions, not availability

Read [data and storage decisions](references/data-and-storage.md) for PostgreSQL, Valkey, S3, search, vectors, and consistency; read the relevant sections of [service decisions](references/service-decisions.md) for all platform services.

**DVC-001 — MUST:** for every proposed dependency, write:

> Choose X because these project conditions hold. Do not choose Y or add another service because this condition is absent. Configure/integrate X this way. Verify these behaviors. Reconsider when this measurable condition changes.

Record **used / not used / undecided**, need, simpler alternative, evidence and revisit trigger in the existing app decision. For selected dependencies, add only relevant consumer, ownership, limits and failure/recovery details. Group unused services; do not write eleven operating runbooks. `Undecided` is provisional. Under local CCoE rules, keep the concise service-use table in the README. Platform-internal dependencies and operator tools are distinct from app runtime dependencies; Casdoor/Temporal/Umami using PostgreSQL does not require an app DB.

Start with one compatible client per process and the smallest useful queue/pool/bucket/site setup. Derive connections, concurrency, bytes, TTL/retention and retry budgets from the accepted workload and shared capacity, not a generic “enterprise” configuration. Unknown demand calls for a stated initial envelope and revisit measurement, not guessed replicas or a new cluster.

The essential branches are:

| Need established | Starting decision | Do not infer |
|---|---|---|
| No shared state, secret, or server-side operation | No business backend or data service | A template requires API, worker, DB, and bucket |
| Durable structured facts and atomic invariants | PostgreSQL as the application source of truth | Valkey persistence makes it an interchangeable business database under the local policy |
| Repeated expensive reads with acceptable staleness | First optimize the authoritative read; add bounded local cache or shared Valkey only when justified | Every app needs Redis-compatible caching |
| Large files, exports, or corpus objects | S3 API with ownership/metadata and authorized access | A bucket is a filesystem or a SQL transaction participant |
| Independent retryable work with deferred completion accepted | Compare an adequate durable job mechanism and the local Valkey Stream pattern | Pub/Sub is a durable queue; fast acceptance proves timely completion |
| Durable waits, timers, multi-step retries, compensation, or human approval | Temporal under the applicable local workflow rule | A Stream alone provides workflow replay/history |
| User login and federated identity | Casdoor/OIDC plus application object authorization | An identity token grants access to every record |
| Server-side secrets | OpenBao with separate provisioning and runtime rights | A secret path or app prefix proves isolation when credentials are shared/root |
| Required remote LLM capability | APISIX route and app virtual key, with app-level limits/evaluation | APISIX is the general ingress, or every AI feature needs RAG |
| Product behavior questions / operational diagnosis / image distribution | Umami / Dozzle / registry, respectively, only for the relevant job | Analytics measures SLOs, logs replace business audit, or registry access belongs in browser code |

These rows route the decision; the detailed references supply exclusions, configuration, and tests. They are not universal performance rankings.

### 3. Check the complete flow against its SLO and failure semantics

Use the architecture skill's [SLO strategy](../archi/references/slo-strategy.md) when present; otherwise explicitly record operation, boundary, target/statistic, window, workload, and success criteria here. Preserve applicable workshop targets: server p99 ≤100 ms; >100 to ≤350 ms requires justification; >350 ms is outside the contract. A different language policy does not waive them.

A cache changes freshness and adds a miss path. A queue adds waiting and requires a separate completion objective. Streaming changes first-output timing, not full completion. A provider call already longer than the full-result deadline cannot be repaired by renaming a service or returning `202` without an accepted product change. Account for resource limits and the shared platform before adding concurrency.

### 4. Use the actual CI and build artifacts

When delivery is in scope, read [delivery guidance](references/delivery-github.md). Detect the actual pipeline and scripts first. This checkout now supplies GitHub Actions calling local lifecycle scripts; a consuming app may still have a different pipeline. Trace build commands → generated files → job artifact transfer when needed → image COPY → runtime entrypoint. A template is not evidence that an app's artifacts were produced or passed between jobs. Do not replace an adequate existing app CI just because the platform has migrated.

Separate hosted pull-request checks from trusted platform-connected operations. A GitHub-hosted runner's `localhost` is not the developer's registry, PostgreSQL, or Podman network. Do not attach an untrusted PR to a privileged self-hosted runner. Document runner access controls and environment setup; do not claim they exist just because YAML names them.

For every selected language/component, declare real lint/type/test/build commands, required integration gates, image identity and publication target, migration ownership, deployment/verification, and rollback. Do not copy Bun commands onto Python/Java/Go. Do not add GHCR, Kubernetes, Helm, Terraform, a second broker, or a monitoring stack unless a concrete requirement justifies it.

### 5. Define operating behavior before declaring readiness

Read [operations](references/operations.md). Specify startup configuration, health/readiness, shutdown, bounded retries/concurrency, logs and metrics, resource budgets, migrations, backups/restores, rotation, retention, and incident recovery for the services actually selected.

Separate **stop**, **runtime purge**, and **business-data deletion**. Verify the actual script's scope; do not use purge as a routine test prerequisite. The supplied development secrets, OpenBao in-memory mode, shared unauthenticated surfaces, and single-host persistence do not constitute a production operating model.

### 6. Deliver proportionately and report evidence

For a full plan, adapt [service-plan.md](assets/service-plan.md) and [operations-runbook.md](assets/operations-runbook.md) in the application's existing documentation location. For a narrow comparison, deliver the equivalent concise decision. When an architecture JSON already exists, keep its selected services and rationales consistent; do not add unsupported fields. Its [validator](../archi/scripts/validate_architecture.py) checks only declared architecture constraints, not service suitability, TTL correctness, durability, GitHub settings, or live SLO compliance.

**DVC-002 — MUST:** label evidence as inspected, proposed, syntax-checked, behavior-tested with doubles, integration-tested, or measured under a stated envelope. Do not infer a live deployment from source files, a configured runner from a workflow, or a successful restore from a backup file. Document unresolved conflicts, actual approvals, and verification still required without blocking unrelated decisions.

### Exceptions: when an alternative is admissible

An alternative is a candidate when a required capability is missing, measured capacity/SLO or isolation cannot be met, an existing compatible service avoids a costly migration, or the deployment model is materially different (for example, an offline embedded tool). Familiarity, popularity, or a synthetic benchmark alone is insufficient. Compare the simpler remedy first and name the operating owner, integration cost, risk, evidence, exit plan and revisit/expiry condition.

A documented alternative within a rule's allowed choices needs no invented waiver. For a `SHOULD`, record the evidence-backed exception as the local policy permits. For an applicable `MUST`, name the exact rule and actual decision authority; prepare the concrete proposal and use the [architecture waiver process](../archi/references/derogations.md) when available. Do not call a proposal approved, create new mandatory approval layers, or repeat authorization already given. Keep independent work moving while a genuinely required decision is unresolved.

Use the contributor handoff route above when implementation or diagnosis needs a focused service skill. A complete platform catalog is not the answer to every small project.
