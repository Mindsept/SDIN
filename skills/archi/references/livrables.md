# Deliver an actionable decision

## 1. Match the output to the request

| Request | Deliverable |
|---|---|
| "Django or FastAPI for this need?" | Short applied comparison: conditions that favor the selected option, why the alternative loses, relevant SLO consequence, evidence needed, and what would reverse the choice; no repository generation |
| Complete new architecture | Markdown decision document + JSON contract + proposed directory tree + validation plan + any waivers |
| Application review | Findings sourced by file/line, severity and impact, declared versus actual deviations, priority fixes; no automatic rewrite |
| Migration | Migration ADR, compatible steps, evidence/baseline, rollback, and condition for removing the old path |

For a complete new design, use the application's established architecture directory. Otherwise use `docs/architecture/decision.md`, `docs/architecture/architecture.json`, and `docs/adr/` for decisions that warrant a history. Do not overwrite an existing document or move documentation without a need. The diagrams already present in this repository are not an architecture decision document for a future application.

## 2. Minimum document contents

Use [the decision template](../assets/decision-architecture.md), then remove irrelevant sections **with a justified N/A entry in the matrix**, without inventing features to fill an outline.

1. Product, users, user flows, and exclusions.
2. Provenance: brief, code, platform files, and technical documentation; policy profile and context.
3. Questions asked, answers, assumptions, and blocking unknowns.
4. Architectural style, components, trust boundaries, and ownership; explicit conditions selecting topology, internal pattern, and execution mode, with rejected alternatives.
5. Language/runtime/framework per component; applied head-to-head reasoning, costs, required evidence, and review conditions.
6. Concrete directory structure and dependency rules; example execution path.
7. Data access, ORM/SQL, migrations, and transactions; explicitly state when there is no database.
8. SDI services used and not applicable, addresses/conventions, provisioning, and adaptations.
9. API/job/workflow contracts and authorization; errors, recovery, and versioning.
10. Per-operation response-time SLOs or explicit absence, measurement boundaries and result semantics, load/window/failure policy, latency allocation, resulting architectural strategy, compute budgets, current evidence, tests, and operations.
11. Deviations and waivers; actual decision-maker and expiry for approved waivers.
12. Implementation plan limited to the need, next test, and validation status.

For each major decision: **project condition → choice → why the nearest alternative loses → SLO consequence → cost avoided/accepted → evidence → review trigger**. Name the relevant comparison rule or pattern branch and apply it; a copied technology catalog does not satisfy this requirement. Detailed decisions belong in the document; JSON checks invariants without copying all the prose.

For each critical operation, include the short decision record in [SLO-driven strategy](slo-strategy.md). If no product SLO exists, record that fact and any applicable course target or provisional assumption. An unmeasured design must show its next test, not an invented passing result. A known feasibility conflict or unknown full-result-versus-acknowledgment requirement remains unresolved until clarified or remedied.

## 3. Statuses without a false green light

- **Draft (`draft`)**: exploratory decision, blocking question, or missing decisive evidence. A `draft` can be syntactically valid; that is not acceptance.
- **Ready for review (`ready`)**: fields completed, needs clarified, choices justified, and no blocking unknown declared. This is neither instructor approval nor a production status.
- **Human acceptance**: recorded in the document/ADR with person, date, scope, and evidence. The v1 schema has no `approved` status for the overall decision.
- **Pending waiver**: recorded in the document, not in `waivers` as though approved. If the solution depends on it, record a blocking unknown and retain `draft`.

Do not confuse "not tested" with "compliant." Documentary validation, a simulated test, and a real test are three different forms of evidence.

`ready` can describe a reasoned design with planned performance tests; label the SLO evidence `proposed`, `estimated`, `measured within envelope`, or `violated` separately. It must not conceal a known incompatible deadline. The v1 validator cannot inspect the quality of these arguments or certify latency.

## 4. JSON contract and commands

Read [the machine-readable contract](contrat-machine.md) and adapt [the example](../assets/architecture.example.json). The schema rejects unknown fields: keep details outside the schema in the human-readable document. Record SLO requirements in `requirements.constraints`, provisional targets in `assumptions`, unresolved questions in `unknowns`, and their consequences in architecture/component rationales. Do not add an unsupported `slo` key or misuse `framework`, `platform_services`, or `waivers` to hide an unmodeled extension.

```bash
# From this repository's root; replace the date with the review date.
python3 -B skills/archi/scripts/validate_architecture.py \
  /path/to/app/docs/architecture/architecture.json --as-of YYYY-MM-DD

# Once the implementation and its paths exist:
python3 -B skills/archi/scripts/validate_architecture.py \
  /path/to/app/docs/architecture/architecture.json \
  --as-of YYYY-MM-DD --repo /path/to/app

# Check the validator when modifying the skill:
python3 -B -m unittest discover -s skills/archi/scripts -p 'test_*.py'
```

`--repo` must not point to the platform by default: it identifies the application whose paths are being checked. A hypothetical example must not pass this check without real files. The script is read-only and runs neither application code, builds, nor containers.

## 5. Example skill invocation

"Use `$archi` to design an internal case-management portal on the SDI platform. The team knows Python, wants a back office, and does not use ML; compare Django/DRF with FastAPI. Ask the missing questions and deliver a decision, directory tree, and verifiable contract."

Do not automatically answer Django solely because Python was mentioned: check back-office needs, volume, real-time requirements, existing systems, course policy, and OIDC integration. Do not propose a waiver if the broader profile has already been authorized.

## 6. Completing the task

Present the files created, the main choices and applied conditions, the SLO-to-strategy mapping and evidence status, remaining questions, and checks actually executed. Do not recite the entire catalog. Do not install the skill globally, start the platform, or generate business code without a corresponding request.
