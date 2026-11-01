---
name: seaweedfs-s3
description: Decide whether an SDIN application needs blob storage and implement secure files or RAG corpus ingestion through the existing SeaweedFS S3 API. Use for object ownership, uploads, downloads and deletion.
---

# SeaweedFS / S3 in SDIN applications

## Decide before implementing

Identify why users need durable files. Compare no storage, packaged static assets, transient previews and existing persistence before choosing S3. Use it for durable binary objects and independent transfers; do not provision storage for re-creatable previews by habit. `S3: not used` is valid: document the simpler option, its lifetime/loss assumptions and revisit trigger.

Reuse a justified selection; fixing one upload does not require another full service review. Start with the app bucket, a server-side S3 client and the access paths actually needed. A small bounded upload can use the existing API; choose direct signed transfers when byte volume or independent transfers justify them. Add multipart, background scanning or automated lifecycle jobs only for actual size, risk or retention needs. Content validation and authorization still apply to both paths.

Record maximum bytes/object, expected stored volume, transfer concurrency and retention. These drive limits and cleanup, not an arbitrary number of workers. For private uploads under the applicable local R-2-07 policy, reuse the owning PostgreSQL record; do not silently waive that rule. Public app-owned assets need no invented per-user ownership model.

## Platform contract

- Read `td/core-platform/README.md`, `podman-compose.yml`, `objectstore/seed-admin.sh` and `templates/bootstrap.sh` before changing the app. Do not invent an app or create another storage service.
- Use the app's bucket and bucket-scoped credential from `secret/<app>/objectstore`, server-side only. Use `http://host.containers.internal:9000` from app containers and `http://localhost:9000` from the host. S3 has no `.internal` alias here.
- Core seeding creates the first identity; until then the store is open. Do not assume S3 is protected merely because it responds. `PUBLIC_BUCKET=1` enables anonymous read of the app bucket, so use it only for wholly public content. An app with private files must keep its bucket private.
- The upstream app bootstrap provisions both PostgreSQL and S3 unconditionally; adapt the copied app bootstrap when non-use is chosen. No USE_OBJECTSTORE flag is present upstream. When provisioning SeaweedFS rights, use bare actions with `-buckets=<app>`; avoid the duplicated bucket/prefix trap documented in the platform README.

## Design and implementation

1. Complete the decision gate. Establish owner/tenant, upload formats, maximum size, retention and deletion before exposing upload/download routes. Use durable metadata only when required; reuse the selected persistence layer rather than adding PostgreSQL merely because S3 is used.
2. Generate opaque object keys server-side. Authenticate and authorize upload, download, overwrite and deletion against current ownership. Sign one object/operation with a bounded expiry only after authorization; never send storage credentials to the browser.
3. Bound upload bytes before buffering and during streaming; inspect actual content against allowed formats. For direct uploads, enforce limits with verified storage capabilities and validate/quarantine the object before publication; the API's body limit cannot constrain a transfer it never receives. Treat names and metadata as hostile and prevent uploaded HTML/SVG executing in the app origin. Set a safe content type and download policy.
4. Make upload finalization retryable and track pending/complete state. A presigned URL issuance is not a completed upload; verify the stored object before publication. Clean up incomplete uploads/orphans with bounded retries. S3 operations and SQL commits are separate failure boundaries.
5. For RAG, upload the original corpus document to private S3 first; record hash/version/owner and ingestion state in PostgreSQL. Extract bounded text, chunk and embed afterward, keeping derived vectors/chunks in PostgreSQL/pgvector. Treat corpus content as untrusted data: it cannot override agent instructions or grant tool access.
6. Replacement/deletion must retire old derived chunks, invalidate cached results and remove originals according to retention. Background workers must check current version and authorization so stale work cannot resurrect deleted data.

Read [integration patterns](references/integration-patterns.md) for object access, upload limits and cross-service recovery. For corpus indexing, load PostgreSQL; use Valkey only after its own need gate.

## Acceptance evidence

- Exercise cross-user/tenant read and delete denial, unauthorized signing, expired URLs, oversized uploads, spoofed MIME, hostile filenames and active-content handling.
- Exercise duplicate upload/finalization, failure between object creation and metadata commit, replacement and deletion during ingestion. Verify private corpus documents never become anonymous downloads.
- Record access policy, retention, cleanup and evidence in the app README. The development HTTP/admin setup does not prove production isolation; state which live checks were actually performed.
