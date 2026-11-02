---
name: sdin-app
description: Build or evolve an application from a product brief using the SDIN platform and its existing decision assistance, including the application's GitHub repository. Use for an app intended to consume SDIN, not for unrelated development or changing the shared platform.
---

# Build an application with SDIN

Take ownership of the supplied repository and infrastructure, then base the
application's decisions on the assistance already present. The user's brief is
the product specification. This skill supplies the entry point and delivery
context; the existing guides remain the authority for architecture and services.

## Establish the working context

Locate the reference checkout and application using [the environment defaults](references/environment.md),
respecting any explicit user override. Read the reference README and AGENTS.md,
inspect the actual infrastructure and follow their relevant routes. Read a
specialist's files directly if the harness does not expose it as an installed
skill. Do not install every service skill or preload the entire catalog.

Keep SDIN, its assistance and `td/` read-only during application work. Implement
in the application's separate directory/repository. Inspect existing work before
creating anything; a parent repository, archived sibling or similarly named app
is not automatically the application to resume. Do not copy its implementation,
data or previous test answers into a fresh attempt unless requested. A directory
rename does not release ports, resource names or running processes.

Record the reference commit used. Do not reset, pull over local changes or
silently update the reference during a comparison run. If no usable checkout is
available, obtain its location or prepare a separate clone of the configured
reference; an access failure is not permission to invent platform contracts.

## Deliver the requested application

Use the existing assistance to clarify consequential gaps, decide, implement
and verify. Reuse known answers and justified choices. Keep nonblocking
assumptions visible and ask only questions that change the product or its
correctness, security, operating commitments or actual execution target.

Let the brief and inspected contracts drive the stack, services, application
structure and useful checks. Do not substitute an isolated demonstration or
test double for a requested platform integration without reporting the gap.
Identify any missing platform capability and address it in the application
where appropriate; changing shared infrastructure needs its own authorization.

For application creation, set up or reuse the dedicated GitHub repository using
[the repository procedure](references/github.md). This is part of the build
workflow, not a request to create a repository while merely inspecting a brief
or editing this skill. Preserve an existing app's valid repository and workflow.

Implement and run meaningful local checks without repeated permission requests.
For provisioning and runtime integration, follow the existing assistance's
bootstrap/lifecycle guidance, inspect current state, and establish the exact
app resources and target. Reuse authorization already provided; if shared-host
mutation or its scope is not authorized, present the concrete plan and request
only that missing authorization while continuing independent work. Paid calls,
global reseeding, destructive cleanup and changes to other apps are not implied
by choosing a service or invoking this skill.

When access, tools or a provider are unavailable, identify the specific blocker,
prepare what can be verified locally and state the next action. Never fabricate
credentials, a repository, a successful provisioning run or a deployment.

## Leave a usable result

Use the app's existing documentation for the chosen services and reasons,
applicable guide references, setup and repeatable verification. Keep source
configuration, tests with doubles, real platform checks and measured objectives
distinct. Preserve the brief's commitments and explain any proposed compromise.

Finish with the application location, verified GitHub URL/branch, how to run it,
checks actually executed, platform integration status and concrete remaining
gaps. Keep harness/model details when available for a comparison run; do not
invent unavailable metadata or claim identical results across models.
