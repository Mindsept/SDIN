# Environment defaults

These are the user's configured defaults. Explicit settings for the current
application take precedence.

| Item | Default |
|---|---|
| SDIN reference checkout | `/Users/mathisgalliano/Documents/Travail/SDIN/SDIN` |
| Reference remote | `git@github.com:Mindsept/SDIN.git` |
| Parent directory for new applications | `/Users/mathisgalliano/Documents/Travail/SDIN` |
| Organization for new application repositories | `Mindsept` — user-confirmed GitHub login |
| Visibility for a new app repository | Private unless explicitly requested otherwise |

Resolve the reference from the user's path or `SDIN_REPO` first, then the
skill's enclosing SDIN checkout if applicable, otherwise the default above.
Verify `README.md`, `AGENTS.md`, `Skills/`, `td/core-platform/` and the remote.
If unavailable, locate or clone the configured reference before using its routes.

Derive the app directory from the brief. Inspect an existing destination before
using it; an archived sibling is not the current app. For an explicitly fresh
attempt, use an empty destination without importing previous app code or data.
