# Choosing languages, runtimes and frameworks

Read this reference after identifying the product, constraints and team. The choices below form a **proposed policy for this harness**, conditional and revisable, not a performance ranking provided by vendors. Technical capabilities are supported by [sources-stacks.md](sources-stacks.md), consulted on **October 14, 2026**. Supported versions, SDKs and limitations must be checked again when making the choice.

## Reading guide

- Method, questions and explicit language comparisons: sections 1–3.
- Product types: matrix in section 4.
- Frontend/TypeScript, Python, JVM, Go, .NET, Rust: sections 5–10.
- PHP, Ruby, Elixir, Scala/R, native/mobile: sections 11–15.
- Cross-cutting cases, platform integration and justification: sections 16–18.

## 1. Separate the decisions

A **language** describes the code; a **runtime** executes it; a **framework** organizes an application; a **build tool** transforms sources; a **protocol** connects systems. TypeScript + Bun + Hono and TypeScript + Node.js + Fastify are therefore two possible stacks. React is a UI library; Vite is development/build tooling; Next.js is a React application framework. Python + FastAPI also requires an ASGI server suitable for deployment. Choosing Java requires neither Spring nor Kubernetes.

**Proposed rule L01 — specify these levels separately in the ADR.** This makes compatibility, packaging and update ownership explicit; it avoids adding builds, runtimes and services for functions already covered. A library alone does not authorize a deployment topology.

In this repository, `td/core-platform/templates/podman-compose.yml` proposes a TS/Vite frontend and TS/Bun API/worker services. The pipeline ties its checks to this tooling and illustrates Rust under a critical-path waiver. The README states that the CCoE rules remain to be written. **The harness compatibility default is therefore TypeScript/Bun; this does not prove that Python, Java or Go are inherently incompatible.** The chosen policy may allow several profiles with justification. If an actually applicable CCoE rule restricts the stack, follow its waiver process. A template example alone does not establish a permanent ban on all other languages.

## 2. Questions that actually change the choice

Do not turn this list into a systematic questionnaire. Inspect the existing system, retain known answers, ask one to three clarifying questions at a time about unknowns that distinguish the options, then continue if necessary.

| Information to obtain | Concrete question | Impact on the choice |
|---|---|---|
| Product and users | “Is this an indexable public website, an internal application, a third-party API, a processing task or a mobile app?” | Static/SPA/SSR, backend, worker or native |
| Critical journey | “Which journey must work in the demo and then in operation?” | Avoids sizing for imagined features |
| Existing system | “Which services and libraries must be retained?” | Extending a familiar stack may outweigh migration |
| Skills and duration | “Which stacks does the team know, and who will maintain the system after delivery?” | Development, support and training costs |
| Load | “How many simultaneous requests/users, what file sizes, what job durations? Measured or estimated?” | Processes, buffers, throughput, concurrency, memory |
| Nature of the work | “Are we mostly waiting for the DB/network, or actually computing on CPU/GPU?” | Async I/O, CPU workers, scientific libraries |
| Request SLO | “Is there an SLO or maximum response time? For which journey, measured from where, at which percentile or as a hard deadline, under what load?” | Latency budget, feasible synchronous work, capacity test; use [slo-strategy.md](slo-strategy.md) |
| Completion and reliability | “Does that delay mean acknowledgement, first useful result or completed work? What acceptable losses and recovery after failure?” | Separate completion target, durable queue, timeout, 202/polling, workflow engine |
| Data | “Relational data, files, sensitive data, offline work?” | ORM, storage, synchronization, server/client separation |
| Ecosystem | “Is a business SDK, ML model or native library essential?” | Eliminates stacks unable to fulfill this contract |
| Interface | “Do we need search indexing, social sharing, a personalized first page, accessibility, native mobile?” | SSR/SSG, browser cost, native platform |
| Operations | “Machine/CI budget, CPU architecture, OS, air gap, support and release frequency?” | AOT/JVM, Python wheels, native dependencies, offline |
| Imposed constraints | “Is a language an educational objective or a contractual obligation?” | Optimize within that constraint; do not dismiss it |

**Proposed rule L02 — do not infer load or an SEO requirement from the word “scalable”, “SaaS” or “AI” alone.** When these are absent, declare a reversible assumption and a review trigger; this avoids clusters, SSR and continuously running services without demonstrated value.

## 3. Tradeoffs and the meaning of optimal

1. Eliminate options that fail a mandatory contract: hardware, SDK, support, security, deadline, target platform. Do not hide this elimination behind an average score.
2. Prefer a maintainable existing system when retaining it meets the need. Personal preference does not justify a rewrite.
3. Normally compare 2–3 credible candidates for the component concerned: delivery time/skills, integration, operations, library quality, resources and longevity. Add a candidate if it clarifies a real tradeoff.
4. Separate **measured**, **estimated**, **unknown**. Do not quantify a difference in CPU, RAM, throughput, cost or energy without a representative experiment.
5. Measure the journey that could overturn the decision: real requests, DB and LLM access, payload sizes, concurrency, startup time, idle/loaded memory, errors, build cost. Record the machine, versions, dataset and protocol. A “hello world” benchmark does not represent the product.

**Proposed rule L03 — compare total cost, not just requests per second.** Include idle runtime, requests, DB, network, storage, LLM calls, jobs, browser computation, builds/CI and operational effort. An integrated framework may cost more at idle but avoid services and code; an AOT binary may shift cost to compilation; a cache may save CPU but consume memory and require invalidation.

**Proposed rule L04 — one primary server-side language per application is the default, with justified specialized extraction.** Reusing contracts and libraries reduces CI and images. A Python worker for an existing model or a Rust module for a profiled loop is admissible: document that benefit, serialization cost, maintenance and the boundary. Do not create a microservice per language or per layer.

### 3.1 Mandatory selection procedure: make a decision, not a catalog

For each component whose stack is being selected, apply these steps **in order**. A broad project label is not a sufficient predicate.

1. **Apply the policy gate.** Under `strict-typescript`, propose the compatible TS/Bun stack first; another language is an explicitly scoped waiver candidate. Under `platform-compatible`, compare other languages without inventing a waiver. Both retain applicable SDI contracts and SLOs.
2. **Apply hard exclusions.** Name the required library, target, runtime support or organizational constraint. Mark each credible candidate `passes`, `fails` or `unknown`; an unknown is a question or a bounded technical check, never an assumed pass.
3. **Use the comparisons below for the actual workload.** Select the relevant rows and state which side's conditions hold. Do not paste all language families into the user's decision.
4. **Choose the framework within that language** using sections 5–15; name the framework capabilities the application will actually consume and the features it will have to assemble.
5. **Apply the SLO path.** Identify the constrained journey, load and bottleneck hypothesis, then the budget and experiment from [slo-strategy.md](slo-strategy.md). A candidate is provisional until evidence supports its performance; a framework name is not evidence.
6. **Resolve ties explicitly:** retain a healthy existing stack; otherwise prefer demonstrated team competence, required-feature coverage and fewer maintained moving parts, in that order unless the user has stated a different priority. If still tied and compatible, use the repository default. Name the fact or measurement that would reverse the choice.

