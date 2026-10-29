# Machine-readable architecture decision contract — v1

This contract describes a decision and the resources it plans to consume. The validator checks its declarative consistency with the platform. It does not generate the application, install anything, execute any application code or call any network service.

## Running the check

From the root of the repository containing the skill:

```sh
python3 -B Skills/archi/scripts/validate_architecture.py architecture.json --as-of 2026-10-14
python3 -B Skills/archi/scripts/validate_architecture.py architecture.json --as-of 2026-10-14 --repo .
python3 -B Skills/archi/scripts/test_validate_architecture.py
```

Adjust the paths if the skill was installed elsewhere. Explicitly provide `--as-of YYYY-MM-DD` with the relevant review date: this makes waiver checks reproducible, regardless of the machine's time zone or clock. If the option is absent, the script announces that it is using the local system date. An explicitly supplied historical date validates a historical state, not whether the waivers are valid today.

| Exit code | Meaning |
|---|---|
| `0` | The declarative checks pass; warnings and declared waivers may remain. A `draft` document remains a draft even with this code. |
| `1` | At least one rule violation or a waiver with invalid dates or scope. |
| `2` | Invalid CLI usage, invalid JSON/schema, inconsistent reference or invalid path with `--repo`. |

The output displays `ERROR`, `WARNING` and `WAIVED`, an identifier and the affected JSON path. `WAIVED` only means that an approval is **declared** in the file. The script does not verify the author's identity or authority. It never presents a result as a design or security certification.

## Structure and types

All fields below are required, even when their value is `null` or an allowed empty list. No unknown fields are accepted, including in nested objects. Duplicate JSON keys, non-standard constants such as `NaN`, booleans used as integers and integers used as booleans are rejected. ID lists cannot contain duplicates.

Notation: `string[]` = list of strings; `path[]` = list of relative paths; `int?` = integer or `null`. Strings are non-empty, except rationale fields explicitly allowed to remain incomplete in `draft`.

| Path | Type / values | Meaning |
|---|---|---|
| `schema_version` | integer `1` | Contract version, not product version. |
| `status` | `draft` or `ready` | Maturity of the described decision, not deployment status. |
| `project` | object | Project identity and policy. |
| `requirements` | object | Need, criteria, constraints and uncertainties. |
| `architecture` | object | Selected structure and comparison of options. |
| `components` | object[] | Application components to create or already existing. |
| `platform` | object | Selected shared services and port convention. |
| `operations` | object | Operational commitment shared by server components. |
| `waivers` | object[] | Already approved and documented waivers; `[]` by default. |

### Project and requirements

| Field | Type / values | Meaning |
|---|---|---|
| `project.name` | string | Project name. |
| `project.kind` | string | Product type in business terms. |
| `project.context` | `workshop`, `production` or `unknown` | Stated context. `unknown` permits a draft without an invented assumption and blocks `ready`. `production` does not trigger automatic certification. |
| `project.policy` | `platform-compatible` or `strict-typescript` | Service compatibility or an explicit language constraint. |
| `requirements.summary` | string | Expected outcome; may be empty in `draft` with a warning. |
| `requirements.drivers` | string[] | Decision criteria, such as skills, latency or volume. Empty: warning. |
| `requirements.constraints` | string[] | Known constraints. `[]` if none have been identified. |
| `requirements.unknowns` | `{question: string, blocking: bool}[]` | Open questions. A blocking question prevents `ready`. |
| `requirements.assumptions` | string[] | Explicit assumptions. `[]` is valid. |

### SLOs and explicit selection reasoning within v1

There is no dedicated `slo` or `performance` object in v1. Do not add one: unknown fields are rejected. Use the existing fields as follows, with the full per-operation contract in the human-readable decision document:

