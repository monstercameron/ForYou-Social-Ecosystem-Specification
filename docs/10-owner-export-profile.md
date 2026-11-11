# Owner export profile (optional)

## Status

This is an optional profile. A provider is conformant to core 1.0 without it. A provider that offers owner export MUST follow it, and a client that imports or creates an export archive MUST apply its checks.

This profile defines the authenticated export routes, the archive encryption, the archive format, the multipart rules, verification of the provider source, and import.

## Scope

Export covers the owner's lawfully available retained posts and admission evidence as of a disclosed snapshot time. An owner can have an empty set. App preferences, external media bytes, root private keys, payment secrets and upload credentials are out of scope.

The post fee does not purchase an export entitlement, and statutory access rights remain exercisable without a post fee. The provider applies [current disclosure controls](./04-compliance.md#current-disclosure-during-owner-export) before preparing a snapshot and before serving each chunk. Preservation alone does not prohibit the owner from receiving otherwise lawful records.

## Archive container

The archive is a private directory. ZIP and tar packaging are not defined.

| Path | Content |
| --- | --- |
| `manifest.json` | Owner-root-signed ExportSetManifest, profile `ForYouExportSet-1` |
| `parts/{n}.json` | Local ExportPartManifest, profile `ForYouExportPart-1` |
| `data/...` | The files listed by the parts |
| `source-index.json` | Exact provider ExportSetIndex bytes (provider-built archives only) |
| `source-parts/{n}.json` | Exact provider source part bytes (provider-built archives only) |

### Set manifest and index

An ExportSetManifest contains `author_id`, a fresh canonical 32-byte base64url `snapshot_id`, `created_at`, `total_entries`, `total_bytes`, `coverage`, the ordered part descriptors, `source_index_sha256` (null for a client-created archive) and `signature`. The owner signs P("export-set", the manifest excluding `signature`).

A provider job first produces an unsigned ExportSetIndex with the same fields except `source_index_sha256` and `signature`. Its hash identifies the exact provider-proposed snapshot; it is not an owner signature or a completeness proof.

Each part descriptor holds `part_number`, `byte_length`, the SHA256 of the exact UTF-8 JCS part bytes, and `entry_count`. Part numbers are contiguous, zero-based and listed once in order.

`coverage` is a provider assertion, not proof:

| Value | The provider MUST use it when |
| --- | --- |
| `complete` | it knows of no omitted entitled record. It MUST NOT claim `complete` for a set it knows is incomplete. |
| `incomplete` | it knows an entitled record is omitted and disclosing that fact is lawful. |
| `unknown` | completeness cannot be established, or disclosing that a record was withheld is prohibited. |

The owner signs the same coverage value and MUST NOT upgrade it.

### Parts and entries

An ExportPartManifest is UTF-8 JCS with profile `ForYouExportPart-1`, the set's `snapshot_id`, `author_id` and `created_at`, a `part_number` and its entries. An ExportEntry has a unique normalized relative `path` below `data/`, `media_type`, `byte_length`, `sha256` and `category` (`public_message` or `service_evidence`).

| Limit | Value |
| --- | --- |
| Index or manifest JSON | at most 1 MiB |
| Part manifest | at most 4 MiB |
| Entries per part | 1–10,000 |
| Parts per set | at most 1,000 (zero for an empty set) |
| Entries per set | at most 10,000,000 |
| Data file `byte_length` | 0–2 MiB |
| Data file path | at most 1024 UTF-8 bytes |
| Default total extraction budget | 1 GiB; larger archives need explicit owner approval and streamed bounded verification |

Public messages remain at most 1 MiB; the 2 MiB file cap exists for service evidence.

Part packing MUST respect both the entry count and the exact encoded part size; 10,000 entries do not necessarily fit in 4 MiB. Before accepting a job the provider MUST determine that the source metadata and the owner-transformed metadata can each be packed within these limits and any lower disclosed limit. A provider MUST NOT silently truncate an offered or legally required export; when a limit prevents completion it reports `incomplete` or `unknown` coverage or uses a separately documented lawful process.

A set is structurally complete only when all of the following verify, using checked arithmetic: contiguous part order, matching snapshot identity in every part, each descriptor's length, hash and entry count, the total entry count, the total data byte count, unique paths, and every file's length and hash. Incomplete or unknown coverage MUST stay visible and MUST NOT be relabeled complete.

## Provider source and owner archive

The export routes expose a provider-proposed unsigned ExportSetIndex and its source part manifests. All entries belong to one owner-bound snapshot. The client MUST verify:

- the index hash against the hash reported by the job;
- every source part's exact JCS bytes, hash and identity;
- allowed paths and categories;
- every source file's length and hash, and the original message, receipt or service-evidence proofs.

An owner signature on the resulting archive cannot establish that the provider included records it withheld. Where independent checkpoints are unavailable, completeness is unknown.

### Prepared admissions

For a prepared admission the provider sends the exact UTF-8 JCS bytes of `{kind:"prepared_admission",object:{request,receipt}}` over owner-authenticated HTTPS only. It MUST reject duplicate keys, noncanonical encodings and unknown wrapper fields before admitting the entry into the snapshot, and MUST protect its staged copy at rest.

The client verifies the original intent, admission authorization, receipt, fee-schedule and provider and author bindings, historical delegation and URL syntax. It then encrypts the plaintext to the owner-controlled archive key and creates an owner-root-signed ArchiveRecord under the owner-export encryption rules. A plaintext prepared submission MUST NOT be stored in the portable archive. All other source files keep their exact bytes.

| Limit | Value |
| --- | --- |
| Prepared AdmissionRequest and SubmissionReceipt | the protocol's request and receipt limits |
| Decrypted PreparedAdmissionRecord | the two limits combined plus 64 bytes |
| Wrapped prepared service-evidence file | at most 2 MiB |

Parsing and decryption MUST be bounded before allocation, and these files MUST NOT be compressed. Archive size allowances never change public admission or download limits, and archive records never appear in public listings.

### Rebuilding the local manifest

Wrapping changes a prepared entry's bytes, hash and length. The client therefore rebuilds the local part descriptors, file metadata and totals, preserving each source entry's path and category exactly once, and signs the resulting ExportSetManifest. It sets `source_index_sha256` to the SHA256 of the exact provider index bytes and keeps those bytes as `source-index.json` and the original source parts under `source-parts/`. These files contain private owner information and need protected storage.

No other transformation or omission is permitted. Source metadata proves consistency with the proposed source, not that the provider's inventory was complete.

### Restored prepared records

A restored prepared record is unpublished recoverable text. A client MUST NOT fabricate a final author signature, display it as public, or charge or publish automatically.

Resuming at the admitting provider requires the verified original admission and receipt, the author's final signature, applicable lawful controls, and first finalization within the provider-local 30-day preparation window measured from receipt `issued_at`. At or after that deadline the provider MUST refuse first finalization; it still returns a previously accepted identical post on retry. A later revocation or an expired admission freshness window does not undo a committed admission or prohibit timely finalization. A new intent needs new authorization and its own admission.

## Import and verification

Import starts from the expected `author_id` taken from a trusted account or backup record; an archive for a different owner is rejected unless the user explicitly chooses a different-account import. Before committing any restored state the client MUST verify:

1. the owner signature on `manifest.json`, every part and every file;
2. for a provider-built archive, the source index and source part hashes;
3. that source and local `snapshot_id`, `author_id`, `created_at` and `coverage` match exactly, that the path and category sets are identical, and that all unchanged file hashes agree;
4. for every wrapped prepared entry, that it decrypts and authenticates, and that the original `{kind,object}` reserialized as JCS matches the source entry's length and hash.

Missing, duplicate, reordered, substituted or corrupt parts or files, an invalid source transformation, unavailable archive keys or known omitted records make the restoration incomplete. An absent entry is never proof that the user had no data. Original signed bytes are preserved, and an old provider receipt is never relabeled as a new admission. Client-created archives MUST be importable without the old provider online.

Entry content:

| Category | Content and checks |
| --- | --- |
| `public_message` | A complete signed UTF-8 JSON post, verified as a direct download. |
| `service_evidence` | Exact UTF-8 JCS `{kind,object}` for supported admission and fee-schedule evidence. Validate the closed ServiceEvidence wrapper and the artifact schema and signature, reject duplicate keys and unknown wrapper fields, and verify each original signature, hash, author and provider binding. |

Provider-specific records MAY be exported only in a bounded documented representation and MUST NOT be presented as a standard portable financial contract. A receipt or manifest proves provenance, not legality, solvency, trusted admission or completeness. Missing media behind an external URL does not invalidate a text archive.

### Path safety

Across the entire set, including `manifest.json`, `parts/`, `source-index.json` and `source-parts/`, the importer MUST reject:

- absolute or drive paths, dot, parent or empty components, and backslashes;
- symlinks, alternate streams, platform device names, and trailing dots or spaces;
- case-insensitive collisions, file-versus-directory prefix conflicts and filesystem aliases.

Unsafe paths are rejected, never normalized. Extraction uses a fresh private directory, no-follow and race-resistant operations, bounded file counts and no overwrite. Root private-key backup is a separate explicit operation.

### Freshness

A signature establishes provenance, not freshness. A client SHOULD persist the digest and `created_at` of its latest verified manifest in an independent checkpoint. An older or divergent archive MUST be identified as historical and MUST NOT silently replace a newer backup; without a trusted checkpoint, freshness is unknown. The previous valid archive is kept until its replacement verifies.

## Disclosure changes and job state

When a disclosure decision invalidates a staged snapshot, the provider MUST NOT redact signed bytes, serve previously staged prohibited bytes or report an incomplete set as complete; the owner MAY request a new job. An authenticated caller receives only information lawful for that caller. Security throttles MUST preserve statutory rights. The provider records and exposes snapshot time, job state and provider-caused failures without revealing restricted data.

## Owner-export transport

Where an operator offers owner export, `POST /v1/exports` uses the same fresh root service-auth and a body `{author_id,request_id}`. Return 202 with ExportJobCreated while preparing or 200 for an exact retry of a ready job; exact authenticated retries recover the original job. A job ID is not a credential. Export availability is governed by operator terms and legal rights, not a prepaid balance.


All export routes require a fresh one-use service-auth challenge for their exact method/resource and the same owner/root author as the job. Authorize the requested resource and current disclosure before revealing whether a job, part, file or offset exists. The client uses the already pinned HTTPS origin and provider service_id; no unapproved origin, server-supplied arbitrary URL, redirects, browser ambient credential or public bearer link is used. These are fixed canonical paths; decimal components are ASCII `0` or nonzero digits without leading zeroes. No query string or Range header is accepted on these routes, so the authenticated resource binds the offset itself. A timeout always requires a new challenge, but never creates a new job or public debit.

Before accepting a new request_id, enforce disclosed per-author and aggregate job-count, creation-rate, build-concurrency, retained snapshot/metadata byte and staging-work budgets. If capacity is unavailable, return 429 or 503 before committing a job; a refused ID may be retried. After authentication, exact retries of a committed request_id always recover that original job before applying new-job limits. Where export is offered or legally required, reserve protected capacity for applicable commitments and statutory rights; throttling cannot erase them. Providers may deduplicate immutable underlying snapshot bytes within authorized scope while retaining each job's identity, fixed snapshot, expiry and current disclosure checks. Repeated fresh request IDs never create unbounded seven-day staged copies. Invalidation/restriction rules apply to every job sharing bytes.

- `GET /v1/exports/{job_id}` returns ExportJobStatus. preparing, invalidated and failed carry only job_id/status. ready additionally carries snapshot_id, index_sha256, ready_at and expires_at. Times are canonical UTC; expires_at is at least seven days after ready_at and later than now. A ready snapshot stays owner-retrievable through expiry unless current lawful disclosure prevents it; account suspension alone does not deny owner export. Re-request with a new request_id after snapshot expiry or invalidation; do not mutate the old ready snapshot.
- `GET /v1/exports/{job_id}/index` returns exact UTF-8 JCS ExportSetIndex bytes as the entire body (at most 1 MiB) with `application/json` and no content encoding. SHA256 MUST equal the ready status index_sha256; snapshot_id/author MUST match the job. It is a provider proposal, not an owner signature or proof of completeness.
- `GET /v1/exports/{job_id}/parts/{part_number}/{offset}` returns a bounded slice of that source part's exact JCS bytes. Part numbers are contiguous zero-based integers from the index. The part's expected byte length and SHA256 are committed by its index descriptor.
- `GET /v1/exports/{job_id}/files/{part_number}/{entry_number}/{offset}` returns a bounded slice of the indexed source data file; entry_number is zero-based within that source part. No filesystem path from a request is resolved. File length/hash come from the verified part manifest.

The last two routes return 200 `application/octet-stream`, identity encoding, exact Content-Length, and decimal `ForYou-Offset` and `ForYou-Total-Bytes` headers. offset is in bytes from the beginning; return 1 through min(262144,total-offset) bytes whenever offset<total, never past total. offset==total returns a zero-length final chunk; offset>total returns 416. Clients check offset/length/total against the index/part before appending, reject zero-length 200 responses before EOF and truncated/mismatched lengths, preserve the last verified resume checkpoint and bound retries/time. Resume by requesting the next exact offset, reject overlapping/mismatched data and verify the complete SHA256 before use. Chunks are owner-authorized and scoped to the exact job snapshot; every retransmitted chunk counts toward the bounded export allowance, subject to disclosed service terms and applicable statutory rights.

Ready artifacts are immutable; check current disclosure authorization at manifest/index delivery and immediately before every chunk or retry as required by [compliance](./04-compliance.md#current-disclosure-during-owner-export). If a relevant restriction makes any included source byte or manifest information undisclosable, atomically invalidate the job, return 409 `{status:"export_invalidated"}` when lawful, and serve no more snapshot bytes. Use the same nonrevealing 404 as an unknown job where existence cannot be disclosed. Never silently omit one entry or revive the old job after a restriction lifts. An unrelated preservation hold does not itself imply denial. If current safety state is unavailable after recovery, fail closed for the affected scope and return 503. A new authorized job may capture a newly permissible snapshot.

Use 404 `{status:"not_found"}` for an unknown or non-disclosable job/part/file, 409 `{status:"not_ready"}` for bytes requested while preparing, 410 `{status:"export_expired"}` for an expired job where disclosure is lawful, 429 with retry information for rate limits and 503 for unavailable service capacity. Apply identical disclosure behavior for absent and concealed objects, without case details. A job in failed state MUST include no arbitrary diagnostic string in its public-shaped status; authorized operator support may provide separate lawful details. Operational status, expiry and disclosure limits never waive statutory rights.

No public bearer URL or root private key is returned. Regional rights requests by non-account subjects retain the alternative workflows in [the compliance specification](./04-compliance.md).

## Owner-export encryption


This encryption profile is solely for confidential prepared-admission evidence in owner archives. It is not a public message type, preference service or private-sync endpoint. The named ArchiveRecord schema has message_type archive_record, author_id, timestamp, version, message_id, signature and payload. Its payload has state_kind `export.prepared-admission.v1`, a fresh `backup:` plus 32 random base64url bytes as device_group_id, state_sequence 0, empty supersedes, encryption_scope device_group, encryption_scheme x25519-xchacha20poly1305 and encrypted_state. The retained field/domain names are byte-level archive encodings, not synchronization semantics. Reject these records on public admission, finalization and download routes.

Verify root ownership, outer message-domain signature and computed ID before decryption. Each archive is standalone; no writable sequence/head or preference stream is maintained. Root secrets and payment/upload credentials are not part of the plaintext. The only plaintext kind is the PreparedAdmissionRecord defined in portability. Use its archive-only size allowance; normal public messages remain bounded to 1 MiB.

Encryption is X25519 + HKDF-SHA256 + XChaCha20-Poly1305 combined mode. Encode binary fields as canonical unpadded base64url. Fresh CSPRNG content_key (32 bytes), content nonce (24 bytes), ephemeral X25519 private key per recipient, and wrap_nonce (24 bytes) are required for every new encryption. Reject an all-zero X25519 shared secret. Recipient public keys are separate 32-byte encryption keys; kid equals base64url of that key. Reject duplicate recipients and more than 32 recipients; sort by kid using ascending ASCII order. Envelope v is exactly 1.

Let C = `{author_id, device_group_id, state_kind, state_sequence, timestamp, version}` from the enclosing message and payload. Let A = P("private-state", C). Plaintext is UTF-8 JCS of the state object. Encrypt using content_key, nonce and A, appending the 16-byte tag to ciphertext. For each recipient let R = `{kid, recipient_pubkey, epk}`. HKDF uses IKM = X25519 shared secret, salt = 32 zero bytes, info = P("private-wrap", R), output length 32. Wrap content_key with this derived key, wrap_nonce and AAD = `A || P("private-wrap", R)`; wrapped_key is exactly 48 bytes including the tag. Reject decryption or key-validation failures without exposing partial plaintext. Verify outer signature and ID before decryption. The entire envelope, recipient list, sequence and supersedes are covered by the outer signature. Encryption context intentionally excludes message_id to avoid a circular hash dependency.