Every substantive recommendation must include: **“Choose X because [project fact]; reject/defer Y because [project fact]; verify [uncertain capability or SLO]; reconsider if [observable condition].”** For a narrow question, one short comparison is enough. Never leave the user with only “both are suitable”.

### 3.2 Language versus language: conditional decisions

These are policy branches, not benchmark conclusions. “Prefer” applies only after the policy and compatibility gates; if both conditions hold, use the tie-breaker in the last column.

| Comparison | Prefer the first option when… | Prefer the second option when… | Reject/defer the change; evidence and tie-breaker |
|---|---|---|---|
| **TypeScript vs Python** | The component is a web API/BFF/remote-LLM adapter; TS is maintained by the team and its libraries cover the work | A named Python model/parser/scientific library is essential, or Django's admin/forms/ORM address substantial product requirements | “AI” alone does not justify Python. Inventory missing capabilities; compare the cost of one Python component with maintaining two stacks. If no Python-specific value exists, retain TS |
| **Python vs Java/Kotlin** | Python libraries or Django capabilities dominate, and the team can operate the workload within its targets | Existing JVM domain/integration libraries, Spring expertise and shared operational tooling cover the business requirements better | Transactional data does not exclude Python. Inspect actual integrations and the critical query/CPU path; choose existing expertise when neither has a unique capability |
| **Python vs C#/.NET** | Scientific/model code or Python administration is the main reusable asset | Required .NET libraries, a maintained C# domain, or ASP.NET/EF tooling and team experience materially reduce delivery/maintenance work | Neither Linux deployment nor a strict SLO excludes either by itself. Verify native dependencies, image and representative journey before a performance-based decision |
| **TypeScript vs Java/Kotlin or C#** | A web-oriented team can express the rules cleanly in TS and the SDI template removes integration work | The JVM/.NET ecosystem provides required domain libraries or conventions and maintainers that TS would replace or rebuild | “Many rules” does not automatically require Java/C#. Compare one representative use case, transaction and authorization rule; team/library advantage breaks the tie |
| **TypeScript vs Go** | Web ecosystem reuse, shared team skills and existing integration outweigh a separate compiled service | A collector/CLI/streaming service has a concrete packaging or operations need, a capable Go team and compatible clients | High concurrency alone is insufficient. Profile waits, event-loop blocking, DB limits and process costs; compare bounded implementations under the same payloads and load |
| **Python vs Go** | Work is primarily library-driven data/ML processing, or Python business features avoid substantial rebuilding | The component is an independently useful collector/agent/CLI with Go expertise and no essential Python dependency | Do not translate Python glue around an already-native kernel merely to change language. Isolate the measured CPU segment first; account for data copies and worker startup |
| **Java/Kotlin vs C#** | Existing JVM assets, libraries, tooling and maintainers are stronger | Existing .NET assets, libraries, tooling and maintainers are stronger | General CRUD, transactions and APIs do not settle this contest. Check required integrations and final deployment; avoid a second runtime when both meet constraints |
| **Java vs Kotlin on the JVM** | Java is the team's maintained language or important tooling/code generation favors it | Kotlin is already maintained and its language/tooling fit the domain without interoperability friction | Do not infer backend choice from an Android client. Prototype the required Java-library boundary and build/static checks; retain the existing language on a tie |
| **Go vs Rust** | The component is ordinary service/CLI code with Go expertise and no established need for Rust-specific control | Required low-level integration, memory/control constraints or a profiled segment justify Rust, and maintainers can own it | “Rust is faster” cannot authorize a rewrite. Measure the same operation, allocation/memory and integration boundary; use the simpler maintained solution if both meet the target |
| **Python with native libraries vs Rust/Go/C++ extraction** | Existing vectorized/native kernels already dominate computation and meet the budget | A profile isolates costly custom processing for which a replacement library or small module demonstrates enough benefit | First test algorithm, batching, copies and kernel configuration. Reject extraction when serialization/FFI, model duplication or maintenance consumes the gain |
| **TS/Go/JVM/.NET vs Elixir** | Existing concurrency tools and maintainers cover the connection/event model | Supervision, messaging and Phoenix capabilities simplify a demonstrated collaboration workload and Elixir expertise exists | Connection count alone is not proof. Test connection memory, reconnect storms, fan-out, backpressure and recovery; do not confuse supervision with business durability |
| **TS/Python/JVM/.NET vs PHP/Ruby** | The team, integration libraries or platform default favor the first group | A maintained Laravel/Symfony/Rails system or integrated forms/business tooling avoids a costly rewrite or framework assembly | Reject a language switch based only on fashion or age. Compare required screens, admin, jobs, deployment support and ownership; retain a healthy existing product |

For R, Scala, mobile and embedded languages, sections 14–15 supply the specialized branch. A native client and its backend are **separate decisions**; sharing a language is a benefit to assess, not an obligation.

### 3.3 How an SLO changes a stack decision

An SLO narrows feasible implementations **through the execution path**, not through a rule such as “below 100 ms means Go”. Compare candidates with identical authorization, data, payload, dependencies, concurrency and resource limits. Do not compare an empty router with a fully validated transactional API.

| Observed or provisional situation | Explicit stack decision | Required evidence / reversal trigger |
|---|---|---|
| Most latency is SQL or external I/O | Retain the language provisionally; fix query shape, indexes, connection/pool waits and dependency deadlines first. Select async/non-blocking handling only when the actual libraries and concurrency need justify it | Trace the complete journey and test peak load. Reconsider language/framework only if a remaining runtime cost consumes the budget |
| Event loop / worker pool saturates while other resources have headroom | Check blocking calls and bounded concurrency before switching. Compare a compatible async path, worker isolation or another runtime as distinct options | Measure pool queueing/event-loop delay and cancellation; keep the option that meets latency/error targets within the resource budget |
| Custom CPU code dominates and misses the target | Keep business/API code; compare algorithm/native-library optimization with a bounded worker or targeted Go/Rust/JVM/.NET implementation appropriate to the team | Profile and benchmark the segment **and** end-to-end route, including queue/serialization overhead. If all latency, capacity and resource targets are met, reject a rewrite justified only by a faster microbenchmark |
| Cold initialization is part of the required response | Compare warm/preloaded service, reduced initialization and a compatible AOT/native option | Measure final artifact startup through readiness, secrets/DB/model loading and first request. Faster process startup alone is insufficient |
| Required computation/dependency cannot finish within the budget | No language choice makes the synchronous contract feasible by declaration. Apply the product-approved asynchronous, precomputed or degraded-result strategy in [slo-strategy.md](slo-strategy.md) | Separate acknowledgement, first result and completion SLOs; otherwise state the constraint conflict. Do not label a quick `202` a completed-result success |

