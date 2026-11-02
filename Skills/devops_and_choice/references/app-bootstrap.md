# Provision only the application's selected resources

Use this after the service-use decision, not as another architecture questionnaire.
The [TD bootstrap](../../../td/core-platform/templates/bootstrap.sh) provisions
PostgreSQL and S3 unconditionally. It remains unchanged. For a new consuming app,
[prepare_bootstrap.py](../scripts/prepare_bootstrap.py) produces a reviewed,
app-owned adaptation of that exact template. It never runs it, starts containers,
copies credentials, changes the core checkout or installs skills globally.

## Prepare the app copy

From the SDIN repository root, with Python 3.12+:

```sh
python3 -B Skills/devops_and_choice/scripts/prepare_bootstrap.py \
  --output /path/to/existing-app/bootstrap.sh
```

The destination directory must exist. An existing script is never overwritten;
generate a separate candidate and review its diff for an existing app. Output
inside `td/` or the selected core checkout is refused, including resolved symlinks.
`--platform /path/to/core-platform` locates an equivalent source checkout.
The source template's full normalized SHA-256 is pinned: if it changes, review
the source diff and update the adapter/tests together. Do not bypass that check.
The canonical OpenBao resolver is preserved verbatim rather than forked.

## Declare the retained resources

Add the applicable flags to the app's **existing** reviewed `app.env`. Keep the
service-use decision in its README; these flags implement that decision.
Example for a PostgreSQL-only app:

```sh
USE_POSTGRES=1
USE_OBJECTSTORE=0
LLM_VKEY=0
TEMPORAL_NS=0
ANALYTICS_SITE=0
PUBLIC_BUCKET=0
PROVISION=1
APP_SECRETS="postgres"
```

| Selected capability | Setting / operation | Created by the app bootstrap |
|---|---|---|
| Durable app records | `USE_POSTGRES=1` | App DB/role and `secret/<app>/postgres` |
| Persistent files | `USE_OBJECTSTORE=1` | App bucket/scoped identity and `secret/<app>/objectstore` |
| External AI | `LLM_VKEY=1` | App virtual key in the shared map and `secret/<app>/llm`; **no Temporal namespace** |
| Durable workflows | `TEMPORAL_NS=1` | App namespace and `secret/<app>/temporal`; **no DB/bucket/LLM key** |
| Product analytics | `ANALYTICS_SITE=1` | Existing targeted site helper and `secret/<app>/analytics`; no app DB/bucket |
| User login | Separate [OIDC helper](../../../td/core-platform/idp/onboard-oidc.sh) with the exact app callback | App client and `secret/<app>/oidc`; not implicitly enabled by another flag |
| Test personas | Separate [test-user helper](../../../td/core-platform/idp/seed-test-users.sh), only when requested for app tests | Personas and test-only secret; not production runtime credentials |
| Valkey | Configure app prefixes and limits from the [Valkey skill](../../valkey/SKILL.md) | No extra cache container, DB or bucket |
| OpenBao | Existing platform secret store, used only by selected resource steps | No app-specific OpenBao instance; runtime identity/policy remains separate |
| Dozzle / Temporal UI | Existing operator surfaces | No new app container or provisioning dependency |
| Registry | Existing registry, used during authorized image publication | No image build/push during bootstrap |

`USE_POSTGRES` and `USE_OBJECTSTORE` are supported by the **generated app copy**,
not upstream TD flags. All five resource flags default to `0`. Only literal `0`
or `1` is accepted, including for `PUBLIC_BUCKET`; an empty or misspelled value
fails before any platform command. `PUBLIC_BUCKET=1` requires object storage.
It grants anonymous read of that app bucket; setting it back to zero does not
revoke an existing grant. Review access changes explicitly with the S3 skill.

For Temporal-only, set only `TEMPORAL_NS=1` and `APP_SECRETS="temporal"`. For
analytics-only, set only `ANALYTICS_SITE=1`, its domain and `CORE_PLATFORM`, and
`APP_SECRETS="analytics"`. Preserve the app's existing OIDC/other secret names
when applicable. For no resources, all five flags are zero; execution is a no-op
without any Podman/OpenBao call. Prefer `PROVISION=0` for that lifecycle path.
The copied lifecycle's broad default secret list is not a resource inventory:
review it and its purge behavior for the actual app, especially an empty list.

## Preview before authorized application

```sh
# app.env is trusted shell configuration: inspect it before sourcing it.
set -a
. ./app.env
set +a
./bootstrap.sh --plan
```

This validates flags/app identity and lists resource/secret **names only**. It
does not probe the platform, read credentials, prove resources exist, infer
missing decisions or authorize provisioning. Keep credentials out of `app.env`.

The generated script accepts `--apply`, and **no arguments also applies** to
preserve the [app lifecycle contract](../../../td/core-platform/templates/app-lifecycle.sh).
Use it through the reviewed app lifecycle on the trusted host, under the existing
shared lifecycle lock. Do not call `start` to obtain a preview, run it from a PR
runner, or replace an existing adequate app CI. A standalone `--apply` invocation
does not acquire that lifecycle lock by itself.

OpenBao must be available before the first mutation. Missing selected analytics
helpers are checked before provisioning other resources. No provider call,
global seeding, OIDC onboarding, app migration, image publication or purge is
automatically added. Publishing an LLM key does **not** activate the APISIX
consumer: gateway regeneration remains a separately authorized operator action.

## Re-runs, partial state and failure

Healthy re-runs reuse the existing saved PostgreSQL password and S3 keys, bucket,
namespace and analytics site. Temporal/analytics may refresh their config secret;
this is not a promise of zero writes. Disabling a flag preserves existing data,
secrets and resources; it never deprovisions anything.

The adaptation also makes three concrete corrections in the **app copy**:

- Existing PostgreSQL DB/role without its saved password, or an existing bucket
  without its saved key: stop for restoration/reconciliation instead of rotating
  credentials implicitly. A failed SQL query or bucket listing stops the step. Public read is applied only
  after the bucket credentials have been created/reconciled.
- If a shared LLM map PATCH fails, the fallback can only create an absent map
  with `cas=0`; it cannot overwrite existing apps' keys. A conflict fails the run.
- The summary reports only selected resources, rather than claiming DB/S3 exist
  for every application.

There is no transaction spanning services and no automatic rollback. On failure,
inspect partial state, restore/reconcile the app's secrets and actual resources,
then retry under the same lock. Do not purge the core or generate replacement
credentials as a recovery shortcut. Retention changes and access revocation are
separate changes, not effects of turning off a flag.

## Verification and limits

[The regression suite](../../../ci/tests/test_bootstrap.py) generates the app copy
in a temporary folder and uses stateful command doubles. It covers all 32 subsets
of the five resource flags, no-op/preview, invalid flags/app names, repeat behavior,
partial-state refusals, failed reads, scoped public grants, shared key-map preservation,
failure ordering, source drift and destination protection. It is discovered by
the existing mandatory `ci/check.sh`; no platform-connected runner is needed.

These checks do not prove real permissions, secret-store error classification,
recovery after OpenBao state loss, effective private S3 access, SDK connectivity,
resource ownership or successful APISIX activation. The workshop's existing dev
credentials/transport remain dev limitations. Validate selected resources through
their service skills in the consuming app during the platform test phase.
