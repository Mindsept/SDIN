---
name: archi
description: "Define and decide the architecture of an application consuming the SDI platform: explicit language/framework/pattern selection, response-time SLOs, clarifications, code separation, ORM, services, and waivers. Use before creating or redesigning an application, or reviewing technical choices; a simple fix does not trigger deployment or a rewrite."
---

# SDI application architecture

Produce a reasoned, actionable, and verifiable decision for **the consuming application**. This skill standardizes choices and their evidence; it does not configure the agent's global behavior, change the requested product, or authorize any deployment.

## Sources of authority

1. Respect the user's needs, explicit choices, and existing authorizations. Do not ask again for a choice already provided.
2. Inspect project instructions, existing code, and the platform actually available. Preserve viable existing decisions; a new catalog is not a mandate to rewrite.
3. Distinguish **repository fact**, **policy proposed by this skill**, **project-specific decision**, **assumption**, and **observed measurement**. A recommendation is not an instructor requirement.
4. A written waiver cannot make a physical or API requirement of the platform achievable. An architecture outside the contract requires an explicit platform adaptation and renewed verification.

The platform is described in `td/core-platform/`. Locate this directory from the Git root or use the location provided by the user; do not assume the current directory or a personal path. From this skill in this repository, the root is `../..`. If the skill is copied elsewhere, ask for or locate that root, then use the references as a documented snapshot, **not as evidence of a running deployment**.

## Usage modes

- **Design**: start from the need, compare options, and produce the decision document and remaining questions.
- **Existing application / redesign**: map current responsibilities and costs, propose an incremental migration, and retain what meets the requirements.
- **Review**: check a document or code against the same criteria; distinguish declarations, evidence, and unverified items.
- **Focused choice**: answer a specific comparison, such as Django versus FastAPI; do not require a full architecture document for this question alone.

A request to compare a stack and its high-level architecture can remain a focused choice when the user asks for concise guidance. Apply the relevant conditions and SLO reasoning, but do not generate JSON or a full dossier unless that deliverable is requested or clearly part of the task. Unresolved security/data questions keep the affected design provisional; they do not automatically block an independently justified framework recommendation.

## Reference routing

Inspect the brief, prior answers, repository instructions, and existing implementation before selecting a route. Load only the relevant sections, then follow another reference only when its condition applies. Revisit this table when constraints, evidence, or scope change.

For a **complete design**, read in stages: scoping and SLOs → architecture and stack → code/data boundaries and platform integration → quality, applicable waivers, and deliverables. For a **focused question**, take the matching route and stop once the choice and its decision-changing uncertainties are explained; do not require a full dossier.

| Situation / trigger | Read first | Conditional follow-up | Expected decision |
|---|---|---|---|
| Brief is incomplete or a requirement could change the choice | [cadrage.md](references/cadrage.md): Method, First round, relevant Conditional branches | Use the matching route below once the missing constraint is known. | Questions that matter, known answers, and explicit assumptions or blockers. |
| Response-time target, deadline, streaming, or sync versus jobs | [slo-strategy.md](references/slo-strategy.md): §§1–4 | Read architectures §5 for asynchronous processing; quality §4 when planning measurements. | Measurement boundary, feasible request strategy, and evidence still needed. |
| Static app, rendering, monolith, services, workflows, offline, or migration | [architectures.md](references/architectures.md): §1 and the relevant pattern section | Read SLO strategy if the critical path changes; code structures for the selected internal boundaries. | Simplest suitable pattern, rejected alternative, and reconsideration condition. |
| Language, runtime, or framework comparison | [langages-frameworks.md](references/langages-frameworks.md): §3 and the relevant ecosystem section | Read stack sources for current capabilities; data/ORM if persistence affects the choice; platform §5 for a non-canonical stack. | Chosen stack, nearest alternative, conditions met, and SLO/compute consequences. |
| Controllers/services, dependency direction, or directory layout | [structures-code.md](references/structures-code.md): §§1–2 and the relevant §4 or §5 example | Read data/ORM for transaction or persistence ownership. | Concrete responsibilities, dependency direction, and a request path. |
| ORM/SQL, migrations, transactions, queries, isolation, or RAG | [donnees-orm.md](references/donnees-orm.md): the matching topic section | Read platform for storage contracts; SLO strategy if query or pool budgets threaten the target. | Data access approach, ownership, consistency guarantees, and checks. |
| Service integration, network/identity boundaries, secrets, ports, or onboarding | [plateforme.md](references/plateforme.md): §§1–4 and the relevant service constraints | Use DevOps for service comparisons or delivery mechanics; waivers only for an actual deviation. | Required services and consumer boundaries, plus provisioning prerequisites. |
| PostgreSQL versus Valkey, Streams versus Temporal, GitHub Actions, delivery, or runtime controls | [DevOps skill](../devops_and_choice/SKILL.md): its matching reference route | Return to architecture/SLO sections only if the service or delivery choice changes application boundaries or feasibility. | Justified service or delivery choice and applicable controls. |
| Security, API contracts, tests, performance evidence, recovery, or costs | [qualite-exploitation.md](references/qualite-exploitation.md): the matching risk section | Read SLO strategy to define a missing target; DevOps for CI or operational implementation. | Proportionate checks, evidence gaps, and operational requirements. |
| A proposed choice deviates from an applicable rule | [derogations.md](references/derogations.md): §§1–3 | Read policy sources if the rule's authority is unclear; machine contract when recording a waiver in JSON. | Whether a waiver is needed and its evidence, owner, approval status, and expiry. |
| Decide the response format or assemble the final design | [livrables.md](references/livrables.md): §§1–3 | Read machine contract only when producing or checking the JSON deliverable. | Output proportional to the request and an honest decision status. |
| Create/check architecture JSON or interpret validator results | [contrat-machine.md](references/contrat-machine.md): Structure and types, Checked rules | Read waivers for a declared exception; deliverables if output scope is unresolved. | Valid declarations and clearly stated limits of validation. |
| Verify versions, support, SDKs, or framework capabilities | [sources-stacks.md](references/sources-stacks.md): relevant ecosystem | Consult the linked official documentation; revisit the stack choice if the evidence changes it. | Current supporting evidence or explicitly deferred verification. |
| Resolve the origin, scope, or maintenance of a cross-cutting policy | [sources-doctrine.md](references/sources-doctrine.md): Priority local sources, Updates | Inspect the cited repository source; use waivers only after establishing the applicable rule. | Separate repository fact, proposed policy, and project decision. |

