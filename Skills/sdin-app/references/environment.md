# Environment defaults

These are the user's configured defaults, not universal requirements. An
explicit location/organization supplied for the current app takes precedence.

| Item | Default |
|---|---|
| SDIN reference checkout | `/Users/mathisgalliano/Documents/Travail/SDIN/SDIN` |
| Reference remote | `git@github.com:Mindsept/SDIN.git` |
| Parent directory for new applications | `/Users/mathisgalliano/Documents/Travail/SDIN` |
| Organization for new application repositories | `Mindsept` — user-confirmed GitHub login |
| Visibility for a new app repository | Private unless explicitly requested otherwise |

Resolve the reference from the user's path or `SDIN_REPO` first. If this skill
is inside the reference checkout, its real enclosing repository is another
candidate; account for symlinks. Otherwise use the configured checkout above.
Verify README.md, AGENTS.md, `Skills/`, `td/core-platform/` and the Git remote
before treating a directory as this reference. Do not replace it with an
unrelated sibling checkout just because its name resembles SDIN.

Derive the app directory and repository name from the brief when unambiguous;
ask only if there is a collision or an identity that cannot be inferred. Do not
hard-code DocDesk or a previous app into reusable instructions. A new attempt
uses an empty destination and synthetic test data. Use a fresh conversation if
prior app answers/code are already in context; renaming a folder does not clear
conversation history. Inspect any existing port,
GitHub repository and platform-resource collision independently.

Authentication comes from the user's existing connectors, CLI or browser
session. A configured organization is not evidence that the active connection
can create repositories or operate the platform. Missing access is a concrete
blocker to report, not a reason to change owner or expose credentials.
