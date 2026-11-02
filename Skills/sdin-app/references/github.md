# Application repository in Mindsept

Read this when building an application or handling its repository. Merely
reviewing a brief, preparing a skill or running a dry evaluation creates none.

Use the exact organization from the environment defaults or the user's explicit
override. `Mindsept` is already confirmed; do not ask again or substitute the
personal account, a similarly named organization or the SDIN reference repo.

## Establish or reuse the destination

- Inspect the app directory, its actual Git root and remotes. Avoid accidentally
  publishing a parent repository or archived app. Reuse the matching existing
  repository; preserve its history, visibility and current work.
- For a new app, choose an unambiguous product-based repository name. Inspect
  that exact owner/name before creation. A 403 or ambiguous 404 does not prove
  that a private repository is absent. If an existing destination belongs to a
  different app, resolve that collision rather than overwriting or force-pushing.
- Verify the active connection/account can use the organization. Prefer a
  suitable connected tool; use authenticated GitHub CLI or the existing browser
  session if the connector lacks creation rights. Explain a real access blocker
  and continue useful local work. Do not request tokens/passwords in chat.
- Create a **private** repository unless the user explicitly chooses public.
  Keep the owner explicit. Configure the application's remote, then read back
  the owner, name, URL and visibility. If creation times out, inspect the exact
  destination before retrying; never create another name/account as a workaround.

## Publish and verify the application

Before committing/pushing, review the actual file set and ignore runtime data,
secrets, logs, dependency caches and generated outputs as appropriate. Synthetic
test fixtures may be versioned deliberately. Never publish the reference
checkout, archived app data or credentials as part of the new application.

Use the reference assistance's delivery guidance to adapt CI to the **app's**
real manifest, selected components and useful tests. Do not copy SDIN's own
repository test suite into a business app or run PR code on the shared host.
Publish reviewed code and verify the remote revision and actual GitHub checks.
Use a feature branch/PR for changes to an established app. Initializing an empty
repository does not authorize overwriting an existing main branch.

Apply the organization's required checks/protection policy when access permits,
using actual check names from the app workflow. Report settings that could not
be applied; YAML alone does not prove branch protection. Never bypass failed
checks. Creating an app does not imply authority to merge an existing PR, grant
broader access, change repository visibility or delete an existing repository.

Report the verified repository URL and branch, CI result, and any pending GitHub
or platform action separately. If no repository could be created, say so.

Official mechanics, to recheck when needed: [GitHub CLI repository creation](https://cli.github.com/manual/gh_repo_create)
and [GitHub repository API](https://docs.github.com/en/rest/repos/repos#create-an-organization-repository).