When consulting DevOps, pass the established facts, selected profile, SLOs, and unresolved question. Use its relevant references without restarting clarification or repeatedly handing the same decision back between skills.

Recommendations are proposed project rules, dated and subject to revision; source references support decisions, not evidence of a running deployment.

## Decision process

### 1. Clarify the need before choosing

Read [the adaptive questionnaire](references/cadrage.md). First extract answers from the repository and brief. Ask **one to three questions at a time**, only those that could change the decision. Explain each question's impact, offer an understandable answer option, and accept "I don't know."

At a minimum, check the business flow, data and its sensitivity, existing system and team, workshop or production context, imposed constraints, and **whether a response-time SLO or maximum acceptable request duration exists**. Ask this even for a small application, unless the brief already answers it. Clarify whether the deadline concerns the complete result, acknowledgment, or first streamed output; never silently substitute one for another. Detailed load, AI, real-time, offline, workflow, ORM, and availability questions depend on the answer. A noncritical unknown can become an explicit assumption; an unknown that changes the trust boundary, latency feasibility, or course requirements keeps the affected decision in draft. Continue independent work while awaiting answers.

### 2. Establish the technology selection policy

Name one of two profiles in the document:

| Profile | Scope |
|---|---|
| `strict-typescript` | Follow the course's TS/Bun default and Vite frontend. Another language in a frontend, API, or worker requires an approved waiver. The presentation mentions Rust for a measured hot spot. Other cases must still be submitted to the course authority, without inventing its approval. |
| `platform-compatible` | The broader policy proposed here: choose a language justified by the need and team, while preserving SDI contracts. Python, Java, and Go are not exceptions by nature. Adapting builds, tests, images, and SDKs is mandatory. |

The repository specifies TS/Bun by default. [Elyes/CCOE-RULES.md](../../Elyes/CCOE-RULES.md) supplies local contributor rules for service selection, PostgreSQL, S3, Valkey, and cross-service consistency; apply them within their stated scope. Their presence does not establish a complete instructor-approved language policy or permission to use the broader profile. **Do not infer the instructor's approval of that profile from either skill or contributor policy alone.** If the policy has not been specified, ask; provisionally analyze under the strict profile and present alternatives. An explicit answer or instruction already given is sufficient: do not add a second permission round.

### 3. Turn response-time requirements into a strategy

Read [SLO-driven strategy](references/slo-strategy.md) before selecting a request architecture. For each critical operation, record the measurement boundary, required result, percentile or hard deadline, target, observation window, load/payload envelope, and treatment of failures. If the user says "maximum 200 ms," clarify whether this means a statistical target or a hard deadline; do not silently call it p99. If no product SLO exists, say so, preserve applicable course targets, and label any proposed target as an assumption.

Apply the reference's decision rules: keep synchronous execution when the complete path plausibly fits; optimize the measured bottleneck; use cache/precomputation only when freshness and permissions allow it; use jobs only when delayed completion is acceptable, with separate acceptance and completion targets; use Temporal when durable orchestration is needed. A fast `202` or first token does not satisfy a full-result SLO. If a mandatory dependency cannot fit and no valid fallback or semantic change is allowed, report the incompatibility instead of promising that another language or microservices will solve it.

### 4. Choose the simplest architecture that meets the need

Read [architectures and patterns](references/architectures.md). First decide whether a server, persistence, jobs, or a workflow is needed. The template offers three components; it does not require all of them. A single-player game can remain static; a CRUD application can remain a modular monolith; a task queue alone does not justify microservices.

