# Application repository

Use this procedure when building an application, in addition to the reference
assistance's delivery guidance. That guidance covers CI, secrets, runners,
release and verification; this file covers the repository destination.

- Inspect the application's actual Git root and remotes. Reuse its matching
  repository, preserving its history and visibility. A parent repository or
  the SDIN reference checkout is not the application repository.
- For a new repository, derive an unambiguous name from the brief and use the
  owner and visibility from [the environment defaults](environment.md).
  `Mindsept` is already user-confirmed. Check that exact destination before
  creation; an access error does not establish that a private repo is absent.
  Resolve a name collision without overwriting an existing repository.
- Use the existing authenticated connector, CLI or browser session with creation
  rights. If access is missing, report it rather than changing owner or asking
  for credentials in chat. Create the repository and configure the app remote.
  After a timeout, inspect the same destination before retrying.
- Read back the owner, name, URL and visibility, then follow SDIN's existing
  delivery route for publishing and CI. Apply the organization's applicable
  protection policy when permitted and verify the actual settings; report any
  access limitation. Report the verified application URL and branch.