### 3.4 Worked applications of the rules

These are **illustrative decisions, not measured results**. Assume `platform-compatible` unless stated otherwise. Their purpose is to show how facts select a branch; adapt them to the user's answers and keep any applicable workshop gate.

| Stated project facts | Concrete decision and rejected option | SLO effect and what could reverse the choice |
|---|---|---|
| Internal inventory portal; Python team; relational data; trusted operators need model administration; a mobile app needs the same domain | **Python + Django + DRF**, modular business services and one persistence model. Reject FastAPI as the primary framework because rebuilding administration/forms is the dominant additional cost | Define list/update SLOs separately from exports; test permissions and query shape. Reconsider if admin is actually a fully bespoke workflow with little reusable Django value |
| API around a required Python classifier; no admin; external clients; inference is variable and users accept delayed completion | **Python + FastAPI** for the typed API and a bounded model worker for computation. Reject Django because its integrated business features are unused; do not run heavy inference on the API event loop | An acknowledgement SLO and a completion SLO are both required. If users require a synchronous final result, evaluate model/compute feasibility instead of assuming FastAPI will make it fit |
| TS team; authenticated app asks a remote LLM via APISIX; no Python-specific libraries; `strict-typescript` | **TS/Bun + Fastify** for a schema-based API, subject to client/runtime verification. Reject Python as an unneeded second stack; reject Nest unless its module/convention benefits are named | Provider latency drives the path: separate first-token and completed-answer targets if streaming is useful. A Python requirement or failed runtime compatibility check reopens only the affected component |
| Maintained Java/Spring application; JPA transactions; latency target becomes stricter; traces show repeated queries | **Keep Java + Spring MVC**, fix the query path and measure again. Reject immediate WebFlux/Go migration because neither addresses repeated DB work by itself | Validate at the agreed percentile/load with pool limits. Reopen concurrency/runtime choice only if remaining measured saturation prevents the budget after data-path fixes |
| New operational CLI must run without an installed interpreter; team knows Go; no native-library dependency; small HTTP collector is also needed | **Go**, CLI entry point plus `net/http` or chi only where routing needs it. Reject Rust because no additional low-level constraint or maintained Rust asset offsets its adoption cost | Verify target artifact, certificates, timeouts, bounded ingestion and required completion/HTTP targets. A required incompatible library or proven low-level constraint can change the choice |

## 4. Project-family matrix

These choices are starting points under the stated conditions. “Avoid” means a poor default for the context, not technical impossibility. Any profile other than the template adapts the gates and packaging; a waiver is required only when an applicable rule is actually violated.

| Family / dominant need | Initial candidate and conditions | Alternatives that may win | Poor default and cost avoided/accepted |
|---|---|---|---|
| Brochure website, documentation, stable catalog | HTML/CSS or Astro with static generation | Vite for a few interactions; an already-used framework | Permanent SSR without request-dependent content: unnecessary computation and processes |
| Authenticated internal portal, CRUD dashboard | TS + Vite + familiar UI library; compatible TS/Bun API | Django if administration is central; Laravel/Rails/.NET if the team is equipped | Next SSR by habit; duplicate API/BFF without a role: runtime and round trips |
| Rich back office, relational data, operators | Python Django; DRF for separate API clients | Laravel, Rails, Spring Boot, .NET depending on the team | FastAPI + rebuilding admin/auth/migrations to imitate Django; code and dependency costs |
| Transactional business product, many rules | Modular monolith in TS/Nest, Java/Kotlin Spring Boot or C# ASP.NET Core depending on skills | Django/Laravel/Rails with separate business services | Premature microservices; distributed transactions and data copies |
| Versioned public API, long-lived contracts | TS/Fastify, Python/FastAPI, Java/Spring or C# ASP.NET Core depending on the ecosystem | Go if the team and operations are suited to it | Language selected from a bare benchmark; retain validation, auth, errors and contract evolution |
| Small HTTP adapter / webhook | TS/Hono or Fastify, Go `net/http`/chi, Python/FastAPI if already using Python | Function in the existing API; existing Flask | New large framework/process for two routes without an independent need |
| BFF aggregating several services | TS + familiar framework, explicit auth and timeouts | Existing backend in its language | Additional gateway or duplicated business logic; reduce fan-out and payloads |
| AI API that only calls a remote LLM | TS/Bun or existing server stack, APISIX call | Python if a useful orchestration library is actually required | “AI therefore Python/GPU”; no local model or ML service without a need |
| Document RAG | Existing API + Python worker if parsing/ML justifies it | TS worker if SDKs/extractors suffice | Multiplying databases/vector stores without evaluation; budget indexing/embedding cost |
| Inference with an existing Python model | Python worker and the model's libraries; FastAPI for an HTTP interface if necessary | Validated specialized runtime, model export after measurement | Synchronous web API blocked by computation; model duplication in RAM/VRAM per worker |
| Training / scientific analysis | Python and scientific libraries; bounded jobs | R for statistical methods/team; existing native tools | Web framework for a batch; oversubscribed CPU/GPU pools |
| Import/export, bounded ETL | Existing server language; Python if the data ecosystem is useful | SQL for computation close to data; Go if streaming/binary packaging is useful | Spark/cluster before measured limits; avoid transfers and loading everything into RAM |
| Distributed processing already on Spark | Scala or PySpark depending on libraries and team | Authorized existing engine; distributed SQL | Adding Spark to a platform that does not offer it for a small CSV; extra orchestration and compute |
| Internal interactive statistical report | R/Shiny or Python/Streamlit with defined access and load | Conventional web application for a complex shared product | Prototype assumed equivalent to a multi-tenant product without session, authorization and testing work |
| Notifications, OCR, file conversion | Worker in the libraries' language, short API call + job | TS, Python, Go, Java depending on formats | CPU loops in the controller; API oversized because of long-running tasks |
| Workflow with human waiting/recovery | Supported Temporal SDK in the chosen stack, verified when used | Queue + application state for a simple task | Engine for simple queuing; or in-memory timer for a durable wait |
| Collaboration, chat, presence | TS/WebSocket in a familiar stack; Elixir/Phoenix with expertise and supervision needs | Go, Java, .NET according to SDKs/protocols | Elixir imposed by the word “real-time” alone; unbounded connections and buffers |
| Network collector, continuous ingestion | Go `net/http`/chi or existing stack with backpressure | Rust for a demonstrated constraint; Java/.NET with existing tooling | Systematic rewrite in Rust; first check DB, allocations, protocol and batches |
| CPU-intensive computation / codec / critical parsing | Appropriate algorithm and library, then Rust/Go/C++ according to the profile | Python with native kernels; optimized Java/.NET | Replacing the whole application; optimize only the measured segment |
| CLI / distributed operations tool | Go if a standalone executable is useful; Python/TS if runtime already available | Rust for low-level constraints and a capable team | HTTP server for a command; framework and idle processes |
| Mobile application with deep sensor/background needs | Swift/SwiftUI for Apple; Kotlin/Compose for Android | Flutter or React Native if plugins cover the needs | Web wrapper without checking offline/sensors; two native frontends without maintenance capacity |
| Cross-platform business mobile app | Flutter/Dart or React Native/TS depending on team and plugins | Responsive web/PWA if capabilities suffice | Native by default for forms; extra pipeline and distributed size |
| Embedded/hard real-time/hardware SDK | C/C++ or Rust depending on target, toolchain and actual constraints | Required manufacturer language | “Fast microservice” confused with hard real-time; memory/FFI review and tooling costs accepted |
| Modernization of an existing product | Compatible evolution of its stack, targeted extraction | Gradual migration if a limitation is established | Total rewrite to follow a trend; dual operations and regression risk |