| Information | Existing field |
|---|---|
| Actual response target, required result, measurement boundary, percentile/deadline, window, workload, and failure policy | `requirements.constraints`; include the source and distinguish a client deadline from a statistical objective |
| Priority of latency versus throughput, freshness, cost, or delivery time | `requirements.drivers` |
| Explicit absence of a product SLO, provisional target or workload envelope, and unmeasured feasibility assumptions | `requirements.assumptions`; distinguish an answered absence from an unanswered question |
| Missing requirement that may change sync/async, cache eligibility, or feasibility | `requirements.unknowns`; `blocking: true` when it prevents the affected final choice |
| Why a pattern meets the actual need/SLO, nearest alternative, additional or avoided cost | `architecture.rationale`, `architecture.alternatives`, `architecture.compute_tradeoff` |
| Conditions favoring the selected language/framework, relevant alternative, SLO consequence, evidence and reversal trigger | Component `rationale` and `framework_rationale`; full comparison in the document |

Example constraint string: `search.full-result: server ingress to final response; p99 <= 100 ms over the agreed workshop acceptance run; workload and success criteria in decision.md; source: course contract`. Keep concrete agreed workload details in that document; if they are still assumptions, label them accordingly. A production observation window and a short acceptance test are not interchangeable.

The validator checks these strings for schema/completeness only. It does not parse latency targets, compare stage budgets, select a framework, test load, enforce `SLO-*` rules, or verify whether a result is complete. A passing JSON file is not performance evidence. Record SLO waivers in the human document, not under an unsupported `rule_id` in `waivers`. See [SLO-driven strategy](slo-strategy.md).

### Architecture decision

| Field | Type / values | Meaning |
|---|---|---|
| `architecture.style` | `static`, `modular-monolith`, `worker-pipeline`, `durable-workflow`, `microservices`, `native-client`, `cli` | Selected dominant structure; does not prove that the code implements it. |
| `architecture.rationale` | string | Why this structure meets the need. |
| `architecture.compute_tradeoff` | string | Processes, storage, calls and compute costs it introduces or avoids. |
| `architecture.alternatives` | `{option: string, rejection_reason: string}[]` | Options actually considered and reasons for rejecting them. At least one for `ready`. |

`rationale`, `compute_tradeoff` and `rejection_reason` may be empty in `draft` with a warning. They must be filled in for `ready`. The script does not judge the merits of the arguments.

### Components and responsibilities

Each `components` entry contains exactly the following fields:

| Field | Type / values | Meaning |
|---|---|---|
| `id` | unique string, other than `*` | Stable component reference, also used by waivers. |
| `role` | `frontend`, `api`, `worker`, `cli`, `native`, `upstream` | Component role. |
| `language` | string | Main language; strict policy: `TypeScript`, `JavaScript`, `ts` or `js`, case-insensitive. |
| `framework` | string | Selected framework; use `none` if none is necessary. |
| `runtime` | string | Explicit execution environment, such as Python/Gunicorn, Bun or browser. |
| `source_root` | path | Component directory, relative to the repository root. `.` is allowed. |
| `layers` | object | Four responsibilities required as keys, even if their lists are empty. |
| `layers.transport` | path[] | HTTP routes, controllers, handlers or input adapters. |
| `layers.application` | path[] | Use cases and application coordination. |
| `layers.domain` | path[] | Business rules and concepts, if a dedicated layer is justified. |
| `layers.persistence` | path[] | ORM, repositories, queries and storage adapters. |
| `rationale` | string | Component responsibility and reason for its existence. |
| `framework_rationale` | string | Why this framework, or `none`, suits the need and the team. |
| `data_access` | `none`, `orm`, `query-builder`, `sql` | Primary mode of relational access to the platform; secondary queries/access described in the human-readable dossier. |
| `platform_services` | service ID[] | Platform services consumed directly by this component. |

Rationale fields may be empty in `draft` with a warning. `ready` requires at least one component and completed rationales. `layers.domain` is not imposed artificially: its list may remain empty. For an API, `transport` and `application` are required in `ready`, as is `persistence` if it consumes Postgres. A controller, service and repository may have different names depending on the framework; declare the corresponding actual or planned paths.

