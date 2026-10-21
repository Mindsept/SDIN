# Official sources for stack choices

Documentation consulted: **October 14, 2026**. This register supports [langages-frameworks.md](langages-frameworks.md). The links were consulted; this constitutes neither a benchmark, an integration test of the frameworks with the repository, nor certification of support for a specific version.

The **capabilities** below come from maintainers. Contextual preferences, rules L01–L18, cost tradeoffs, proposed usage limits and admission conditions are the **harness policy**, inferred from these capabilities and platform needs. They are not presented as vendor prescriptions. No promotional throughput, RAM or startup figures are reused as application performance.

## Local foundation to reread before a decision

| Repository source | What it establishes | What it does not establish |
|---|---|---|
| [`td/core-platform/README.md`](../../../td/core-platform/README.md) | Exposed services and contracts; the CCoE rules remain to be written | An immutable catalog of authorized languages |
| [`templates/podman-compose.yml`](../../../td/core-platform/templates/podman-compose.yml) | TS/Vite frontend, TS/Bun API/worker structure; unused services must be removed | An obligation to systematically deploy all three services |
| [`templates/gitlab-ci.yml`](../../../td/core-platform/templates/gitlab-ci.yml) | Bun gates and build; example of a Rust service under a critical-path waiver | Automatic validation of a Python/Java/Go service by those same gates |
| [`templates/README.app.md`](../../../td/core-platform/templates/README.app.md) | Documented architectural decisions, libraries and waivers | Approval of a waiver simply because its section is filled in |
| [`requirements.md`](../../../td/core-platform/requirements.md) | Workshop prerequisites and Bun tooling; optional Rust profile illustrated | Availability of every compiler, GPU and SDK on the current workstation |

## Web, frontend and TypeScript/JavaScript

