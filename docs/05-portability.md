# Portability and decentralization

## Non-negotiable boundaries

The protocol requires user-held identity, interoperable messages, independently chosen download sources, autonomous operator policies and voluntary provider choice. There is no protocol token, universal feed, global content authority, exclusive directory or mandatory project-operated publishing service.

The ForYou Foundation is identified by a `foundation_id` certified by the release keys. It receives protocol fees, distributes fees and operates the Lifetime Vault, as defined in [economics](./03-economics.md). It has no authority over message validity, identity, content moderation or client trust choices.

Cryptographic validity does not compel a host to accept, store or serve content. Interoperability claims measure conformance, not political agreement or paid membership. Providers MAY reject trust relationships but MUST disclose them. A closed default allowlist MUST NOT be described as permissionless universal acceptance.

## Independent provider entry and discovery

Anyone MAY implement and operate a provider without maintainers' approval. A provider charges the release-approved fee schedule and settles collected fees as defined in [economics](./03-economics.md#settlement). Neither membership fees nor maintainer certification are protocol prerequisites. Trust remains local.

A provider that peers MUST publish objective admission requirements for peering. They include supported profile, signature checks, abuse handling and availability. A refused applicant receives an explanation where lawful, but a peer cannot be forced to trust it.

Clients MUST support:

- manually entered HTTPS endpoints and operator keys;
- imported signed manifests;
- independently distributed bootstrap lists;
- locally stored peer hints.

Clients MUST enforce the destination checks, freshness and limits of [the protocol specification](./02-protocol.md). Discoverability never grants provider trust, and no source guarantees complete network coverage.

Default provider or monitor lists MUST disclose:

- who controls and funds the list;
- its version;
- the selection and exclusion criteria;
- included monitor identities;
- known ownership relationships and material conflicts.

Clients MUST:

- make defaults visible and replaceable, and let users add or remove providers and monitors without the default operator's permission;
- disclose any automatic list update and its authenticated source, and never apply vendor-controlled silent trust updates;
- where available, offer at least two independently controlled discovery or monitoring sources. Lack of two sources MUST NOT block a deliberate choice of a single provider.

Distinct URLs or keys do not establish independence, and a locally chosen source never becomes a mandatory global directory.

## Public download and provider exit

Every provider exposes its retained finalized messages through public HTTPS GET routes. The server authenticates itself with TLS; the reader does not log in. Downloaders need no account, payment, cookie, wallet signature or social relationship, and reads are never charged. Unfinished intents, payment-attempt data, owner exports and administrative records remain private.

`GET /v1/messages/{message_id}` returns the exact complete signed post as UTF-8 JCS as the entire 200 body, at most MAX_MESSAGE_BYTES as defined in the protocol. Clients MUST require the returned ID to equal the requested ID and independently verify every proof. An update is a new post and never replaces the bytes addressed by an earlier message ID.

