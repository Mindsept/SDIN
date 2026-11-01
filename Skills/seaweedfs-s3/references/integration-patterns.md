# SeaweedFS / S3 agent guide

Use these patterns when designing, implementing, reviewing or debugging storage
of files, media, exports or other object payloads. Use the platform sources named in the skill entrypoint for current configuration.
Assume uploaded content and filenames are hostile, and users must not be able
to read one another's private objects.

## Platform contract

- SeaweedFS exposes an S3-compatible API on port 9000 and a dev filer browser
  on 9001. From an app container, use
  `http://host.containers.internal:9000`; from the host, use
  `http://localhost:9000`. There is no `.internal` alias: S3 is modelled as an
  external/cloud-style service.
- Each app owns one bucket and one credential scoped to that bucket. Runtime
  credentials live at `secret/<app>/objectstore`; never use `platform-admin`.
- The store starts open until the first S3 identity is created. Core seeding
  must happen before app traffic. Public read is opt-in and bucket-scoped via
  `PUBLIC_BUCKET=1`.
- This workshop setup uses HTTP and development credentials; do not present it
  as a production security configuration.

## Gate 0: is object storage needed?

Before adding S3 code, identify a user-visible need for durable binary objects
that must be shared, retained, downloaded independently, or exceed a reasonable
database-row size. Consider no storage first for transient previews or
re-creatable assets. For small structured data, use PostgreSQL; for static
build-time assets, package them with the frontend. Reuse an existing store if
it meets the need. Choose S3 when object lifecycle, independent transfer, or
size makes it the lighter fit.

If S3 is not needed, do not provision a bucket/key, add an S3 SDK or create
upload endpoints. Record `S3: not used` in the app README, the simpler approach,
and a concrete revisit trigger. Non-use is a valid outcome.

## Direct transfer is conditional, not a default SDK recipe

For small infrequent uploads, a bounded streaming API path may be sufficient.
For direct browser transfers, sign the browser-reachable endpoint; do not rewrite
the signed host/path afterward. Container endpoints are not automatically usable
by a browser on another machine. Verify the deployed S3 compatibility and CORS.

A signed PUT does not inherit the API's body limit and is not inherently single-use.
Use verified storage-side limits where available; otherwise use the bounded API
path when a hard pre-upload bound is required. Keep direct uploads private/pending,
verify size and actual content before publication, and clean rejected objects.
Prevent reuse of a still-valid upload URL from replacing an already validated
object: use a protected final key/version or another verified immutability control.
Do not assume a HEAD request validates the actual file content.

The AWS [presigned URL contract](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)
describes reusable bearer URLs and overwrite semantics; verify the actual SeaweedFS
version's support instead of assuming every AWS policy feature exists there.

## Agent workflow

1. Complete Gate 0 and record the service decision before implementation.
2. Store object bytes in S3 and keep their stable object key, owner,
   authorization and business metadata in the app's selected durable store
   (PostgreSQL for RAG). Generate opaque keys
   server-side; never use a raw user filename as the authorization key.
   For RAG, upload the original corpus document here before extraction or
   embedding; S3 is the durable source file, while chunks and vectors belong in
   PostgreSQL/pgvector.
3. Use only the app bucket and its scoped credential. Design app-owned key
   prefixes so retrieval and cleanup do not require scanning the whole bucket.
4. Authorize every upload, download, overwrite and delete against the owner or
   tenant record in that durable store. Do not expose the bucket or accept an object key
   as proof of access. Issue a short-lived, single-object signed URL only after
   the server has checked the user's authorization.
5. Apply a hard request/body size limit before buffering. Validate the actual
   content (not only the client MIME header or extension), allowlist supported
   formats and assign a safe content type. Stream or use multipart upload when
   warranted; clean up incomplete multipart uploads.
6. Treat filenames and metadata as untrusted: normalize/discard path
   components, escape them when displayed and do not reflect raw values into
   headers or HTML.
7. Define overwrite, retention, deletion and recovery behavior. On account or
   record deletion, remove dependent private objects or enqueue retryable
   deletion; do not orphan them silently.
8. Make writes retry-safe. SQL and S3 do not share a transaction: model pending
   and completed state, then provide retry/compensation for partial failures.
9. Load endpoint and credentials from app runtime configuration and
   `secret/<app>/objectstore`. Never log keys, signed URLs or object contents.
10. Separate public assets from private user uploads. `PUBLIC_BUCKET=1` exposes
   the bucket's read surface; it is not a shortcut for authenticated downloads.
11. Test unauthorized cross-user reads/deletes, expired signed URLs, oversized
    uploads, spoofed MIME types, traversal-style filenames, duplicate/retried
    writes and deletion after partial failure.

## Reject or challenge

- Treating S3 as a mounted filesystem or relational database.
- Using a root/shared credential or enabling anonymous access globally.
- Using `localhost` or an invented `.internal` hostname from an app container.
- Storing business authorization only in object metadata.
- Returning an S3 key or signed URL before checking the requesting user's
  authorization.
- Accepting unlimited uploads, trusting extensions, or rendering uploaded
  SVG/HTML as trusted active content.
- Making a user-upload bucket public to simplify downloads.
- Adding a second object store without a concrete requirement.

Explain the reason and compute/operations avoided for each pattern. Configuration review cannot prove authorization, actual content validation or cleanup; cover
those with integration tests and review.