All `layers` paths are **relative to the repository**, not to `source_root`. Absolute paths, Windows drives, backslashes, NUL bytes and `..` segments are rejected even without `--repo`. Names use `/` to remain portable.

Without `--repo`, the validator only checks path syntax: a plan for sources yet to be created can pass. With `--repo`, every path must exist, `source_root` must be a directory and all resolved paths must remain within the repository. Internal symbolic links are accepted; links outside the repository, loops and broken links are rejected. The script neither reads nor imports sources; it does not validate that files declared in the layers conceptually belong to those responsibilities.

### Platform and operations

The only v1 service IDs are:

```text
postgres valkey s3 openbao apisix temporal temporal-ui casdoor umami registry dozzle
```

Use these IDs, not the DNS aliases `redis.internal`, `vault.internal`, `llm.internal`, `idp.internal` or `analytics.internal`.

| Field | Type | Meaning |
|---|---|---|
| `platform.services` | service ID[] | Services selected for the application and its operations. This list may include Registry or Dozzle without a direct application consumer. |
| `platform.app_port_base` | int? | Base of the local application block of 10 ports, or `null` if no such allocation is declared. |
| `platform.vector_enabled` | bool | The application plans to use the pgvector extension in its Postgres database. |
| `operations.shutdown_seconds` | non-negative int? | Shared shutdown budget for API/worker/upstream components; `null` if unknown or not applicable. |
| `operations.health_endpoints` | bool | The architecture plans `/health` and `/ready` for the relevant server components. This is not a test result. |

Each `component.platform_services` must be a subset of `platform.services`. The validator does not add any service by default. A static frontend may therefore declare `platform_services: []`.

The v1 contract represents only a canonical port allocation: frontend `+0`, API `+1`, worker health `+8`. When `app_port_base` is not null, multiple components with the same canonical role cause a declarative collision. `null` means **no verifiable allocation**, never proof that there is no conflict. Custom port mappings, upstream ports and multiple allocations require an explicit contract extension and review, rather than silently added fields.

## Checked rules

| Stable ID | Check | JSON waiver |
|---|---|---|
| `PLAT-001` | `frontend` and `native` do not directly consume `postgres`, `valkey`, `openbao`, `apisix`, `temporal` or `umami`. Casdoor and S3 are declaratively allowed; permissions, keys and public paths still need to be designed. | No |
| `PLAT-002` | Null base or a multiple of 10 between 8000 and 8990, except 8200 reserved for OpenBao; no collision between declared canonical offsets. | No |
| `DATA-001` | `vector_enabled: true` requires `postgres` in `platform.services`. | No |
| `DATA-002` | `data_access` other than `none` requires `postgres` in the **component's** services. Another database requires an explicit contract change, not a false alias or JSON waiver. | No |
| `ARCH-001` | API: `transport` and `application` paths; also `persistence` if Postgres is consumed. Missing: warning in `draft`, violation in `ready`. | Yes, component |
| `STACK-001` | In `strict-typescript`, the `frontend`, `api` and `worker` roles use TypeScript/JavaScript. `platform-compatible` accepts Django/Python, Rust or another justified choice, among others. | Yes, component |
| `OPS-001` | API/worker/upstream: declared shutdown strictly below 10 seconds and health endpoints. Incomplete or non-compliant: warning in `draft`, violation in `ready`. | Yes, component or `*` |
| `READY-001` | `ready` with a known context, no blocking question, a summary, rationales, at least one alternative and at least one component. Non-blocking questions and missing criteria produce warnings. `draft` flags its incomplete decisions, including an `unknown` context. | No |

`SCHEMA`, `PATH` and `WAIVER` are diagnostic categories, not rules that can be waived. A nonexistent service or scope reference is a schema error. Non-waivable rules remain errors even in `draft`; a draft does not make private client consumption or an inconsistent declaration acceptable.

The `frontend` role means code running in the browser, even if nginx serves its assets. For example, compliant Umami measurement goes through a backend relay; it must not be declared as direct frontend consumption. `native` is also an unprivileged client. A CLI application is not automatically treated as a browser; its actual permissions must be reviewed in context.

