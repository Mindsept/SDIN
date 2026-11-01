---
name: temporal-operations
description: Inspect and diagnose an SDIN Temporal execution using Temporal UI, history and existing Worker logs. Use for a concrete run or a minimal operator handoff; a healthy human wait is not automatically an incident.
---

# Temporal operations sized to the question

Use the shared Temporal UI when the app has Temporal executions to inspect. A single-run investigation normally needs the UI and existing logs. Do not create an app dependency on the UI, an SDK for it, or a new monitoring stack to answer that question.

Reuse known application decisions. If Temporal is not selected, mark this operator integration N/A; another app may still use the shared UI. For a product-facing status page, use the authenticated app API and its chosen state source, not UI scraping.

## Context and entry points

Locate the app and the SDIN repository from their actual paths. In this repository, the Git root is `../..` from this skill. Inspect `td/core-platform/README.md`, the actual Compose configuration and app docs. Treat templates and stored examples as configuration evidence, not proof of deployed containers or completed CI runs.

Local defaults are UI `http://localhost:9233` (`temporal-ui.internal:8080` inside the container network), gRPC `temporal.internal:7233` for app containers and `localhost:7233` on the host. Confirm the environment before using them. The supplied dev service lacks production authentication/mTLS; use the deployment's authorized operator access.

## Follow the narrowest investigation

1. Capture environment, namespace, workflow ID and run ID. A closed run, retry or Continue-As-New may lead to another run with the same workflow ID. If absent, check start acknowledgment, filters, visibility delay and closed-history retention.
2. Read the status, pending work and relevant event history. Compare elapsed time to the actual deadline or expected completion, including intentional human waits. A `Running` status alone is not evidence of failure.
3. Use [diagnostic-matrix.md](references/diagnostic-matrix.md) for the observed symptom. Inspect the relevant Worker queue/build and bounded logs only as needed. Pending Activity details may expose retry attempts that are not individually present in history.
4. Stop once the question is answered by evidence: expected wait, identified cause, or a specific missing observation. Report the execution identity, decisive event/pending state, conclusion and next action. Reserve a full incident report for a real incident.

UI downtime does not by itself mean Temporal or the app is unavailable; do not add it to business readiness checks. Workflow history and existing logs suffice for an occasional diagnosis. If recurring operational objectives require queue-age/completion alerts or retained metrics, first reuse existing instrumentation; add only the missing measurement, retention and alert. Dozzle is an optional existing log viewer, not a prerequisite.

## Interventions and handoff

A diagnosis request is read-only. For an authorized Signal, cancellation, reset, termination or retry, identify the exact run and business effect, check idempotency and use the app's normal approval/audit path. Reuse authorization already given; do not create an extra approval round for routine authorized work. A reset/new execution can repeat effects; termination does not run Workflow cleanup. SDK replay testing is different from restarting/resetting a live run.

Keep payloads and credentials out of reports. For app onboarding, record only the UI location, namespace/queue, how to find a run, and the expected waits/failures. Validate this with one controlled scenario when the environment is available; no live environment means an unexecuted runbook, not a successful test.

Sources: [Event history](https://docs.temporal.io/encyclopedia/event-history), [Activity failures](https://docs.temporal.io/encyclopedia/detecting-activity-failures), [Visibility](https://docs.temporal.io/visibility).