| ID | Official source consulted | Relevant fact retained; consequence to verify in the application |
|---|---|---|
| S01 | [Bun — Node.js compatibility](https://bun.sh/docs/runtime/nodejs-compat) | Compatibility documented API by API with differences; test selected SDKs/modules, do not infer equivalence across all npm packages |
| S02 | [Node.js — Don't block the event loop](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop) | Blocking the event loop and pool affects other work; bound or isolate blocking computation |
| S03 | [Fastify — Validation and Serialization](https://fastify.dev/docs/latest/Reference/Validation-and-Serialization/) | Schemas for validation/serialization; design boundaries and contracts without inventing a throughput advantage |
| S04 | [NestJS — Documentation](https://docs.nestjs.com/) | Server framework and modular architecture; the benefit for a team remains a local decision |
| S05 | [Hono — Documentation](https://hono.dev/docs) | Web Standards-based framework with several runtimes; verify target runtime capabilities and plugins |
| S06 | [Express — Using middleware](https://expressjs.com/en/guide/using-middleware/) | Middleware-based organization; validation/error policy to complete according to the product |
| S07 | [React — Creating a React App](https://react.dev/learn/creating-a-react-app) | Several creation/tooling approaches; do not confuse React with a mandatory server runtime |
| S08 | [Vite — Deploying a Static Site](https://vite.dev/guide/static-deploy.html) | Building and deploying static artifacts; `vite preview` is not this harness's operations strategy |
| S09 | [Next.js — Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components) | Boundaries between server/client components; protect secrets and server dependencies at this boundary |
| S10 | [Astro — Islands architecture](https://docs.astro.build/en/concepts/islands/) | Targeted interactivity through islands; decide what actually requires JavaScript or a server |
| S11 | [Vue — Introduction](https://vuejs.org/guide/introduction.html) | Component-based UI framework with several adoption modes; choose the mode according to the product |
| S12 | [Angular — Overview](https://angular.dev/overview) | Application framework/tooling; weigh the value of conventions against the team and existing system |
| S13 | [SvelteKit — Introduction](https://svelte.dev/docs/kit/introduction) | Svelte application framework; evaluate its rendering mode and adapt deployment/contracts |

## Python and scientific computing

| ID | Official source consulted | Relevant fact retained; consequence to verify in the application |
|---|---|---|
| S14 | [Django — At a glance](https://docs.djangoproject.com/en/stable/intro/overview/) | Integrated ORM, migrations, administration, routing and templates; potential back-office benefit without a DB obligation |
| S15 | [Django — Asynchronous support](https://docs.djangoproject.com/en/stable/topics/async/) | Async support with constraints and sync/async adaptation; check middleware, DB operations and selected version |
| S16 | [Django REST Framework](https://www.django-rest-framework.org/) | Serialization, views and auth/permission policies for APIs; select extensions according to need |
| S17 | [FastAPI — Concurrency and async/await](https://fastapi.tiangolo.com/async/) | Distinction between I/O concurrency and parallelism; decide where blocking code executes |
| S18 | [FastAPI — Features](https://fastapi.tiangolo.com/features/) | Data contracts, validation and API documentation; does not remove the need for persistence/auth/business architecture |
| S19 | [Flask — Using async and await](https://flask.palletsprojects.com/en/stable/async-await/) | Limits of the async model with WSGI and extensions; an `async def` alone does not transform the execution topology |
| S20 | [Python — concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html) | Executors with distinct concurrency models; check version and library limits |
| S21 | [scikit-learn — Parallelism and resource management](https://scikit-learn.org/stable/computing/parallelism.html) | Interaction between job parallelism, OpenMP and BLAS; control thread oversubscription |
| S22 | [Streamlit — Client-server architecture](https://docs.streamlit.io/develop/concepts/architecture/architecture) | Sessions and server/client architecture; size access and exposure according to context |
| S23 | [Streamlit — Caching overview](https://docs.streamlit.io/develop/concepts/architecture/caching) | Reruns and data/resource caching mechanisms; examine sharing, memory and isolation |

## JVM, Go, .NET and Rust

| ID | Official source consulted | Relevant fact retained; consequence to verify in the application |
|---|---|---|
| S24 | [Spring Boot — Documentation](https://docs.spring.io/spring-boot/index.html) | Integrated configuration and operational features; retain only useful starters and services |
| S25 | [Spring Framework — WebFlux overview](https://docs.spring.io/spring-framework/reference/web/webflux/new-framework.html) | Reactive/non-blocking model and relationship to MVC; decide based on the I/O chain and team |
| S26 | [Oracle — Virtual Threads](https://docs.oracle.com/en/java/javase/25/core/virtual-threads.html) | Virtual-thread concurrency and limits; the JDK 25 document is a source for the mechanism, not a required version |
| S27 | [Quarkus — Building a native executable](https://quarkus.io/guides/building-native-image/) | Native compilation procedure/constraints and tests; measure full build/execution cost |
| S28 | [Micronaut — Framework](https://micronaut.io/) | Compile-time injection and native-image options; do not convert marketing examples into SLOs |
| S29 | [Ktor — Create and run a project](https://ktor.io/docs/server-create-a-new-project.html) | Composable Kotlin server and configuration choices; validate plugins and packaging |
| S30 | [Go — net/http](https://pkg.go.dev/net/http) | Standard-library HTTP client/server API; configure lifecycle, timeouts and limits |
| S31 | [go-chi/chi — maintainers' repository](https://github.com/go-chi/chi) | Composable router compatible with `net/http`; the domain still needs structure |
| S32 | [gin-gonic/gin — maintainers' repository](https://github.com/gin-gonic/gin) | Routing, binding and middleware; no comparative README figures used in the policy |
| S33 | [ASP.NET Core — APIs overview](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/apis) | Minimal APIs and controller-based APIs; choose conventions according to responsibilities |
| S34 | [.NET — Worker Services](https://learn.microsoft.com/en-us/dotnet/core/extensions/workers) | Background-service hosting and lifecycle; adapt to the repository's job contracts |
| S35 | [.NET — Native AOT](https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/) | Native compilation and restrictions; test final dependencies before adoption |
| S36 | [Rust Book — Ownership](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html) | Ownership as a language mechanism; neither a benchmark nor a guarantee of freedom from application defects |
| S37 | [Axum — crate documentation](https://docs.rs/axum/latest/axum/) | HTTP framework and ecosystem integration; check compatibility for the selected version |
| S38 | [Actix Web — Documentation](https://actix.rs/docs/) | Rust HTTP framework; alternative conditional on libraries and skills |
| S39 | [Rust — Embedded devices](https://rust-lang.org/what/embedded/) | Embedded ecosystem; check target, toolchain and libraries without presuming compatibility with every piece of hardware |

## Other ecosystems and clients

| ID | Official source consulted | Relevant fact retained; consequence to verify in the application |
|---|---|---|
| S40 | [Laravel — Directory structure](https://laravel.com/docs/12.x/structure) | Separation of responsibilities and organization of HTTP/console entry points; documentation-version URL, not a prescribed version |
| S41 | [Symfony — Create your first page](https://symfony.com/doc/current/page_creation.html) | Routes, controllers, templates, services and directories; retain these conventions while separating business logic and transport |
| S42 | [Rails — Getting Started](https://guides.rubyonrails.org/getting_started.html) | Application, data and controller conventions; compare total cost against team experience |
| S43 | [Phoenix — Overview](https://phoenix.hexdocs.pm/overview.html) | Web framework in the Elixir ecosystem; concrete architecture to size and test |
| S44 | [Scala — Language website](https://www.scala-lang.org/) | Ecosystem and interoperability; the language does not require a Spark cluster |
| S45 | [Apache Spark — Documentation](https://spark.apache.org/docs/latest/) | Engine and interfaces; check operations and distributed-processing need before adding it |
| S46 | [R Project — What is R?](https://www.r-project.org/about.html) | Statistical computing language/environment; suitability depends on required methods and libraries |
| S47 | [Posit Shiny — Welcome to Shiny](https://shiny.posit.co/r/getstarted/shiny-basics/lesson1/) | Building Shiny interfaces; not proof of multi-tenant or load capacity without additional design |
| S48 | [Android — Guide to app architecture](https://developer.android.com/topic/architecture) | Recommendations for UI/data separation and mobile organization; adapt offline and synchronization |
| S49 | [Apple — SwiftUI](https://developer.apple.com/swiftui/) | UI framework in Apple's ecosystem; the backend may remain in another stack |
| S50 | [Flutter — Architectural overview](https://docs.flutter.dev/resources/architectural-overview) | Architecture and cross-platform targets; validate actually required plugins/capabilities |
| S51 | [React Native — Get Started](https://reactnative.dev/docs/environment-setup) | Native/cross-platform creation approaches; check native dependencies and distribution |
| S52 | [WG14 — C Committee](https://www.open-std.org/jtc1/sc22/wg14/) and [WG21 — C++ Committee](https://www.open-std.org/jtc1/sc22/wg21/) | Standardization references; provide no conclusion about the performance or suitability of a particular application |
| S53 | [Temporal — Develop](https://docs.temporal.io/develop) | Official SDK entry point; check language, runtime, versions and replay constraints when used |

## Sources checked for the explicit decision paths

The language and framework comparisons in sections 3–15 remain contextual harness recommendations. These additional checks support particular capability distinctions; they do not establish that one candidate will meet the application's SLO without a representative test.

| ID | Official source consulted | Relevant distinction retained |
|---|---|---|
| S54 | [Nest — Fastify adapter](https://docs.nestjs.com/techniques/performance) | Nest can use Fastify as its HTTP provider; adapter-specific middleware/packages must be checked. The advertised benchmark comparison is deliberately not used |
| S55 | [Django — Admin site](https://docs.djangoproject.com/en/stable/ref/contrib/admin/) | Admin targets trusted internal model management; a process-centric user interface may need custom views. Its mere presence cannot be counted as a complete product UI |
| S56 | [Hono — Web Standards](https://hono.dev/docs/concepts/web-standard) | Use of standard Web interfaces supports a concrete interoperability criterion; validate all target-runtime dependencies separately |
| S57 | [Laravel — Service container](https://laravel.com/docs/12.x/container) | Laravel has dependency injection/service-container facilities; DI is not a capability unique to Symfony |
| S58 | [Symfony — Service container](https://symfony.com/doc/current/service_container.html) | Container and reusable components support explicit service composition; compare actual reuse and team conventions with Laravel |
| S59 | [Phoenix LiveView — lifecycle](https://hexdocs.pm/phoenix_live_view/Phoenix.LiveView.html) | Connected live processes, state and interaction lifecycle require evaluation of connection loss, server capacity and network latency |

Also rechecked S03 (Fastify validation/serialization), S17 (FastAPI concurrency), S19 (Flask async), S25 (Spring MVC/WebFlux applicability), S33 (ASP.NET API models), S37 (Axum/Tokio/Tower integration) and S38 (Actix Web versus the separate actor framework). Flask async does not by itself increase per-worker request concurrency or provide durable background execution. Spring's guidance favors assessing blocking dependencies and actual concurrent I/O needs rather than assuming a reactive rewrite makes computation faster. ASP.NET supports both endpoint and controller models; choose required features and maintained conventions, not a simplistic application-size cutoff.

## Maintaining recommendations

Check the version actually selected, its security maintenance and dependency compatibility. The `latest`, `stable` and `current` URLs change; their presence in this register does not authorize an automatic upgrade. Some consulted pages redirected to a version; no version displayed by this research was converted into a harness requirement.

Verified entry points for maintenance policies: [Node.js — releases](https://nodejs.org/en/about/previous-releases), [Django — release process](https://docs.djangoproject.com/en/stable/internals/release-process/), [.NET — releases and support](https://learn.microsoft.com/en-us/dotnet/core/releases-and-support). For other stacks, read the official policy associated with the candidate version during the admission study. Do not describe a runtime as LTS or supported without this check.

If a link becomes unavailable, state that its capability is no longer reverified and find the corresponding official documentation; do not replace the gap with blog rankings. The official chi and Gin websites did not provide usable content during this pass: their maintainers' repositories were consulted instead. The Micronaut `latest` documentation route only returned a redirect; the project's official website was used to verify general capabilities. The C/C++ pages identify the standards; selection recommendations for systems/native development are explicitly proposed tradeoffs, not facts demonstrated by those pages.