An SSR/BFF server accessing private services is described as a backend component (`api`) separate from the browser part (`frontend`), even if they are built from the same repository. The JSON describes the trust boundary; the dossier specifies whether these components share a process and how their ports are served. If additional roles or ports need to be represented beyond what v1 can describe, document that limitation instead of obtaining a false passing result with an unsuitable role.

`data_access` describes relational access **to the platform**: primary ORM use with a targeted SQL query is declared as `orm`, with the query and its transaction documented in the dossier. An offline client's local storage (e.g. SQLite) is not SDI PostgreSQL consumption: describe it in the dossier with its synchronization and permissions; `data_access: none` means no relational access to the platform here, not the absence of any local persistence. A server engine replacing Postgres remains outside the v1 contract and requires an explicit change, not this shortcut.

## Documented waivers

A `waivers` entry requires exactly:

| Field | Type | Meaning |
|---|---|---|
| `id` | unique string | Waiver decision identifier. |
| `rule_id` | rule ID | Only `ARCH-001`, `STACK-001` or `OPS-001` can actually be waived. |
| `scope` | component ID or `*` | An existing component; `*` is reserved for `OPS-001`. |
| `reason` | non-empty string | Constraint justifying the exception. |
| `alternatives` | non-empty string[] | Solutions investigated to avoid the exception. |
| `compute_impact` | non-empty string | Impact on processes, resources and compute costs. |
| `evidence` | non-empty string[] | References allowing the reviewer to verify the need and approval. The script does not open them. |
| `approved_by` | non-empty string | Person who actually authorized the waiver, according to project rules. |
| `approved_on` | `YYYY-MM-DD` date | Date when authorization was obtained. |
| `expires_on` | `YYYY-MM-DD` date | Last valid day, inclusive. |
| `rollback` | non-empty string | Planned return to the rule or replacement of the temporary solution. |

`approved_on <= --as-of <= expires_on` is required. A future approval, expiration before approval or expired waiver causes an error, **even in draft and even if no violation uses it**. Two waivers with the same rule and scope are rejected. A valid waiver without a corresponding violation produces a warning. A waiver scoped to component A does not cover component B.

Never invent an approver, authorization date or evidence to pass the check. An architecture request or technical preference is not, by itself, approval of a waiver. Without actual authorization, keep `waivers: []`, leave the violation visible and prepare the decision for the appropriate person. The validator contacts no one and grants no approval.

## Example and limits of evidence

[`architecture.example.json`](../assets/architecture.example.json) describes a Django/Postgres portal in a workshop context with a React frontend. It uses `platform-compatible`, so Python requires no waiver. The frontend calls the API; the API consumes data, secrets, OIDC and files. No analytics, worker or AI call is added without a need.

The example is an **illustrative plan**, with no application sources provided. It passes without `--repo`. A check with `--repo` must fail until its paths exist; create the actual paths or adjust the declaration after implementation. Do not create empty directories solely to obtain a passing result.

The check does not prove:

- Actual separation of controllers/use cases/domain/persistence, import direction or absence of business logic in routes. The reviewer must read the code and examine its tests.
- Framework suitability, fit of the architectural style to volumes, consistency of the business model, actual cost or quality of alternatives; response-time SLO coverage, feasibility or measured compliance.
- Platform availability, network state, installed versions, port collisions on the host or between multiple applications.
- Actual existence of databases, users, buckets, namespaces, analytics sites, OIDC clients or the pgvector extension; nothing is provisioned.
- Observed shutdown time, quality of `/health` and `/ready`, adherence to retry policies, authentication, data confidentiality or production robustness.
- Actual consumption of declared services, absence of a direct provider call, presence of secrets in the code or validity of approval evidence.

The `context: production` field neither relaxes nor completes the rules: security, persistence, backups, observability, operations and capacity must undergo an appropriate review. Non-empty strings do not, by themselves, constitute a convincing justification. Supplement machine validation with human review and checks proportionate to the change.
