---
name: sdin-app
description: Build or evolve an application from a product brief using the SDIN platform and its existing decision assistance, including the application's GitHub repository. Use for an app intended to consume SDIN, not for unrelated development or changing the shared platform.
---

# Build an application with SDIN

Take ownership of the reference repository and supplied infrastructure, then
use the existing assistance to realize the user's application brief.

1. Locate SDIN and the application using [the environment defaults](references/environment.md).
   Read the reference's `README.md` and `AGENTS.md`, then follow their routes.
   Their architecture, service, delivery and bootstrap guidance remains the
   authority; this launcher adds no parallel decision process. If the harness
   does not expose a routed skill, read its files in the reference checkout.
2. Work in the application's separate directory/repository. Keep the SDIN
   reference, its assistance and `td/` read-only during application work.
   Record the reference commit used; keep it stable during a comparison run.
3. When building the application, set up or reuse its dedicated GitHub repository
   using [the repository procedure](references/github.md). Reviewing a brief or
   editing this skill alone does not trigger repository creation.

Clarification, implementation, CI, provisioning and verification follow the
existing assistance's applicable routes, without restating their instructions here.