## 5. Frontend, TypeScript and JavaScript

### 5.1 Choose rendering before the framework

| Option | Choose when | Do not choose solely because | Cost and expected evidence |
|---|---|---|---|
| HTML/CSS + targeted JS | Simple pages, modest interactions | Every project must have a framework | Little JS to transfer/execute; check accessibility and maintainability |
| React + Vite / Vue + Vite / Svelte in SPA mode | Rich authenticated interface, separate API, capable team | An SPA is necessarily faster for every user | Deployable static build; measure JS cost and initial client-side rendering |
| Static Astro + interactive islands | Mostly content with localized interactions | Astro would remove every need for a backend | Avoids server execution on every read and global hydration; dedicated API for mutations |
| Next.js or SvelteKit with rendering chosen per route | Dynamic public pages, initial rendering needs, justified integration | SEO always implies SSR; Next always implies a permanent server | Examine static generation/cache first; pay SSR runtime cost only for relevant routes |
| Angular | Angular team/existing system, useful shared conventions and tooling | “Enterprise” product necessarily means Angular | Bundle/build cost potentially offset by standardization; measure critical routes |
| Django/Twig/Blade/Rails templates | Server- and form-centered product, limited interactivity | Every interface must have a separate API + SPA | Reduces duplicated validation and two build stacks; budget server rendering |

**Apply the rendering branch in this order.** If pages can be generated ahead of requests, choose static output; use Astro when content dominates and only some areas are interactive. If users need a rich authenticated workspace and initial public indexing is irrelevant, prefer a Vite SPA. If request-specific public HTML is a demonstrated requirement, compare Next.js/SvelteKit rendering per route with server templates; do not make every route dynamic. For a form-centric product already in Django/Laravel/Rails, start with templates unless interaction or independent clients justify a separate frontend. A browser-only game needs neither SSR nor a backend unless a named feature requires one.

**React vs Vue vs Svelte vs Angular:** retain a maintained UI ecosystem first. For a new Vite SPA, prefer the team's demonstrated component/testing skills and required UI integrations; Angular wins only when its conventions/tooling are useful and maintainable, not because the customer is an enterprise. If still tied, compare one critical accessible screen, build/distribution cost and maintenance effort. Do not declare a winner from library bundle size alone. Reconsider the choice when a required editor, visualization, native bridge or accessibility behavior cannot be supported satisfactorily.

**Proposed rule L05 — do not create SSR, a BFF or a second API without a named responsibility.** The aim is to avoid permanent processes, repeated rendering computation and network hops. If SSR/BFF is selected: distinguish server and client modules, private/public cache, sessions, invalidation, errors, deployment and load cost. SSR is not a necessary condition for search indexing of a static website.

Browsers and mobile applications consume public interfaces or interfaces exposed for them. No server secret or `*.internal` URL in their shipped code. Calls to OpenBao, PostgreSQL, Valkey and APISIX with a server key belong in the backend/worker. This separation also applies to client modules in a full-stack framework; “same repository” does not mean “same trust boundary”.

### 5.2 TS/JS runtime

| Option | Use in this harness | Selection condition / cost |
|---|---|---|
| Bun | Default aligned with templates for API/worker and frontend installation/build | Test the SDKs actually used, native modules, instrumentation and shutdown behavior; explicit type-check in CI |
| Node.js | Alternative if an SDK or tooling requires/better supports Node, or for a stable existing system | Adapt commands/images and document the benefit; using Bun as a package manager does not change the production runtime |
| JavaScript without TS | Small isolated script, existing integration, clearly explained constraint | For a long-lived application, TS is the proposed default; TS does not replace runtime input validation |
| Edge runtime / Deno | Hosting target or standard API actually required | Do not add it for the “lightweight” label; check sockets, SDKs, secrets and this platform's network contract |

**Proposed rule L06 — test runtime compatibility instead of assuming it from npm.** Bun documentation explicitly describes compatibility differences. A small integrated proof is preferable to an abandoned full migration; it avoids adding a second “bridge” service to work around an SDK. Blocking CPU processing is isolated or bounded; `async` does not make CPU computation free.

### 5.3 TS/JS server framework

| Framework | Good fit | Alternatives / poor fit | Policy and cost |
|---|---|---|---|
| Fastify | API with validation/serialization schemas and structured plugins | Hono for a small adapter; Nest when cross-cutting modules/DI dominate | Define schemas at the boundary; accept validation cost for a reliable contract, without identical double validation at every layer |
| NestJS | Several business modules, team valuing injection, guards and conventions | Fastify/Hono if Nest's structure solves no problem | Modules/controllers/providers do not remove the need for business services; avoid decorators and providers without a responsibility |
| Hono | Focused routes and Web APIs, adapter/BFF or a real need for multiple runtimes | Complex business APIs are possible, but structure/contracts must be organized | Accept missing components, check middleware and SDKs; a small core does not prove low total cost |
| Express | Existing product, required middleware, experienced team | New service: compare Fastify/Hono according to contracts | Explicitly provide validation, errors, async and separation; do not rewrite reliable Express without a benefit |
| Native Bun API / `node:http` | Very narrow service with controlled invariants | Framework when routing, security or validation become recurring concerns | Avoids dependencies only while rebuilt infrastructure code does not outweigh the benefit |

**Explicit Fastify / Nest / Hono / Express decision path:**

