# Service choices and delivery decision — <application>

Status: <proposed / accepted design / partially verified / operated and measured>
Owner: <owner> · Review date: <YYYY-MM-DD> · Repository/commit: <identity>
Applicable policy: <local rules and architecture profile; approval authority if relevant>
Related architecture decision: <link or N/A> · Runbook: <link>

Replace placeholders. Remove sections that do not apply and explain material N/A choices. No unresolved placeholder represents a verified setting.

## Product and constraints

- User-facing outcome and consumers: <browser/mobile/API/operator/batch>.
- Durable facts and data owner: <facts; existing authority or app-owned>.
- Sensitivity/tenants/authorization: <who may perform each action>.
- Load/payload/data-size envelope: <observed/estimated/unknown, review trigger>.
- Loss, duplication, consistency and stale-age tolerance: <explicit values or unknown>.
- Workshop or operated deployment; target machine/network; maintainers: <facts>.
- Open questions that change a decision: <question, dependent choice, owner>; independent work: <what can proceed>.

## SLO and recovery contract

| Operation | Complete result / acknowledgment / first output | Measurement boundary and statistic | Target, window and workload | Error/degradation policy | Evidence |
|---|---|---|---|---|---|
| <operation> | <meaning> | <client/server; p99/hard deadline> | <value and envelope> | <policy> | <measured/proposed/etc.> |

For deferred work add completion deadline, queue wait, job loss/duplication tolerance and overload behavior. Record workshop server thresholds separately from product objectives; document any actual approved deviation. RPO: <value or unknown>. RTO: <value or unknown>. Backup/restore owner: <owner>.

## Service-use matrix

Use `used`, `not used`, or provisionally `undecided`; resolve required dependencies before claiming design acceptance. Keep a concise final table in the app README under the applicable local rules and link this longer record. Distinguish app runtime, provisioning, operator tooling, and platform-internal dependency; a service used by the platform is not automatically an app dependency.

| Service | Status and consuming process/role | Actual need / reason not needed | Data authority and scope | Simpler alternative and reason rejected | Revisit condition |
|---|---|---|---|---|---|
| PostgreSQL / pgvector | | | | | |
| Valkey | | | | | |
| SeaweedFS S3 | | | | | |
| OpenBao | | | | | |
| APISIX LLM gateway | | | | | |
| Temporal server | | | | | |
| Temporal UI | | | | | |
| Casdoor | | | | | |
| Umami | | | | | |
| Container registry | | | | | |
| Dozzle | | | | | |

Other service proposed: <why the existing platform/no-service option cannot satisfy the requirement; operation/cost/approval consequences>. Do not add a technology merely to fill this row.

## Decision record — repeat only for selected or disputed choices

**Choose <X> when <actual conditions>. Reject <Y/no service> because <missing capability or evidence>.**

1. Project evidence and applicable rule IDs: <source; local/team/proposed policy distinction>.
2. Consumer and endpoint: <host/browser/container distinction; protocol; validated SDK/runtime>.
3. Resource scope: <DB/user, bucket/key, Valkey prefix, secret path, namespace/task queue, OIDC client, analytics site or virtual key as applicable>.
4. Provisioning action and owner: <actual script/manual step; effects; idempotency limits; authorization already held or needed>.
5. Credentials and real access controls: <names/roles only, no values; known workshop exceptions>.
6. Integration: <transaction/cache TTL and invalidation/job ack and recovery/object authorization/etc.>.
7. Failure/recovery: <outage, timeout, restart, duplicate, partial write; fallback or fail-closed condition>.
8. SLO/capacity/cost consequence: <budget contribution; freshness/completion change; operating cost>.
9. Verification: <specific success and failure behavior, command/test, evidence level>.
10. Reconsider when: <measurable trigger, owner and next review>.

## Flow and consistency

<Describe or diagram the user's flow through only the selected services. Mark trust boundaries, authoritative writes, cache/projection updates, async admission/completion and data leaving the platform. Explain how partial cross-store failures are reconciled.>

## GitHub Actions and local delivery

| Concern | Decision and exact configuration/command | Actual evidence / remaining setup |
|---|---|---|
| Retained components and toolchain versions | | |
| Hosted PR validation, no shared platform | | |
| Lint/type/unit/integration/build/security gates | | |
| Trusted runtime workflow/ref and target | | |
| Runner owner, reachability and enforced access restriction | | |
| GitHub environment/protections/secret names | | |
| Artifact/registry, source SHA and digest identity | | |
| Provisioning and migration ownership | | |
| Cross-repository shared-host serialization | | |
| Deployment, readiness and smoke check | | |
| Previous compatible release and rollback/repair | | |

## Operating handoff and exceptions

- Health, SIGTERM, bounded retries/pools/queues, log/metric owner: <runbook sections>.
- Backup/restore, rotation, retention and scoped deprovision: <runbook sections>.
- Applicable local MUST rules met: <rule → evidence>; N/A rules: <rule → reason>.
- Exception if needed: <specific rule, necessity, alternatives, risk, compensating control, authority/status, expiry/review, exit plan>. Do not invent approval or treat an unknown policy as a granted exception.
- Evidence ledger: <inspected / proposed / syntax-checked / behavior-tested with doubles / integration-tested / measured>, each linked to actual evidence and date.
- Remaining actions: <owner, condition, evidence needed>. Design acceptance is not deployment or SLO certification.