For the selected option, explicitly apply the pattern decision rules: **choose X because these conditions hold in this project; reject Y because this condition does not hold; reconsider if this evidence changes**. State how the pattern affects the critical request path and SLO. Separate deployment topology, internal code organization, and execution mode; a modular monolith can use vertical slices, ports/adapters, and a worker. Document operating cost and **compute avoided or additional cost accepted**. Compute includes CPU, memory, I/O, network, storage, builds, and billed calls; do not turn intuition into quantified savings.

### 5. Choose the language, framework, and data access approach

Read the relevant sections of [languages and frameworks](references/langages-frameworks.md), then [data and ORM](references/donnees-orm.md). Default to one primary stack; use multiple languages only with a useful boundary and explicit integration cost.

Compare functional fit, essential libraries, expertise, existing systems, maintenance, concurrency model, **measured** performance, and platform compatibility. Distinguish language, runtime, framework, ORM, and build tool. Do not conclude that "Go is always optimal," "Python is slow and therefore forbidden," "async makes computation parallel," or "ORM is mandatory everywhere."

For **each actual language and framework choice**, apply the relevant head-to-head rules from the reference to the user's facts. Write: chosen option, conditions met, nearest viable alternative, why it loses here, SLO/compute consequence, evidence still needed, and a condition that would reverse the choice. "Django for CRUD," "FastAPI is fast," or an unranked catalog is insufficient. A latency threshold alone never selects a language or framework; assess the end-to-end bottleneck and validate the selected stack under the declared workload.

Consult official documentation for support, versions, SDKs, or capabilities that may have changed. The [stack sources](references/sources-stacks.md) are a starting point, not a guarantee of future compatibility. Without network access, identify deferred checks instead of inventing their results.

### 6. Define boundaries and code structure

Read [code structures](references/structures-code.md). Separate the responsibilities that exist: transport/controllers, application services, business rules, and persistence/integration adapters. Controllers contain neither SQL queries nor business orchestration. The detailed rules allow idiomatic Django, Rails, Go, or Nest mappings; they do not require classes, interfaces, and empty directories everywhere.

Provide a concrete directory tree suited to the chosen framework, the direction of dependencies, and an example request path. Specify where DTOs, validation, authorization, transactions, errors, migrations, and tests belong. Frontends and workers have their own responsibilities, without mechanically copying an HTTP architecture.

### 7. Connect only the services that are useful

Read [platform contracts](references/plateforme.md) and use [service selection and DevOps choices](../devops_and_choice/SKILL.md) for explicit comparisons such as PostgreSQL versus Valkey and Streams versus Temporal. Associate each service with a need; mark others "not applicable" with a reason. Separate browser, API, worker, script, and operator flows. Do not consume OpenBao or PostgreSQL from the frontend, treat S3 as an external endpoint, use APISIX for LLM access, and use the application's API to proxy Umami.

Plan provisioning without executing it merely because of this analysis. The supplied bootstrap creates a database and bucket by default: adapt it before using it for an application that does not need them. `onboard-app.sh` enables LLM + Temporal; it is not a universal minimal onboarding procedure.

### 8. Check quality attributes and deviations

Read [quality and operations](references/qualite-exploitation.md), apply the [DevOps skill](../devops_and_choice/SKILL.md) for GitHub Actions, delivery, and runtime controls, then read [waivers](references/derogations.md) if a deviation exists. Distinguish isolated pull-request checks from explicitly triggered operations on the trusted workshop runner; an architecture review does not trigger either deployment or purge. Keep the review proportional to actual risks: business authorization, data, API contracts, asynchronous processing, capacity, performance, tests, and operations. Copying the workshop Compose setup does not make an application production-ready.

For a waiver, specify the rule, scope, evidence, alternatives, owner, actual approval, expiry, and exit plan. Do not self-approve or accept an expired waiver. Do not block an alternative allowed by the chosen profile merely because it differs from the template.

### 9. Deliver and validate

Follow [the deliverables guide](references/livrables.md). For a complete design, provide an architecture decision with applied language/framework/pattern comparisons, a per-operation SLO contract and its strategy, JSON contract, directory tree, validation scenarios, and any waivers. For a focused choice, limit the result to that choice and the requirements that can change it. State separately whether a design is justified and whether its SLO has actually been measured; `ready` is not a performance result.

The [machine-readable contract](references/contrat-machine.md) specifies fields, limitations, and exit codes. **Fictional** example to adapt: [architecture.example.json](assets/architecture.example.json).

```bash
python3 /path/to/skills/archi/scripts/validate_architecture.py \
  /path/to/app/docs/architecture/architecture.json --as-of YYYY-MM-DD
```

Replace the date with the review date in the user's context. Add `--repo /path/to/app` **after** creating the declared paths. Do not create empty directories to obtain a passing check. A valid result certifies only the script's declarative constraints, not actual code separation, SDK compatibility, a decision-maker's approval, or production readiness.