1. If a healthy Express/Nest/Fastify application already owns the use case, extend it unless an identified capability or measured constraint blocks that option.
2. If the new API primarily needs explicit request/response schemas and plugins, with manageable composition owned by the team, **choose Fastify over Nest**. Reject Nest when its module/DI/guard conventions solve no concrete coordination problem.
3. If several domain modules repeatedly need consistent dependency wiring, guards and cross-cutting policies, and the team values those conventions, **choose Nest over bare Fastify/Hono**. Reject Nest when the delivery/maintenance cost of its abstractions exceeds the demonstrated benefit. Route count alone does not establish this need.
4. If a narrow adapter/BFF primarily needs Web `Request`/`Response` APIs or verified runtime portability, **choose Hono over a larger application framework**. For an API dominated by schema/serialization requirements, compare the complete Hono validation/OpenAPI/error stack with Fastify; select Fastify if it avoids assembling capabilities the team needs. Hono does not remove layering or authorization duties.
5. If essential middleware or an existing team's operational knowledge favors Express, **retain/choose Express** and explicitly provide validation/error/contracts. For a greenfield API without that advantage, prefer the candidate that covers those needs with less custom infrastructure.
6. If Nest wins structurally, choose its HTTP adapter separately: **Nest can use Fastify**, so “Nest versus Fastify” is not always exclusive. Check adapter-specific packages/middleware and the chosen Bun/Node runtime; preserve the same behavior in any comparison. [Nest adapter documentation](https://docs.nestjs.com/techniques/performance)

**Evidence before final selection:** implement or inspect one protected representative endpoint, input/output validation, error mapping, dependency lifecycle and shutdown. Include the real persistence/client path in an SLO test. Reverse the decision if missing middleware/SDK support, duplicated infrastructure or measured overhead defeats its stated benefit; never use the framework's name as a latency guarantee.

## 6. Python: distinguish business product and scientific ecosystem

| Option | Favorable case | Unfavorable case / alternative | Cost avoided or accepted |
|---|---|---|---|
| Django | Relational models, admin, forms, operator-managed product | Micro-adapter without data/admin: FastAPI/Flask suffice | Reuses ORM, migrations, admin; accepts framework cost instead of reimplementations |
| Django + DRF | API sharing Django domain and models, web/mobile/third-party clients | Do not add DRF to a server-rendered-only website | Serialization, permissions and API contracts; API-layer cost justified by consumers |
| FastAPI | Typed API, contract validation, Python/ML integration, compatible concurrent I/O calls | Rich business admin to rebuild: compare Django; batch only: no web framework | Targeted addition of persistence/auth if needed; ASGI and workers sized without multiplying models/pools |
| Flask | Healthy existing system, small WSGI service, team familiar with its extensions | Async concurrency is central: FastAPI/ASGI or another coherent stack | Accept the responsibility to select security/schemas/migrations; do not improvise a complete framework |
| Python without a server | ETL, scheduled task, CLI, training | HTTP only if a consumer actually needs it | No idle web server; CLI/job entry point separated from logic |
| Streamlit | Data exploration, focused internal tool, prototype of a scientific result | Multi-tenant product/public API/highly customized UI: appropriate backend + frontend | Understand reruns, session state and caches; limit recomputation, cross-user leakage and model copies |

**Explicit Django / DRF / FastAPI / Flask decision path:**

1. **No HTTP consumer:** choose plain Python plus the required libraries for a batch, CLI, training or worker. Reject every web framework unless an actual API is required; health probes alone do not justify exposing the business operation over HTTP.
2. **Relational operations and internal administration dominate:** choose Django when its models, migrations, forms and trusted-operator admin materially cover the required product. Add DRF **only** for separate API consumers. Prefer Django templates for ordinary forms; prefer Django+DRF if a SPA/mobile/partner must consume that domain. Do not rebuild this feature set in FastAPI without an identified benefit.
3. **An HTTP contract around Python libraries dominates, with little integrated admin/forms:** choose FastAPI. This includes a model-service interface or an API with useful typed validation and compatible I/O dependencies. Specify persistence, migrations, OIDC and authorization separately; FastAPI's API features do not provide the full business platform.
4. **Both rich admin and an ML/API need exist:** prefer Django+DRF plus a separate bounded Python job/worker when the ML operation can be invoked through the same application contract. Add a FastAPI service only for a named isolation/interface requirement; “we use ML” does not justify two HTTP frameworks. If the frontend is process-centric and highly customized, do not count Django admin as the delivered user UI: validate its actual fit with an operator screen. [Django admin scope](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)
5. **Healthy Flask system or a small WSGI integration with useful existing extensions:** retain Flask. For a new typed API without that advantage, prefer FastAPI when its contract tooling avoids rebuilding the same capabilities. If long-lived async I/O is central, compare an ASGI design; Flask's async view support retains a worker for the request and does not itself create durable background jobs. [Flask async model](https://flask.palletsprojects.com/en/stable/async-await/)

**Django vs FastAPI tie-breaker:** list the actual admin screens/forms/permissions Django would supply and the API/async composition FastAPI would simplify. Choose the option with less required feature assembly that the team can maintain, then verify one representative journey. If both are equivalent, retain the existing framework. Reverse a Django choice if its supposedly reusable admin needs extensive replacement and no longer delivers the benefit; reverse a FastAPI choice if it requires recreating the integrated business features that dominate the product. Neither reversal follows from a millisecond target alone.

**SLO consequence:** for a DB-bound CRUD route, inspect queries, indexes and pool waits before considering a framework switch. For many waiting HTTP calls, compare the complete sync/async dependency path under concurrency. For CPU-heavy inference, choose model execution, batching and isolation separately; changing Django to FastAPI does not accelerate the model. Test the final outcome and, if asynchronous, its separate completion target.

**Proposed rule L07 — identify the sync/async and CPU/I/O nature of each Python dependency.** Django also has async capabilities; FastAPI is not automatically faster; an `async` function that calls a blocking library remains problematic. Document where blocking executes and the pool limits. This avoids saturation, cascading latency and unnecessary process replication.

For scientific computation, start with algorithms, vectorized operations and proven libraries. The process/thread choice depends on the selected Python runtime, the library and its GIL handling; do not apply a generalization to every version/configuration. Bound workers **and** BLAS/OpenMP threads when present: multiplying them can saturate the machine. Separate model loading, inference and ingestion; measure RAM/VRAM per process. The GPU must match a compatible workload and library.

## 7. Java and Kotlin: choosing the JVM ecosystem

Java and Kotlin are languages; the JVM, JDK and a native image represent separate execution decisions. Kotlin may be chosen for a skilled team and required JVM libraries; Android does not impose it on the backend, and it is not systematically preferable to Java.

| Option | Favorable case | Alternative / poor fit | Cost and validation |
|---|---|---|---|
| Spring Boot | Broad business domain, transactions, integrations and familiar Spring tooling | Small adapter: compare a simple existing stack | Integration and conventions may avoid code; measure startup/RAM/build cost with the starters actually present |
| Quarkus | Jakarta/Quarkus ecosystem, established need for native packaging or constrained startup | Do not assume every containerized application needs a native image | Test extensions, reflection, DB, TLS and SDKs in the final mode; accept native compilation/CI cost |
| Micronaut | Skilled team, compile-time injection and suitable integrations | Spring already mastered with no observed limitation | Shifts work to build time; compare compatibility and diagnostics, not marketing figures |
| Ktor | Kotlin and explicit API composition, few integrated services required | Spring/Quarkus/Micronaut when their integrations save time | Accept plugin selection and assembly; no implicit free parallelism |

**Explicit Spring / Quarkus / Micronaut / Ktor decision path:** choose **Spring Boot** when the maintained Spring stack or required transactions/security/integrations save more work than another framework's execution mode. Choose **Ktor** when Kotlin is established and a focused API can be composed without rebuilding a large integrated feature set. Choose **Quarkus** when required extensions fit and a concrete startup/image/operations constraint makes its execution choices worth evaluating. Choose **Micronaut** when compile-time DI and its verified integrations fit the constraint and the team can maintain it. Reject a switch away from a healthy Spring application if the only argument is “microservices” or “native is faster”. Quarkus, Micronaut and Spring all require compatibility checks in their selected execution mode; these conditions are not exclusive vendor capabilities.

If Quarkus and Micronaut remain tied, use the actual extension/SDK inventory and team skill, then compare final artifact startup/readiness, loaded memory, route latency, diagnostics and CI build cost. Select native/AOT only if that result improves the relevant budget enough to accept restrictions; otherwise retain the conventional runtime. Record the missing extension or measured resource limit that would reverse the decision.

**Spring MVC vs WebFlux:** prefer MVC for a maintained imperative application and predominantly blocking JPA/JDBC integrations. Prefer WebFlux when a demonstrated concurrent I/O/streaming need, compatible non-blocking dependencies and team competence justify the different model. Using an HTTP client from MVC is an alternative to a full reactive rewrite. Do not choose WebFlux for CPU speed or merely because an SLO is strict. [Spring's applicability guidance](https://docs.spring.io/spring-framework/reference/web/webflux/new-framework.html)

**Proposed rule L08 — choose the concurrency model and compilation mode for an observed constraint.** Spring MVC with blocking access suits many products; WebFlux is justified by a non-blocking path and a demonstrated concurrency/streaming need. Mixing a blocking driver and an event loop without isolation recreates saturation. Virtual threads do not shorten CPU work or remove DB connection limits. AOT/native replaces neither profiling nor a support plan.

## 8. Go: compiled services and explicit structure

| Option | Favorable case | Limits / alternatives | Cost |
|---|---|---|---|
| `net/http` | Limited server/collector, simple middleware, Go team | Many application features to assemble | A sufficient standard library avoids dependencies; auth, validation and observability remain necessary |
| chi | Composable routing/middleware while retaining `net/http` | Not a complete business framework | Lightweight structure; documented assembly cost |
| Gin | Team already comfortable with its handlers, binding and middleware | Do not adopt it based on a promotional routing figure | Accept the framework and conventions; check validation/error contracts |

**Explicit `net/http` / chi / Gin decision path:** start with **`net/http`** if its routing plus a few clear middleware functions covers the service. Choose **chi** when grouped/composable routing and reusable `net/http` middleware simplify real route organization without needing a full framework. Choose **Gin** when the team's existing Gin handlers, binding and middleware cover more required behavior than they cost to adapt. Reject a switch between them if the problem is SQL, external calls or an unbounded goroutine pool. When still tied, prefer existing conventions or the smallest assembly that meets the whole contract, including validation, errors and observability. Verify one protected streamed/large-payload route where relevant; change the choice only for a concrete missing capability or measured remaining router/middleware cost.

Go is a candidate for CLIs, operations agents, collectors and APIs that benefit from its tooling model. It remains possible for business CRUD, but the lack of integrated admin may make Django/Laravel more economical overall. **Proposed rule L09 — bound goroutines, queues, buffers, requests and waiting times.** This prevents memory accumulation and uncapped calls to external services; “concurrent Go” does not mean “unlimited concurrency”. Check `CGO`, native libraries, certificates and target CPU before promising a standalone binary or a `scratch` image.

## 9. C# and .NET

ASP.NET Core can serve an API in an appropriate environment; this choice implies neither Windows nor Azure. Justify it through skills, libraries, tooling and contracts, then check the Linux image/target for this workshop.

| Option | Favorable case | Limit / alternative | Cost |
|---|---|---|---|
| ASP.NET Core Minimal APIs | Focused API, well-grouped endpoints, explicit validation | Do not confuse “minimal” with business logic in `Program.cs` | Reduces ceremony; services/contracts remain separate |
| ASP.NET Core controllers | MVC conventions, filters and API organization familiar to the team | Minimal APIs when those conventions add nothing | Structural cost accepted for consistency |
| Worker Service | Persistent jobs/consumers in the .NET stack | No HTTP controller beyond health/readiness when unnecessary | Shares libraries; explicit lifecycles and cancellation |
| Native AOT | Demonstrated deployment/startup need with compatible dependencies | Conventional JIT build when the benefit is not established | Accept compilation and dynamic-feature restrictions; tests on the final binary |

**Explicit Minimal APIs / controllers / Worker decision path:** choose **Minimal APIs** for focused endpoint groups with clear service delegation when controller conventions offer no needed feature. Choose **controllers** when the required filters, MVC conventions or existing organization reduce custom work; list the relevant feature rather than using “large application” as the justification. Both can structure substantial APIs. Choose **Worker Service** for continuous background processing that has no business HTTP interface. A product can have API and worker entry points sharing application code; it need not expose every job as a controller. Resolve a tie through the existing code and one representative authorization/validation/error path. Consider Native AOT separately only after checking dependency compatibility and the measured startup/resource constraint. [ASP.NET API models](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/apis)

**Proposed rule L10 — preserve a controller/endpoint → services → data-access boundary regardless of Minimal APIs or MVC.** It enables testing and reuse in a worker without duplicating computation and network access. EF Core is a persistence option, not a requirement for choosing .NET or adding a DB.

## 10. Rust: proven specialization or a product with an already-skilled team

Rust may suit a computation module, parser, CLI, system component or API with established constraints and a skilled team. Axum suits Tokio/Tower integration; Actix Web is another option if the team and middleware fit. The ownership model is a language capability; it does not demonstrate that this application will be cheaper, faster or safe in every use. `unsafe`, FFI, logic errors and external resources require their own review.

**Axum vs Actix Web:** choose Axum when the selected clients/middleware already align with Tokio/Tower and the team benefits from those conventions. Choose Actix Web when maintained Actix code, middleware and expertise cover the product better. Do not infer that choosing Actix Web requires an actor architecture. If neither has a unique benefit, prototype the actual authentication, cancellation, streaming and persistence boundaries in the team's stronger ecosystem; use a representative benchmark only for a real unresolved constraint. Reject a router rewrite when the critical cost lies in SQL or computation outside the framework.

**Proposed rule L11 — when replacing an existing component for performance, require a profile and a target segment.** First compare algorithm, SQL queries, allocations, formats and network calls. The expected benefit must cover compilation, complexity, maintenance and transfer between components. Extracting a library or worker may suffice; do not rewrite the frontend/business API to speed up a parser. A new project for which Rust is an accepted constraint may be valid without “proving” the failure of a fictitious prototype, but must comply with the chosen CCoE mode.

For the musl profile illustrated in the repository, check host/runner architecture, system libraries and the final artifact; do not blindly use `x86_64` on ARM. The production image must include what the program actually depends on.

## 11. PHP: Laravel or Symfony

| Option | Favorable case | Poor fit / alternative | Cost |
|---|---|---|---|
| Laravel | Business web application, forms, CRUD and integrated conventions; Laravel team | Small proxy: keep the existing stack; numerical needs: specialized worker | Reused features avoid assembly; do not deploy extra brokers/caches/DBs because a starter suggests them |
| Symfony | Existing Symfony system, components/DI and structure suited to a long-lived domain | Laravel if its conventions accelerate the team more | Modularity and integrations versus configuration; choose Doctrine according to the data |

**Laravel vs Symfony:** choose Laravel when its established application conventions and the team's Laravel knowledge directly cover forms, CRUD and jobs. Choose Symfony when an existing Symfony product, reusable components and its service organization better fit the required domain/integrations. Both support dependency injection; “we need DI” does not distinguish them. On a greenfield tie, compare one real workflow, its authorization and persistence, required packages, maintenance skills and operations. Reject Laravel if adopting it requires replacing needed Symfony assets without a compensating benefit; apply the same test in reverse. Reconsider only for a missing integration, sustained assembly burden or measured execution-mode constraint, not an abstract “enterprise” label. [Laravel container](https://laravel.com/docs/12.x/container), [Symfony container](https://symfony.com/doc/current/service_container.html)

**Proposed rule L12 — preserve framework conventions with separate business services, and check the selected execution mode.** Per-request processes and persistent workers have different lifetimes; no user state may leak between tasks. This avoids leaking connections, recomputation, duplicated state and concurrency bugs. Adapt jobs to the Valkey/Temporal contracts actually selected; a queue package does not establish compatibility with every queue.

## 12. Ruby: Rails

Rails is a candidate for a business web product when conventions, migrations, forms and Ruby expertise accelerate delivery. Its Active Record ORM is natural for relational data but does not remove the need for services for complex use cases, explicit transactions, access policy and query review.

Prefer an existing Rails system to a trend-driven migration. Compare a more focused framework for a simple adapter, or a specialized worker for numerical computation. **Proposed rule L13 — do not add a second SPA/API when templates and planned interactions suffice.** This avoids duplicated view models and builds; if mobile/public API needs require an HTTP boundary, make it explicit. Check the jobs/cache backend before adoption: no implicit new databases for framework features.

**Rails templates vs Rails API plus SPA:** choose templates when most interaction is forms/content inside the web product. Choose an explicit API when mobile/third-party clients or a genuinely rich independent frontend need it; shared business services remain below both entry points. For a new Ruby-based tiny adapter, compare the existing framework before adding Rails features that will remain unused. For a new business product comparing Rails, Django and Laravel, required libraries, integrated features actually used and maintainer skill settle the choice; no framework wins solely because it is “productive”. Verify the critical transaction and user interaction, and revisit only when the accepted capability/operations assumptions change.

## 13. Elixir: Phoenix and the BEAM ecosystem

Phoenix is a candidate for messaging, presence, collaboration and events when supervision and concurrency match the team's expertise. LiveView can reduce the amount of client-side UI logic to maintain for some products, with server-side state and connections to size. It is neither a latency guarantee nor a universal frontend replacement.

**Proposed rule L14 — distinguish many connections, business durability and CPU computation.** Supervision does not replace DB transactions, idempotence or workflow recovery after external effects. Bound mailboxes and load; avoid uncontrolled blocking native computation. Accept BEAM and hiring costs if the model simplifies the product; a TS/Go/.NET API may be a simpler choice for a team without Elixir.

**Phoenix LiveView vs a separate SPA:** choose LiveView when a connected server-driven interface fits the interactions and the team benefits from keeping UI behavior in Elixir. Choose a separate client when offline execution, local interactions independent of network latency or other API consumers require it. Reject a LiveView-only solution when essential actions must work without connectivity. Test actual interaction latency, reconnect behavior and server memory per connected user; if these exceed the agreed budget, change the UI boundary before changing the whole backend. A simple notifications feed may only need the existing API and SSE; it does not establish a need for Phoenix. [LiveView lifecycle and connected behavior](https://hexdocs.pm/phoenix_live_view/Phoenix.LiveView.html)

## 14. Scala, R and data processing

**Scala/JVM.** A candidate for business/data code already in Scala or existing Spark transformations. Choosing Scala does not require Spark; choosing Spark does not require Scala, since PySpark/SQL may meet the need. Do not introduce a cluster for a workload that SQL or a bounded process can handle. Compilation/tooling/operational overhead must be tied to reuse or measured volume.

**R.** A candidate for statistical methods, specialized libraries and analytical expertise; Shiny for suitable interactive presentation. A general product backend can consume results prepared by an R job. This split retains the scientific ecosystem without requiring the whole product to use R. R does not require Shiny to produce a file/report.

**SQL / Python / R / Spark decision path:** if relational filtering/aggregation meets the computation and freshness requirement in PostgreSQL, start with SQL and bounded result transfer. If custom transformations or Python libraries are necessary and a bounded job meets volume/deadline, choose Python. If an established R method/library and analytical maintainers are decisive, choose R; add Shiny only for an interactive report that fits its access/session needs. Consider Spark only after a demonstrated distributed-processing requirement and explicit platform/operations decision. With an existing Spark platform, choose Scala for maintained Scala/JVM transformations, PySpark for Python/data-team assets, or SQL when it expresses the work sufficiently. Estimate and then measure read volume, memory, shuffles/transfers and completion time before choosing an engine; do not use row count alone as the threshold.

**Proposed rule L15 — move computation closer to the data when that is simpler and measurable.** SQL aggregation, batch processing, projected columns and chunked reads may save more network and RAM than a language change. If an external engine is necessary, document ingestion, cost, ownership, recovery and exit strategy; it is not automatically provided by this repository.

## 15. C/C++, native mobile, cross-platform and desktop

| Need | Choices to examine | Platform boundary and cost |
|---|---|---|
| Hardware, C/C++ SDK, hard real-time, existing codec | Toolchain and language compatible with the target; Rust if supported and the team is skilled | Isolated native layer; accept cross-compilation, memory, FFI and hardware-testing cost; not a default web backend |
| Apple with deep system integration | Swift and SwiftUI/UIKit according to need/existing system | Client consumes an exposed API and suitable public-client OIDC; no service key in the binary |
| Android with deep system integration | Kotlin and Compose/Android APIs according to target | Same boundary; measure battery, network, background tasks and offline behavior |
| Cross-platform mobile | Flutter/Dart or React Native/TS depending on team/plugins | Test sensors, notifications, accessibility, offline and distribution; maintain a common backend |
| Standard mobile forms | Responsive web/PWA before native if capabilities suffice | Avoids two native pipelines and additional distribution; check actual functional limits |
| Desktop requiring files/local capabilities | Web application if sufficient; existing desktop/native solution otherwise | Perform a dedicated study of runtime, permissions, updates and signing; do not add Electron/Tauri automatically |

**PWA / React Native / Flutter / native decision path:** choose responsive web/PWA if it meets required device APIs, offline and distribution behavior. If native distribution is necessary, choose React Native when TS/React expertise and validated native packages cover the device needs; choose Flutter when Dart/Flutter expertise and its validated components cover them better. Choose Swift/Kotlin native interfaces when critical platform capabilities, interaction behavior or existing native assets justify separate implementations. Reject a shared framework if an indispensable background/sensor/accessibility capability fails on a target device. Settle a tie with one representative offline/device workflow, maintained plugins and release-pipeline ownership; verify startup, interaction responsiveness, battery and synchronization targets on actual target hardware. Do not infer client and server SLOs are the same metric.

**C/C++ vs Rust for native/system work:** use the supported manufacturer toolchain or retained native library when it is a hard constraint. Prefer Rust for a compatible new component when its memory/control model and team competence address the actual need; prefer maintained C/C++ integration when replacing it introduces unsupported FFI/toolchain risk. Hard real-time needs a dedicated worst-case execution, scheduling and hardware analysis; a web p99 result cannot qualify either language for that constraint.

**Proposed rule L16 — do not confuse a native client with a trusted internal service.** Even when distributed within an enterprise, the application is inspectable; use public contracts and user tokens. This avoids secret exfiltration and unnecessary tunnels/bridges. Offline means synchronization and conflict resolution, not an embedded PostgreSQL connection to the platform.

## 16. Cross-cutting cases that may change the choice

| Signal | Decision to make explicit | Incorrect inference to avoid |
|---|---|---|
| Maintainable existing system | Keep runtime/framework, upgrade gradually | Every old framework must be replaced |
| Vendor SDK available in only one stack | Isolated adapter or adoption of that stack, with contract tests | Rewrite the whole application in the SDK's language |
| ML/CUDA/native dependency | Verify image, architecture, ABI, license and quotas | A pip dependency installs everywhere or a GPU is available |
| Cold-start constraints | Measure final boot + DB/secrets/model initialization | AOT always has a better total cost |
| Strong integrity need | Model, DB and transactions before framework | Java/.NET guarantees distributed transactions |
| Real-time | Choose SSE/WebSocket/gRPC according to flow direction and clients | WebSocket everywhere, including for a several-minute job |
| Air gap | Bundled lockfiles, artifacts and dependencies, defined fallbacks | Runtime failure is acceptable because the build was connected |
| Insufficient performance | Profile, SLO, targeted optimizations, measurement after change | Rewrite in Go/Rust before inspecting N+1 queries or an external API |
| Educational deadlines | Familiar stack, declared learning objective | Novelty presented as technical optimization |
| Several autonomous teams | Module/contract ownership, then deployment if useful | Headcount requires microservices |

## 17. Admitting a stack to this platform

**Proposed rule L17 — a new stack must demonstrate the necessary contracts, not every possible integration.** For a stateless worker, do not create a DB/ORM/frontend. For a static website, do not create an API/worker. This reduces processes, pools and permanent resources.

For each selected component, provide the applicable elements:

- build/test/type-check or static-analysis command, lockfile and support for the chosen version; Bun gates do not validate Python/Java/Go;
- artifact and image compatible with CI, registry, runner OS/architecture and the repository's build model; do not copy a multi-stage Dockerfile that contradicts an active contract;
- startup, configuration, stdout/stderr logs, `/health`, `/ready`, graceful shutdown, quotas and no secrets in images;
- clients for only the consumed services: OIDC authentication, OpenBao secrets, PostgreSQL, Valkey, S3, APISIX, Temporal as appropriate; versions/protocols actually tested;
- stable HTTP/event contract between languages, serialization of dates/decimals/identifiers, timeouts, retries, idempotence and cancellation;
- operational impact and an owner capable of maintaining the stack; documentation of known incompatibilities.

For a Temporal SDK or queue package, check supported languages/runtimes **at implementation time**. HTTP compatibility with a platform does not guarantee compatibility of an SDK with workers/replay. Do not replace APISIX with a direct vendor SDK simply because it is available in the language.

## 18. Justification and waivers

Three distinct situations: **recommended profile**, **authorized alternative with an ADR**, **violation of an applicable rule requiring a waiver**. Choosing an alternative is not itself a violation. Identify the rule, its owner and its status before announcing mandatory approval; never invent professor approval.

The justification must hold up against this form:

```text
Component and need:
Mandatory constraints and unknown information:
Chosen language / runtime / framework / build:
Applied language comparison and project facts selecting one branch:
Applied framework branch, required features and rejected branch:
Why the template stack is sufficient or insufficient:
Credible alternative A / reason for rejection:
Credible alternative B / reason for rejection (if useful):
Verified capabilities, sources and versions actually tested:
Request / completion SLO, measurement boundary and target load:
Latency bottleneck hypothesis or profile, budget and validation experiment:
Compute saved OR additional cost accepted and why:
CI, network, secrets, health and contract adaptation:
Rule requiring a waiver, otherwise “none”:
Measurement or event that would trigger a review:
Maintenance owner and, for a waiver, scope/expiry/return to the standard:
```

Acceptable reasons depending on context: essential SDK, skills and maintenance of an existing system, business need covered by an integrated framework, explicit educational objective, target constraint, measured gain, isolated and bounded experimentation. Insufficient reasons on their own: popularity, agent preference, “more modern”, “faster”, “AI therefore Python”, “enterprise therefore Java”, “scalable therefore Go”, “secure therefore Rust”. **Proposed rule L18 — also document rejected alternatives and accepted cost.** This avoids repeating studies and migrations without new evidence; no fictitious compute savings are required when the real benefit is delivery time or maintainability.