| Status | Meaning at this provider |
| --- | --- |
| 200 | The exact signed record. |
| 403 | The bounded policy, legal or generic status in [compliance](./04-compliance.md#shared-signals-and-legal-restrictions). |
| 404 `{status:"not_found"}` | No accessible known object. |
| 410 `{status:"retention_expired"}` | The record was accepted here and dropped after its `retain_until`. |
| 429 | Rate limit, with retry information. |
| 503 | Service unavailable. |

A status describes this provider only; it never proves global absence or deletion. The protocol has no author-delete operation. Already downloaded public versions MAY persist indefinitely. A restriction or removal at one provider neither changes the signed record nor binds another provider.

The baseline profile serves complete GET bodies only. A provider MUST either ignore Range and conditional request headers and return the current full result under the same checks, or refuse the request. It MUST NOT use a 304 or partial response to evade checks. HEAD, if supported, applies the same disclosure and rate controls, never returns a body and is not proof of continued accessibility.

### Retention

No provider has a duty to retain forever. Each provider publishes a provider-signed RetentionDeclaration `{provider_id, retention_seconds, effective_at, ...}` (ID prefix `fyrd2:`).

| Rule | Value |
| --- | --- |
| Minimum `retention_seconds` | 31536000 (1 year) |
| Maximum `retention_seconds` | none |
| `retain_until` of a record | receipt `issued_at` plus the `retention_seconds` of the declaration named by the settlement claim that contains the receipt |
| Changing the period | A new declaration applies to later claims only. A provider MAY keep a record longer than declared and MUST NOT drop it before its `retain_until`. |

Until `retain_until` the provider MUST retain the record and serve it on the public routes, subject to provider-local legal restrictions. Insufficient capacity does not justify dropping a record earlier. A provider that cannot meet its declaration MUST stop accepting new admissions first.

After `retain_until` the provider MAY drop the record. It then returns 410 `{status:"retention_expired"}` on direct GET and omits the record from listings and `/v1/changes`. There is no paid renewal.

Each signed version has its own receipt and its own `retain_until`. Restriction, expiry or loss of one version does not erase, restrict or renew another. The retention duty is not a guarantee against storage failure or provider shutdown.

### Lifetime Vault

The Lifetime Vault is an archive operated and funded by the Foundation. It serves the same public read routes as a provider: direct GET, listings, `/v1/changes` and `/v1/settlements/{receipt_id}`.

A provider MUST deliver every finalized message to the vault with `PUT /v1/vault/messages/{message_id}` within 7 days after its receipt is settled. The body is a `VaultDelivery`: the exact record the provider serves on direct GET together with its settlement proof. The request needs no authentication. Anyone MAY deliver a message a provider failed to deliver. The vault returns a signed VaultReceipt, as defined in [economics](./03-economics.md#lifetime-vault).

The vault retains delivered records with no scheduled expiry, subject to law. This is an obligation of the Foundation, not a guarantee of perpetual availability. Vault restrictions are local to the vault like any other provider's.

### Read capacity and caching

A conformant provider MUST configure at least the following anonymous capacity. Listing requests are the listing routes, the optional index routes and `/v1/changes`.

| Request class | Aggregate floor | Per-source floor |
| --- | --- | --- |
| Direct `GET /v1/messages/{message_id}` | 600 per minute | 30 per minute |
| Listing requests | 60 per minute | 6 per minute |

These are minimum configured capacities, not guarantees under distributed attack, legal restriction, outage or resource exhaustion. Providers MUST:

- disclose their request-rate, concurrency and response-size limits;
- group sources fairly without requiring a reader account or tracking cookie;
- answer exhaustion with 429 plus retry information or with 503.

A throttled request neither destroys a valid cursor nor signals end-of-results.

| Response | Cache-Control |
| --- | --- |
| 200 from `GET /v1/messages/{message_id}` | MAY be `public, max-age=3600`; otherwise `no-store`. A longer lifetime MUST NOT be sent. |
| Listings, `/v1/changes`, HEAD, and every error or status response | `no-store` |

Accepted records are immutable, so a cached 200 body stays correct. The one-hour bound ensures that a provider-local restriction takes effect at every cache within an hour. The origin MUST apply a committed restriction to every later response at once and fail closed when the current control state is unknown. Provider-controlled caches SHOULD be purged when a restriction is committed and MUST NOT serve the record beyond the bound. A cache MUST NOT serve stale content in place of an error. Bytes already released cannot be recalled.

### Settlement proofs

`GET /v1/settlements/{receipt_id}` is a public route on every provider and on the vault. It returns the SettlementProof for that receipt:

- the provider-signed claim;
- the sum-tree audit path that binds the receipt to it;
- the committee monitors' witnesses;
- where needed, the `chain` of later claims that links it to the witnessed one.

A provider also serves its claim chain at `GET /v1/settlement-claims` and its declarations at `GET /v1/retention`. Formats, verification and status codes are defined in [economics](./03-economics.md#proofs-and-receipt-states).

### Listing and date filters

`GET /v1/messages` lists publicly deliverable retained records. `GET /v1/author-messages` additionally requires `author_id` (a canonical DID) and filters by exact signed author. `author_id` is rejected on the unfiltered route. Listings include every matching version, not only an apparent latest one, and deduplicate identical message IDs only. The MessageListQuery and AuthorMessageListQuery schemas describe decoded query values; the rules below also apply.

| Parameter | Contract |
| --- | --- |
| date | One valid Gregorian UTC calendar date, exactly YYYY-MM-DD. Equivalent to from at that day's midnight and until at the next day's midnight. Mutually exclusive with either explicit bound. |
| from | Inclusive lower bound on the signed message timestamp, exactly YYYY-MM-DDTHH:mm:ssZ. Omission means no lower bound. |
| until | Exclusive upper bound on that timestamp, using the same format. Omission means no upper bound. |
| limit | Canonical decimal integer 1–100; default 50. No leading zeroes, signs, whitespace or fractional form. |
| cursor | Opaque canonical unpadded base64url encoding of exactly 32 random bytes (43 ASCII characters). Omit for a new snapshot. Repeat the same effective filters and limit on continuation. |

The predicate is `(from absent OR from <= message.timestamp) AND (until absent OR message.timestamp < until)`, AND exact author equality on the author route. The filter uses the author's signed timestamp, not receipt `issued_at`, insertion time or a client-local date. Each comment and each version is filtered by its own timestamp. A date range is therefore not a complete version history.

Query validation, in order:

1. The raw query string is at most 16384 bytes. Parameter names MUST be the literal supported ASCII names. Repeated or unknown names, empty components, malformed percent escapes or UTF-8, and noncanonical encodings return 400 `invalid_query`. Values are decoded exactly once (unreserved characters literal, other bytes uppercase `%HH`); `+` is not a space.
2. Filters and limit are validated before any snapshot is allocated. Zero or invalid years, invalid days, leap seconds, timezone offsets, fractional seconds, empty values, `from >= until`, `date` combined with `from` or `until`, and a `date` whose next midnight is not representable (9999-12-31) return 400 `invalid_query`.
3. A present cursor with an invalid length, alphabet, padding or final bits, including an empty cursor, returns 400 `invalid_cursor`.

There is no timezone parameter: for a local calendar day the client sends explicit UTC bounds. No value is SQL, a regex, executable code or a URL for the server to fetch.

```http
GET /v1/messages?date=2026-11-10&limit=100
GET /v1/messages?from=2026-11-01T00%3A00%3A00Z&until=2026-12-01T00%3A00%3A00Z&limit=100
GET /v1/author-messages?author_id=did%3Akey%3Az6Mk...&date=2026-11-10
```

The author example abbreviates the DID; real requests carry its complete canonical value.

### Finding authors and replies

`/v1/author-messages` is the minimum author lookup: the client supplies the full canonical `author_id` and pages through that provider's matching posts. It is not a username service or global directory.

Replies can be found without an index: a client downloads listings from selected providers and maps each signed `reply_to` ID to its verified child posts. A provider need not hold the parent to return a child, and an empty result is not proof that no replies exist.

A provider MAY offer the advisory route `GET /v1/replies/{message_id}`. It accepts the `date`, `from`, `until`, `limit` and `cursor` parameters of `/v1/messages`, has no author parameter, and returns the same DiscoveryPage with the additional predicate `payload.reply_to == message_id`. A valid parent ID need not resolve locally: the provider returns matching deliverable children or an empty page without revealing whether a hidden parent exists.

### Finding declared references and version successors

A provider MAY offer two further advisory routes with the same query parameters and DiscoveryPage response:

| Route | Returns each retained, deliverable post where |
| --- | --- |
| `GET /v1/references/{target}` | an entry of the signed `payload.refs` has `target` exactly equal to the requested canonical MessageId or canonical author DID |
| `GET /v1/versions/{message_id}` | the signed `payload.supersedes` exactly equals the requested MessageId |

A reference result is an author declaration, not proof that the target exists or that anyone consented to a notification. A version result is an immediate successor candidate, not a verified chain or a globally latest version.

Rules common to the three optional index routes:

- **Path encoding.** The path component is encoded exactly once: unreserved ASCII literal, every colon as uppercase `%3A`. A message target is `fy1%3A` plus 64 lowercase hexadecimal digits. A DID target begins `did%3Akey%3Az6Mk` and carries the complete canonical base58btc encoding. Raw colons, lowercase `%3a`, extra escapes, unsupported target types and other malformed paths return 400. An identifier is data, never a URL to fetch.
- **Validation and cursors.** Path and query are validated before snapshot allocation. Each cursor is bound to the exact route and canonical target in addition to the bindings in [snapshot pagination](#snapshot-pagination); a cursor used for another target or route returns 400 `invalid_cursor`.
- **Disclosure.** Responses MUST NOT reveal whether a hidden target exists. A result whose reference itself cannot lawfully be disclosed is withheld whole.
- **Status.** The routes are provider-local and optional. They are not global search, a notification service, an authoritative count or proof of complete coverage.

Clients MUST independently verify each returned post's ID, signatures, receipt trust, the exact requested predicate, date filter, ordering and uniqueness. A lookup reveals the reader's interest to the operator; clients SHOULD NOT prefetch such lookups without a user action and MUST bound provider fanout and graph traversal.

A reply keeps its exact signed parent-version ID. A client MUST NOT rewrite a `reply_to` to another version or infer a link to an unavailable or unverified version. Signed author timestamps alone are not proof of publication order.

### Finding the latest known version

Listings never collapse versions. A client MAY group posts by `payload.supersedes` only after verifying the predecessor's ID, the same author and the unchanged `reply_to` under [the protocol rules](./02-protocol.md#posts-comments-and-versions). A missing, inaccessible or untrusted predecessor leaves the edge unresolved.

To search, a client MAY query several independently selected providers with `/v1/author-messages`, `/v1/versions/{message_id}` or `/v1/changes`, with bounded work, repeated-ID and cycle detection. The search is independent of which provider admitted each version.

Among the known terminal leaves of a verified same-author chain, the default selection is:

1. a leaf signed directly by the root key (`signer_id == author_id`, no delegation) beats any delegate-signed leaf;
2. then the greatest receipt `issued_at`;
3. then the ASCII-smallest `message_id`.

This is a local display default over the records known to that client. It does not establish which branch was published last or which the author intended, and no provider response, index or signature proves that a later or competing version does not exist. Forks stay visible: clients MUST preserve every verified branch and report incomplete or failed lookups rather than claim a globally latest version.

### Snapshot pagination

All listing routes (`/v1/messages`, `/v1/author-messages` and, where offered, `/v1/replies/{message_id}`, `/v1/references/{target}` and `/v1/versions/{message_id}`) return a UTF-8 JCS DiscoveryPage `{generated_at,expires_at,messages,next_cursor}`. Nested TransportMessages use the same canonical bytes as direct downloads.

| Limit | Value |
| --- | --- |
| Messages per page | at most `limit`, at most 100 |
| Page size | at most 2 MiB of JSON; at least one maximum-sized message MUST fit |
| Snapshot lifetime (`expires_at - generated_at`) | at least 15 and at most 60 minutes, fixed at creation |
| Order | signed timestamp descending, then `message_id` ascending by ASCII |
| Cursor | 32 CSPRNG bytes, canonical unpadded base64url |

**Snapshot.** An initial request freezes the set of matching records that are finalized, retained and deliverable at `generated_at`, one representation per `message_id`, in the order above. Records that arrive later, including backfilled old-timestamp records, enter only a new snapshot. `generated_at` and `expires_at` are identical on every page of a snapshot, and no request extends the expiry.

**Bounded state.** Snapshot and cursor state is short-lived provider state. A provider MUST disclose a cap on the snapshot state it holds (count, bytes and lifetime) and is never required to hold more than that cap. It MAY refuse a new snapshot or a continuation with 429 or 503, and MUST apply this admission control before expensive work. Limits MUST NOT silently narrow a requested range or truncate results. Attacker-selected date ranges MUST NOT run as unbounded scans.

**Cursors.** A cursor is an opaque handle to provider-side state bound to the issuing provider, route, normalized filters (`date` and its equivalent explicit bounds are the same query; an omitted limit equals 50), effective limit, snapshot and last scanned position. No client-supplied offset is trusted. A changed query, wrong route or provider, or an unknown, discarded or expired cursor returns 400 `invalid_cursor` without revealing hidden records. A cursor is a public continuation hint, not a credential, and a continuation is repeatable without consuming it.

**Paging.** `next_cursor` is null only when the snapshot has been fully scanned. A page MAY hold fewer than `limit` records, or none, with a non-null cursor; every successful non-terminal page advances the scan position. A provider that cannot continue safely returns 400 `invalid_cursor`, 429 or 503 and MUST NOT return an empty terminal page instead.

**Restrictions.** The provider rechecks current deliverability on every page. Records restricted or expired since snapshot creation are skipped without exposing hidden IDs or counts, and are not reintroduced into that snapshot if later restored. A provider MAY instead invalidate the affected snapshot. A signed record is served whole or withheld whole, never redacted. A replayed page is therefore not guaranteed to be byte-identical.

**Clients.** Clients MUST verify:

- the page schema;
- each record's bytes, ID, signatures and filter predicate;
- the ordering and uniqueness;
- the 15–60 minute interval and unchanged snapshot times.

Clients MUST reject a `generated_at` more than 60 seconds ahead of the local clock, a response at or after `expires_at` and a repeated cursor. They MUST deduplicate by `message_id` across retries and snapshots.

Clients continue through empty pages and stop on null, failure or their own page, time and work budget. After expiry or snapshot loss the client restarts the original interval; resuming below the last timestamp can miss late arrivals. A completed snapshot is not a completeness proof. Mirrors SHOULD use [incremental sync](#incremental-sync) instead of repeated rescans.

Topic or search feeds, ranking, notifications and private synchronization have no core endpoints.

### Incremental sync

Each provider assigns every newly accepted public message a provider-local `sequence` at acceptance. `GET /v1/changes` returns accepted records in sequence order. It holds no snapshot state.

```http
GET /v1/changes?after=0&limit=100
```

| Parameter | Contract |
| --- | --- |
| after | Canonical decimal integer 0 to 2^53-1; default 0. Only records with `sequence > after` are returned. |
| limit | Canonical decimal integer 1–100; default 50. |

The response is UTF-8 JCS `{provider_id, items, next_after, more}`, at most 2 MiB in total.

| Field | Contract |
| --- | --- |
| provider_id | The provider that assigned the sequences. |
| items | At most `limit` entries `{sequence, message}` in strictly increasing `sequence`. `message` is the same TransportMessage as the direct GET. |
| next_after | The value to send as the next `after`: the greatest sequence this response covered, never less than the request's `after`. |
| more | `true` when the provider holds sequences greater than `next_after` at response time, otherwise `false`. |

Sequence rules:

- A sequence is a positive integer, strictly increasing in acceptance order at that provider, and never reused, including after recovery from backup.
- Sequences are provider-local. They are not a global order and are not comparable across providers.
- Restricted and retention-expired records are omitted and their sequence numbers are skipped. A gap is not proof of removal, and a response MUST NOT identify which sequences were omitted.
- A response MAY contain fewer than `limit` items, or none, with `more` true; the client continues from `next_after`. An `after` beyond the greatest assigned sequence returns no items, `next_after` equal to `after`, and `more` false.

Query encoding errors return 400 `invalid_query` as for listings; 429 and 503 apply as for listings. Clients verify every record as for a direct download, store `next_after` per `provider_id`, and deduplicate by `message_id`. A fully consumed change stream is not a completeness proof.

### Changing provider

Changing provider preserves `author_id` and all existing message IDs and proofs, and needs no approval from the old provider. New publication at another provider uses the current fee schedule and, where delegated, a new provider-scoped delegation. A destination chooses which admitting providers it trusts. Imported historical records are evidence, not newly admitted content, and do not end the original provider's retention duty.

Clients MAY back up downloaded public records independently. Private owner material is covered by the optional [owner export profile](./10-owner-export-profile.md).

## Decentralized operation and trust boundaries

Each provider keeps its own admission records, chooses its own peers and enforces its own availability, legal and abuse policies. It charges the release-approved fee schedule and collects each fee from the author's provider-local prepaid balance as a collection agent. It owes the full amount to the Foundation under [settlement](./03-economics.md#settlement).

Author identity and message IDs do not derive from a provider account or project registry. A client can:

- configure an HTTPS provider endpoint and an independently obtained provider key manually;
- change defaults;
- download signed records;
- publish under the same root identity at a different provider.

No project-run directory, network token, global moderation service, consensus feed or permission from the old provider is required. Independent provider records do not form one trustless global ledger.

A verifier assigns each receipt one settlement state:

| Receipt state | Condition |
| --- | --- |
| `settled` | A valid SettlementProof for the receipt has been verified. |
| `pending_settlement` | Not settled, fetched from the provider's own read routes, less than 7 days old, from a provider the verifier trusts locally and has no delinquency record for. Not proof of payment. |
| `unsettled` | Anything else. |

A verifier assigns each record one local trust classification:

| Classification | Meaning |
| --- | --- |
| `invalid` | A required encoding, ID, signature, receipt binding or delegation proof fails. |
| `cryptographically_valid_untrusted` | The proofs verify but the receipt provider is not accepted under the receiver's policy. |
| `cryptographically_valid_trusted_unaccepted` | The issuer meets local trust criteria but there is no verified local host acceptance yet. |
| `locally_admitted` | The receiver's explicit trust policy accepts the issuer, the host has durably accepted that message and receipt representation, and the receipt is `settled` or `pending_settlement`. |

Clients and relays MUST NOT classify a record whose receipt is `unsettled` as admitted. A receipt from a self-operated or colluding provider is not by itself proof that a fee was paid. The settlement proof is the evidence that the fee reached the Foundation.

These names are local classifications, not signed message types, portable certificates or a global ranking. A client MUST NOT present cryptographically valid but untrusted content as admitted. Invalid records are never promoted by a trusted provider's assertion. For delegated signatures the claimed authorization time depends on the issuing provider's receipt-time assertion.

A local policy MAY accept any structurally and cryptographically valid provider receipt, or MAY use a user- or host-selected allowlist or other explicit criteria. No universal allowlist is mandatory, and no receiver is forced to store or serve records from every provider. Fees and distinct DIDs do not prove unique humans or prevent Sybil identities.

A local receipt-trust policy MAY consider signed monitor reports under [quality evidence](./09-quality.md). Before using a report the client MUST verify its schema, monitor signature, exact provider identity, period and freshness. A report that is stale, from an unselected monitor or missing required evidence is unknown. It is neither a verified failure nor a favorable score.

Quality-based decisions remain local. A poor, missing or disputed report MUST NOT change cryptographic validity, rewrite a signed post or receipt, or become a network-wide ban. The Foundation's distribution calculation in [economics](./03-economics.md) uses quality reports for payouts only and does not bind any client's trust policy.

A receipt, provider statement or replica acknowledgment is evidence of one signer's commitment, not proof of solvency, availability, completeness or independent ownership. Distinct hostnames, signing keys, cloud accounts or geographic labels are not proof of independent control; unverified independence is unknown.

Independent sources MAY disagree, omit records, disappear or refuse a receipt provider. No endpoint proves it returned every matching message. Clients deduplicate by message ID, validate each representation and report coverage rather than global counts. Root-key compromise, loss of a provider's signing key, simultaneous failure of all copies and widespread legal restrictions remain real limits.

Release conformance evidence MUST exercise two independently administered providers and clients in:

- manual bootstrap and provider-key pinning;
- publish, download and proof checks;
- labeling of an untrusted issuer;
- publication under the same author ID after the first provider is offline;
- differing trust decisions on the same evidence;
- a tested independent replica restore.

This is a release evidence gate, not a central certification.

## Export bundle and import rules

Owner export is not part of the core protocol. The archive format, multipart rules, provider source verification, path rules and import checks are defined in the optional [owner export profile](./10-owner-export-profile.md). A provider is conformant to core 1.0 without offering owner export; a provider that offers it MUST follow that profile.

## Replication and failure behavior

The copies the protocol requires are the admitting provider's own copy until `retain_until` and the copy delivered to the Lifetime Vault. Further replicas are voluntary unless legally required. Gossip is discovery, not a storage contract.

A provider SHOULD sample signature- and ID-verified restores at least monthly and after failover, record missing objects, and repair from verified copies.

A provider that claims independent replicas MUST name their controlling entities and disclose correlated infrastructure. Two URLs on one operator or cloud account are not independent.

Restoration of retained data, revocations and restrictions MUST pass the [control recovery checkpoint](./04-compliance.md#recovery-of-acknowledged-controls) before affected operations reopen. Legal removals follow [the compliance specification](./04-compliance.md) and MUST NOT be undone by automated repair at the same responsible operator.

Failure tests disconnect the original provider, its preferred directory and one index simultaneously. A client with an alternate provider MUST still publish under the same identity and download verified records from the remaining sources, and MUST report missing copies as missing. Not every historical post survives every failure. A restored message restores its external URL references, not the media behind them.

## Keys, device loss and recovery

Identity is `did:key`. A lost root key with a usable backup can be restored. A lost root key without a backup cannot be recovered by anyone, including a provider or the Foundation, and a compromised root key requires a new identity.

A KeySuccession, defined in [the protocol specification](./02-protocol.md) and served at `GET /v1/successions/{did}`, links an old key to a new key for provider keys and author root keys. It is an advisory identity link signed by both keys. It proves control of both keys. It MUST NOT automatically transfer trust or restriction history. Conflicting successions for one old key are unresolved.

Device posting uses scoped, short-lived, provider-specific delegations from [the protocol specification](./02-protocol.md). A signer holding the root key MUST show the method, target service and operation before approving a high-impact action. Untrusted remote content MUST NOT trigger blind signing. Revocation and backup do not require a post fee. Copying a root key creates irrevocable authority under that identity.

## Measured decentralization

Pilot reports SHOULD state provider counts and concentration by controlling entity, infrastructure provider, admission volume and stored bytes, and label unverified independence as unknown. The evidence required for a release is defined in [the governance specification](./06-governance.md).
