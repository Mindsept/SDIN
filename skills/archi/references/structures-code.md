# Code structures and responsibility boundaries

Reference for the `archi` skill. Read when creating, reviewing, or reorganizing an application, API, worker, CLI, or frontend. Read only the variants for the relevant language and framework. For storage, transaction, and ORM choices, see [Data and ORM](donnees-orm.md).

**Status:** the rules below form a policy proposed by this skill, not a description of business code already present in SDI. The directory trees are adaptable examples. Tool capabilities are sourced from their official documentation, accessed **October 14, 2026**. Project versions, explicit constraints, and useful conventions take precedence over migrating to another tool.

## Contents

1. [Deciding how much structure is needed](#1-deciding-how-much-structure-is-needed)
2. [Separation contract and dependency direction](#2-separation-contract-and-dependency-direction)
3. [Models, modules, and composition](#3-models-modules-and-composition)
4. [Directory trees by ecosystem](#4-directory-trees-by-ecosystem)
5. [Frontend, worker, CLI, and integrations](#5-frontend-worker-cli-and-integrations)
6. [Verifying boundaries](#6-verifying-boundaries)
7. [Decision and review](#7-decision-and-review)

## 1. Deciding how much structure is needed

Start with the behaviors actually requested, execution modes, and rules to preserve. A directory does not prove a boundary exists; a well-named function or module may suffice.

| Situation | Suitable initial structure | Trigger for further separation |
|---|---|---|
| Static page, local game, client-side calculator | UI, local state, and computation functions if needed | Shared persistence, identity, collaboration, or server processing requested |
| CLI or one-off file-based job | CLI entry point, processing function, file adapter; no HTTP controller | Several entry points, reused rules, or an external dependency to isolate |
| Small CRUD API | Feature module with identifiable transport, application service, and data access | Complex invariants, several transports, several use cases, or integrations |
| Business application with several features | Feature-oriented modular monolith; lightweight internal layers | Measurements and constraints demonstrating the need for independent deployment |
| Asynchronous processing | Consumer adapter + use case + outbound adapters | Concurrency or a specific resource justifying a separate executable or container |
| Durable workflow | Orchestration workflow, activities, and use cases; separate business persistence | Waits, recovery, compensation, and compatibility with ongoing executions |

**CODE-01 — MUST:** create only responsibilities that are actually present; do not generate empty directories, interfaces, services, or containers to match an architectural shape. **Benefit:** readable scope and proportionate maintenance. **Compute avoided:** unnecessary idle services, builds, images, and plumbing tests; accepted cost: introduce the boundary when the need appears.

**CODE-02 — SHOULD:** prefer a feature-oriented modular monolith when the application shares a lifecycle and has no constraint justifying distributed services. **Benefit:** local transactions and refactoring, simpler deployment. **Compute avoided:** networking, serialization, observability, and replicas for artificially separated components; accepted cost: deploy modules together and monitor their dependencies.

In this repository, `frontend`, `api`, and `worker` are three **template** components, to remove if unnecessary, not a mandatory three-container architecture. Local source: [templates/podman-compose.yml, lines 8–13 and 62–95](../../../td/core-platform/templates/podman-compose.yml). The presentation specifically gives a single-player game served by a static frontend as an example of simplicity: [sdi-2026.src.html, lines 850–863](../../../presentations/sdi-2026.src.html).

## 2. Separation contract and dependency direction

When an entry point carries a business request, the path is:

```text
Transport / controller / consumer / CLI command
    → application service / use case
        → domain rules
        → outbound ports
            ← adapters: SQL repositories, S3, LLM, events, clock…
```

This diagram distinguishes **runtime calls** from **code dependencies**. The service calls a port; the adapter implementing it depends on the port's contract. The domain does not depend on the ORM, transport, or adapters. The composition root may know implementations in order to assemble them.

### Responsibilities and limits

| Element | Contains | Do not put here |
|---|---|---|
| Transport / controller | Decoding, structural validation, already-authenticated identity, DTO → command conversion, use case call, result/error → protocol conversion | SQL, direct ORM calls, business calculations, deciding a discount, multistep transaction, provider orchestration |
| Application service / use case | Business authorization, coordination, transaction boundary, idempotency, calls to rules and ports, explicit result | HTTP details, framework responses, opaque global connection, scattered SQL |
| Domain | Invariants, allowed transitions, business calculations, values, and decisions | Queries, HTTP client, request context, environment variables, hidden system clock |
| Ports | Contracts required by the use case: retrieve a case, record a transition, read a file, obtain the time | Reproducing the entire ORM API, interfaces without consumers, universal CRUD methods without semantics |
| Adapter / repository | Parameterized queries, data mapping, technical transactions, external-system client, translation of technical errors | Business decisions scattered through hooks, public HTTP contract, implicit authorization policy |
| Composition | Loading configuration, creating pools/clients, injection, assembling routes and consumers, graceful shutdown | Business rules or data access during module import |

**CODE-03 — MUST:** separate transport, use cases, business rules, and access to external systems as soon as those responsibilities exist; the controller contains neither SQL nor business logic. **Benefit:** a rule remains identical when invoked from HTTP, a CLI, or a worker and can be verified without a server. **Compute avoided:** full scenarios launched to test a pure rule and duplicated I/O across entry points; accepted cost: an explicit handoff between transport and use case. This handoff can be a function, not necessarily a class.

**CODE-04 — MUST:** direct dependencies toward the domain and application contracts; isolate frameworks, ORMs, and SDKs within technical boundaries. **Benefit:** business rules remain independent of protocol and storage. **Compute avoided:** initializing a server, pool, or SDK to run business tests; accepted cost: contracts and conversions at boundaries. A constraint from an existing framework can be documented with its scope rather than hiding the coupling.

**CODE-05 — MUST:** centralize sensitive business decisions in the domain or use case, especially object permissions, transitions, and amounts; transport validations remain input validations. **Benefit:** no alternative entry point bypasses the rule. **Compute avoided:** invalid operations started before rejection; accepted cost: a few repeated validations when they protect a distinct boundary. A well-formed DTO is not authorization.

### Placement examples

| Decision | Placement |
|---|---|
| “The JSON contains a valid identifier and date” | Transport schema/DTO |
| “This actor may approve this case” | Business policy called by the use case, with identity context |
| “An archived case can no longer be approved” | Domain invariant |
| “Lock or check the version before the transition” | Requirement expressed by the use case, mechanism implemented by the transactional adapter |
| “Find this tenant's 30 cases after this cursor” | Specific read port, SQL or ORM in the adapter |
| “Respond with HTTP 409” | Error mapping at the transport layer; the domain expresses a business conflict |
| “Obtain a model response within the app's budget” | LLM port consumed by the use case, APISIX adapter |

An application service that only calls a repository can be a short function in a small CRUD application. It remains the place for permissions, transactions, and orchestration if they arise. There is no need to invent a rich aggregate around a catalog read; the business boundary still remains.

## 3. Models, modules, and composition

### DTOs, domain, and persistence

**CODE-06 — MUST:** explicitly define the data allowed in and out; never automatically expose an entire ORM entity. **Benefit:** stable API contract and no leakage of internal fields. **Compute avoided:** lazy loading during serialization, relational graphs, and unnecessary payloads; accepted cost: explicit projection or mapping.

**CODE-07 — SHOULD:** distinguish transport types, business models, and persistence representations when their rules, lifecycles, or fields diverge. **Benefit:** each model expresses its constraint. **Compute avoided:** recursive mappings and aggregate hydration for simple reads; accepted cost: maintain targeted conversions. Sharing an immutable value type or identical projection is possible; mechanically copying every field three times does not constitute an architecture.

“Document” example:

- `UploadDocumentRequest` contains the client-supplied name and a controlled upload reference; no `ownerId` field is accepted as authoritative.
- `RegisterDocumentCommand` contains the actor/tenant from authentication and the validated intent.
- `Document` carries relevant transitions if they exist: draft, indexable, published, archived.
- `DocumentRow` describes persisted columns: identifiers, S3 key, status, version, fingerprint, dates.
- `DocumentSummary` is a read projection suited to the interface; no need to reconstruct the whole aggregate for a list.

Conversions precisely handle dates/time zones, `null`, decimals, integers exceeding JavaScript precision, unknown enums, and confidential fields. A mapping can be a column selection; it does not require a dedicated library.

### Feature modules

**CODE-08 — MUST:** give each feature an identified public interface and prevent imports into another module's internal adapters; circular dependencies are fixed or explicitly isolated in a bounded migration. **Benefit:** data ownership and independent module evolution. **Compute avoided:** hidden cross-module queries and unnecessary transitive loading; accepted cost: contracts between modules and a few dedicated projections.

**CODE-09 — MUST:** prohibit catch-all packages such as `utils`, `common`, or `helpers` when they mix responsibilities without an owner. **Benefit:** understandable dependencies. **Compute avoided:** frontend bundles and transitive initializations triggered by an innocuous import; accepted cost: name the actual abstractions, such as `money`, `time`, `pagination`, `http-errors`. A small, coherent, shared technical module remains possible.

**CODE-10 — SHOULD:** keep an app's API and worker in a coherent set of modules or packages, sharing use cases instead of copying rules. **Benefit:** business compatibility and controlled migrations. **Compute avoided:** duplicated builds and transformations; accepted cost: version together the contracts on which several executables depend. Sharing code does not justify coupling to the same memory or transactions.

The `dossiers` module can call the public use case `documents.autoriserLecture`; it does not read the `documents` authorization table directly. Future extraction into a service remains an option, not a requirement to prepare for with internal HTTP calls right now.

### Composition and resources

**CODE-11 — MUST:** create and close heavyweight resources within the process lifecycle; inject required pools, clients, and parameters without starting I/O on import. **Benefit:** predictable startup, tests, and shutdown. **Compute avoided:** a pool per request, orphan connections, and unnecessary initialization; accepted cost: explicit composition root and shutdown management.

A request identity, ORM session, or transaction is not a singleton. Validated configuration or a bounded pool may be shared. An object's lifetime is a choice distinct from its architectural layer.

## 4. Directory trees by ecosystem

The examples use a `documents` feature. Preserve the framework's own resolution and generation conventions. English names are illustrative; choose a consistent language for business identifiers. Create listed files only when they carry a concrete responsibility.

### TypeScript — Fastify

```text
src/
  main.ts                         # process lifecycle
  app.ts                          # Fastify construction and composition
  modules/documents/
    index.ts                      # module's public interface
    transport/http/
      routes.ts                   # route registration
      controller.ts               # DTO -> use case -> response
      schemas.ts                  # input/output schemas
    application/
      register-document.ts
      list-documents.ts
      ports.ts                    # contracts actually consumed
    domain/
      document.ts
      publication-policy.ts
    infrastructure/
      postgres-document-repository.ts
      s3-document-store.ts
  infrastructure/
    postgres-pool.ts
    config.ts
tests/
  architecture/
  documents/
migrations/                       # a single owning mechanism
```

A Fastify plugin bounds routes, hooks, and decorators; it can represent a transport module. Fastify encapsulation does not prove domain independence: imports must also respect boundaries. A `makeRegisterDocument(dependencies)` function suffices to inject ports without a DI container. Official documentation: [Fastify, encapsulation](https://fastify.dev/docs/latest/Reference/Encapsulation/), accessed October 14, 2026.

### TypeScript — NestJS

```text
src/
  main.ts
  app.module.ts
  documents/
    documents.module.ts           # composition, limited exports
    transport/
      documents.controller.ts
      dto/register-document.dto.ts
    application/
      register-document.service.ts
      ports/document-repository.ts
    domain/document.ts
    infrastructure/
      postgres-document.repository.ts
  platform/
    database.module.ts
    configuration.module.ts
test/architecture/
```

The controller delegates to the application provider; the ORM belongs in infrastructure providers. Injection tokens associate a port with an adapter; avoid global modules that make all dependencies implicit. The domain can remain plain TypeScript classes or functions without Nest decorators. References: [Nest, providers](https://docs.nestjs.com/providers) and [modules](https://docs.nestjs.com/modules), accessed October 14, 2026. A Nest service is not automatically a domain or repository: the name must match its responsibility.

### Python — Django and Django REST Framework

```text
config/
  settings.py
  urls.py
documents/
  apps.py
  urls.py
  admin.py                        # operator entry point, same business rules
  api/
    views.py                      # DRF transport
    serializers.py                # contract and structural validation
  services/
    register_document.py          # use cases and atomicity
  domain/
    publication.py                # pure rules if present
  persistence/
    queries.py                    # reads/projections
    repositories.py               # targeted business writes
  models.py                       # Django persistence models
  migrations/
  tests/
```

Django models stay where the framework expects them. Pure rules are not buried in `views.py`, `Serializer.create()`, or signals. To apply CODE-03 to a `ModelViewSet`, its read and write paths pass through identified services/selectors: DRF hooks do not become a second set of business logic. A deferred `QuerySet` is not an already-materialized projection; consuming it must remain within a boundary that controls the session and query count.

**The admin is also an application entry point.** Apply CODE-03/CODE-05 to transitions, permissions, and business writes in `ModelAdmin` and its actions: delegate to the same use cases, adapt permissions and the scope of visible objects. If the generic screen cannot cleanly guarantee these rules, make the operation read-only or provide a dedicated action/view. Avoid saving a second time after a use case has already persisted the change. The `save_model`/`delete_model` hooks are not designed as vetoes; bulk deletion actions behave differently from an individual `Model.delete()` call. Test creation, editing, actions, and deletion through this entry point, not only through DRF. Sources: [Django admin](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/) and [admin actions](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/actions/), accessed October 14, 2026. Casdoor login integration for this operator area still needs to be designed; Django admin does not become OIDC automatically.

Choosing Active Record does not make Django models independent of persistence. A service can manipulate a result from these models without rebuilding three copies of every object; ORM calls and their evaluation remain in identifiable selector/query/repository functions. Reusable invariants stay in pure functions or objects. A repository interface is useful when it expresses a real contract; a generic wrapper around every Django method is unnecessary. This idiomatic adaptation permits neither ORM calls in the controller nor SQL in the middle of a use case. The boundary is visible in `queries.py` and `repositories.py`; existing code that still mixes these roles requires a migration or an explicit deviation. Asynchronous Django also requires transaction precautions detailed in [Data and ORM](donnees-orm.md). Source: [Django, asynchronous support](https://docs.djangoproject.com/en/5.2/topics/async/), accessed October 14, 2026 for the documentation version specified by the link.

### Python — FastAPI

```text
app/
  main.py                         # lifespan, router assembly
  wiring.py                       # dependencies and session scopes
  documents/
    router.py
    schemas.py                    # Pydantic transport models
    application/
      register.py
      ports.py                    # Protocol or functional contracts
    domain/
      document.py                 # dataclass/values, if useful
    adapters/
      sqlalchemy_repository.py
      orm_models.py
      object_store.py
alembic/
tests/
```

`Depends` injects the service or its dependencies at the boundary; the domain does not import FastAPI. `async def` does not turn a synchronous driver into nonblocking I/O. Define a consistent chain of async drivers/sessions or a synchronous boundary executed through the mechanism provided by the framework. Do not pass a request session to a job that will run after the response. Source: [FastAPI, concurrency and async](https://fastapi.tiangolo.com/async/), accessed October 14, 2026.

### Java / Kotlin — Spring

```text
src/main/java/com/example/app/      # src/main/kotlin for Kotlin
  Application.java
  documents/
    Documents.java                # optional public facade
    api/
      DocumentController.java
      RegisterDocumentRequest.java
    application/
      RegisterDocument.java
      port/DocumentRepository.java
    domain/
      Document.java
      PublicationPolicy.java
    infrastructure/
      persistence/
        DocumentEntity.java
        SpringDataDocumentRepository.java
        JpaDocumentAdapter.java
  configuration/
    DocumentConfiguration.java
src/main/resources/db/migration/
src/test/java/com/example/app/architecture/
```

The Spring Data interface and JPA entity belong to persistence; they do not become the REST contract. The use case defines the transaction boundary, through an annotation or an explicit unit of work according to the project's strategy. A transactional annotation depends on framework mechanisms: check internal calls/proxies before assuming it is effective. The domain remains testable without a Spring context. A Gradle/Maven module per feature is necessary only if isolation or build times justify it; packages often suffice. Sources: Spring Modulith, [fundamentals](https://docs.spring.io/spring-modulith/reference/fundamentals.html), and Spring Framework, [using `@Transactional`](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html), accessed October 14, 2026.

### Go

```text
cmd/
  api/main.go
  worker/main.go                  # only if necessary
internal/
  documents/
    domain/
      document.go
    application/
      register.go
      ports.go                    # small consumer-side interfaces
    http/
      handler.go
      dto.go
    postgres/
      repository.go
      queries.sql
      generated/                  # sqlc, if selected
  platform/
    config/config.go
    database/pool.go
migrations/
```

The `handler` decodes and calls the use case; `context.Context` carries cancellation and deadlines to I/O calls without becoming a bag of business parameters. Errors remain typed or categorized before HTTP translation. For a small module, `internal/documents/register.go` and separate adapters can replace numerous subpackages; package granularity must avoid cycles. `internal` limits importing from outside its tree but does not enforce every rule between internal modules on its own. Reference: [Go, module layout](https://go.dev/doc/modules/layout), accessed October 14, 2026.

### C# — ASP.NET Core / .NET

```text
src/
  App.Api/
    Program.cs                    # composition and lifecycle
    Features/Documents/
      DocumentEndpoints.cs        # or DocumentController.cs
      RegisterDocumentRequest.cs
  App.Application/
    Documents/RegisterDocument.cs
    Documents/Ports/IDocumentRepository.cs
  App.Domain/
    Documents/Document.cs
  App.Infrastructure/
    Persistence/AppDbContext.cs
    Persistence/Documents/DocumentConfiguration.cs
    Persistence/Documents/EfDocumentRepository.cs
    Persistence/Migrations/
tests/
  App.ArchitectureTests/
  App.IntegrationTests/
```

This project-level separation enforces verifiable references, but a single project with feature namespaces suits a small app. Minimal APIs remain a transport: the route lambda does not absorb the transaction or business logic. A `DbContext` session is not a singleton shared across requests and is not used concurrently by several operations. Persistence can combine EF Core with a targeted Dapper read, with a single transaction strategy and migration mechanism. Official source for query analysis: [EF Core, efficient querying](https://learn.microsoft.com/en-us/ef/core/performance/efficient-querying), accessed October 14, 2026; see also lifetime sources in [Data and ORM](donnees-orm.md).

### Rust

```text
src/
  main.rs                         # runtime, configuration, assembly
  lib.rs
  documents/
    mod.rs                        # explicit exports
    transport.rs                  # axum/actix/etc. handlers as used in the project
    application.rs
    domain.rs
    ports.rs                      # useful traits or injected functions
    postgres.rs
  platform/
    config.rs
    database.rs
migrations/
tests/
```

Introduce a workspace with `domain`, `application`, `infrastructure` crates and executables when dependency separation or reuse justifies it; not a crate per file. The domain can use error enums and business types without HTTP, SQLx, or Diesel. The choice between generic traits and trait objects addresses injection needs and compilation constraints; it is not a requirement for dynamic allocation. Rust visibility restricts exports; it does not replace crate dependency analysis. Source: [Rust, visibility and privacy](https://doc.rust-lang.org/reference/visibility-and-privacy.html), accessed October 14, 2026.

### PHP — Laravel

```text
app/
  Http/
    Controllers/DocumentsController.php
    Requests/RegisterDocumentRequest.php
    Resources/DocumentResource.php
  Documents/
    Application/RegisterDocument.php
    Application/Ports/DocumentRepository.php
    Domain/PublicationPolicy.php
    Infrastructure/EloquentDocumentRepository.php
  Models/Document.php             # Eloquent persistence model
  Providers/DocumentsServiceProvider.php
database/migrations/
routes/api.php
tests/
```

`FormRequest` and `Resource` carry the HTTP contract; the controller delegates. Policies can delegate to a reusable business policy; a job or command does not rely exclusively on HTTP middleware for authorization. Eloquent observers and callbacks do not hide external calls or business orchestration. Laravel conventions can be preserved without making the persistent model the API response. Sources: [Laravel, controllers](https://laravel.com/docs/12.x/controllers) and [Eloquent](https://laravel.com/docs/12.x/eloquent), accessed October 14, 2026 for the indicated pages, without prescribing a version.

### PHP — Symfony

```text
src/
  Documents/
    UI/Http/DocumentController.php
    UI/Http/RegisterDocumentRequest.php
    Application/RegisterDocument.php
    Application/Port/DocumentRepository.php
    Domain/Document.php
    Infrastructure/Doctrine/DocumentRecord.php
    Infrastructure/Doctrine/DoctrineDocumentRepository.php
config/services.yaml
migrations/
tests/
```

Symfony services assemble dependencies; the controller adapts the protocol. Doctrine can map a domain entity using separate metadata when a single model remains clear, or use a separate record when constraints diverge. Do not mandate two identical classes without reason or expose Doctrine proxies to the transport. Sources: [Symfony, controller](https://symfony.com/doc/current/controller.html) and [Doctrine, getting started](https://www.doctrine-project.org/projects/doctrine-orm/en/current/tutorials/getting-started.html), accessed October 14, 2026.

### Ruby — Rails

```text
app/
  controllers/documents_controller.rb
  services/documents/register_document.rb
  domain/documents/publication_policy.rb
  queries/documents/list_documents.rb
  repositories/documents_repository.rb
  models/document.rb              # Active Record, conventions preserved
  serializers/document_summary.rb # if required by the output contract
  jobs/index_document_job.rb
db/migrate/
test/                              # or spec/ according to the existing project
```

The controller does not compose business queries. A command service and query object often suffice; do not introduce a hierarchy of generic repositories. Active Record callbacks do not hide an external workflow. The worker receives a stable identifier and reloads through the use case, rather than receiving an object tied to stale connection state. Rails remains based on its Active Record conventions; pure rules are extracted when they exist. Source: [Rails, Active Record basics](https://guides.rubyonrails.org/active_record_basics.html), accessed October 14, 2026.

### Elixir — Phoenix

```text
lib/app_web/
  controllers/document_controller.ex
  controllers/document_json.ex
lib/app/
  documents.ex                    # context's public API
  documents/
    register_document.ex          # orchestration if it grows
    publication_policy.ex         # pure rules
    document.ex                   # Ecto schema, or separate record if useful
    queries.ex
    repository.ex                 # targeted adapter if the context needs one
  repo.ex
priv/repo/migrations/
test/
```

Phoenix contexts structure business capabilities; `app_web` calls the context API. In simple CRUD, the same context can group **distinct, identifiable** application and persistence functions: the former delegate queries to the latter. This mapping satisfies CODE-03/DATA-04 without requiring a repository class or scattering `Repo` across controllers or business transitions. Extract the pure domain and ports when their responsibilities appear. A GenServer is not a universal substitute for a stateless application service or SQL transaction. Changesets describe validations and data changes; a multistep process deserves explicit orchestration. Sources: [Phoenix, contexts](https://phoenix.hexdocs.pm/contexts.html) and [Ecto](https://ecto.hexdocs.pm/Ecto.html), accessed October 14, 2026.

### Other contexts: map the responsibilities

| Context | Mapping |
|---|---|
| Express, Hono, Koa | Route/middleware → use case function → rules → adapters; do not put SQL in a route callback |
| Flask | Blueprint/view → application service → rules → adapters; Flask context stays at the boundary |
| Ktor, Micronaut, Quarkus | Routing/controller → use case → domain → persistence/infrastructure according to project conventions |
| Mobile or desktop application | View/ViewModel/presenter → application action → rules → remote API/local storage; no embedded server secrets |
| Reusable library | Public API → business functions → necessary ports; no server or container added without a request |

These mappings express the skill's policy, not verified features of every framework or a requirement to adopt them.

## 5. Frontend, worker, CLI, and integrations

### Frontend

```text
src/
  app/                            # routes, composition, providers
  features/documents/
    ui/                           # components and accessibility
    application/                  # actions, UI orchestration
    model/                        # state, local rules if needed
    api/                          # HTTP contract and error conversion
  design-system/                  # visual components actually shared
  platform/http-client.ts
```

A small page can be limited to a few files. In a server-rendered application, mark server-only modules and keep secret-bearing ORM/SDK imports out of the client bundle; SSR does not remove the browser/backend boundary. A UI event handler can drive an interaction but does not decide server authorization on its own. Remote data, navigation state, temporary form state, and derived computations do not necessarily share the same storage mechanism.

**CODE-12 — MUST:** prevent imports of server persistence, secrets, and internal SDKs into code delivered to the browser. **Benefit:** explicit trust boundary and controlled backend contract. **Compute avoided:** heavy bundles, unnecessary initialization, and impossible calls to internal DNS names; accepted cost: backend endpoint or facade for private operations.

### Workers and workflows

```text
worker/
  main                         # configuration, concurrency, shutdown
  consumers/                   # Valkey or selected broker protocol
  handlers/                    # message -> command -> result
  workflows/                   # only for durable orchestration
  activities/                  # workflow I/O, through use cases
application/                   # can be shared with the API
adapters/                      # SQL, S3, LLM, other systems
```

The consumer decodes, passes the required identity/scope, calls the use case, and applies the acknowledgment policy. The “already processed” decision belongs to persisted idempotency logic; a `try/catch` that systematically acknowledges an exception destroys this guarantee. A Temporal activity performs effects; the workflow orchestrates them according to SDK constraints. Durability, recovery, and data details are covered in [Data and ORM](donnees-orm.md) and other relevant skill references.

### CLI and batch

A CLI command replaces the controller: arguments/stdin → use case → output/exit code. The HTTP component disappears. A purely analytical job can use a transformation function and file adapter, without a relational repository or artificial domain. Input errors, business errors, and infrastructure errors retain explicit categories so automation can distinguish data correction from recovery.

### External integration

The SDI contract mentions an `upstream` container for external flows but does not provide its implementation: [README, line 33](../../../td/core-platform/README.md). If needed, specify protocol, deadlines, throughput, caching, recovery, and data ownership; do not imply that moving an HTTP client into another container provides network isolation on its own. The provider adapter must not contaminate business types with every detail of its response.

## 6. Verifying boundaries

**CODE-13 — SHOULD:** automate the few genuinely sensitive boundaries in the project's existing tooling before adding another tool. **Benefit:** drift detected during review and CI. **Compute avoided:** integration suites used to detect simple import errors; accepted cost: running and maintaining a small set of static rules.

**CODE-14 — MUST:** verify critical behaviors with tests at the appropriate level: domain without infrastructure, use cases and authorization, adapter integration, then a few complete flows. **Benefit:** boundaries protect actual behavior. **Compute avoided:** multiplying redundant end-to-end tests and starting the whole platform for every function; accepted cost: real SQL tests for guarantees that in-memory doubles cannot reproduce.

| Ecosystem | Suitable check | Limitation to understand |
|---|---|---|
| JS/TS and frontend | [ESLint `no-restricted-imports`](https://eslint.org/docs/latest/rules/no-restricted-imports) for local prohibitions; [dependency-cruiser](https://github.com/sverweij/dependency-cruiser) for graphs, layers, and cycles | A static rule must cover aliases and reexports; do not assume it forbids a dynamically constructed import |
| Python | [Import Linter](https://github.com/seddonym/import-linter) for import contracts; service tests with pytest/unittest according to the existing project | Introspection and dynamic imports also require review; isolate necessary Django exceptions |
| Java/Kotlin | [ArchUnit](https://www.archunit.org/userguide/html/000_Index.html), possibly already-installed Spring module checks | Tests bytecode dependencies; adapt rules to generated classes and the language |
| Go | `internal` boundaries, cycle-free packages; dependency test based on `go list -deps`/package graph | `internal` does not automatically separate every module within an app |
| C# | Project references and [NetArchTest](https://github.com/BenMorris/NetArchTest) if useful | Scan the relevant assemblies and avoid rules based only on filenames |
| Rust | Crate dependencies, module visibility; Cargo graph audit and tests | Compilation forbids some dependencies, not misplaced business decisions; do not add an unnecessary workspace |
| PHP | [Deptrac](https://deptrac.github.io/deptrac/) and namespaces | Define collectors that actually cover services and generated code; review dynamic loading |
| Ruby | Public modules, tests; [Packwerk](https://github.com/Shopify/packwerk) if packages are justified by the project | Checks statically analyzable references, not every effect of metaprogramming |
| Elixir | Public contexts, ExUnit tests, and [`mix xref`](https://mix.hexdocs.pm/Mix.Tasks.Xref.html) to explore dependencies/cycles | The graph supports review; an inspection command is not automatically a blocking CI rule |

Tool sources: linked official documentation or repositories, accessed October 14, 2026. Exact commands are chosen according to versions already locked in the project; no “latest” version is required.

### Invariants to test instead of an exact directory tree

1. A controller does not import the SQL client, ORM, or concrete repository.
2. A business rule can be tested without starting the framework, opening a socket, or reading a secret.
3. A business module does not traverse another module's private imports.
4. A business error produces a stable response, without SQL details or an internal stack trace in the public contract.
5. The same transition through the API and worker applies the same authorization and idempotency.
6. Exposed projections do not trigger additional queries during serialization.
7. The browser bundle contains neither server modules nor private credentials.

Port doubles trigger specific business cases. Adapter tests verify queries, constraints, transactions, and error behavior with the relevant engine. A “controller file exists” test evaluates none of these properties.

## 7. Decision and review

For each nontrivial feature, record a few lines covering:

- Entry points: HTTP, message, CLI, scheduling, or local interface.
- Use case and protected business invariant; authorization point.
- Modules owning the data; ports/adapters actually required.
- Transaction unit and recovery strategy, detailed in [Data and ORM](donnees-orm.md).
- Transport/business/persistence models kept together or separated, with the reason.
- Processes and containers actually required; cost of the chosen separation.
- Behavior and import checks demonstrating the boundary.

Examples of acceptable decisions:

| Request | Reasoned decision |
|---|---|
| “A simulation page without accounts” | Frontend only; simulation rule extracted if separately testable; no backend or ORM |
| “Catalog API with filters” | Thin transport, read service, SQL/ORM projection; no artificial aggregate to display a list |
| “A case submitted and then approved by another role” | Transition domain, approval service, transaction, and concurrency version; same use case from authorized entry points |
| “Large import from a partner” | Dedicated consumer/entry point, bounded processing, isolated external access, idempotency; worker only if duration or throughput justifies it |

An exception describes the sacrificed boundary, the constraint requiring it, the concrete risk, the control measure, and when the decision will be reviewed. It does not require creating new layers “just in case.”
