# Display names profile (optional)

## Status

This is an optional profile. A provider, replica or client is conformant to core 1.0 without it. A holder that offers the routes below MUST follow this profile, and a client that shows display names from it MUST apply its client rules.

The profile defines a signed name record, three routes and the rules for showing names. It adds no message type, no fee and no core state. Likes, follows, profiles and ranking remain outside the core, as stated in the [overview](./01-overview.md#core-principles).

In this document a **holder** is a provider or replica that offers the routes.

## Principles

- The author key (`did:key`) is the identity. A display name is a label the author attaches to that key.
- Names are not unique. There is no global registry. Two keys can use the same name. A name never proves a real-world identity.
- A signed name means exactly one thing: this key signed this name. A client MAY show that as "signed by this key" and nothing more.
- People follow the key, never the name. A follow is client state, not protocol state. Renaming keeps followers. Using another author's name gains none.
- An author MAY keep a name local, visible only in their own client, or sign and publish it.

## Name records

A `NameRecord` is `{name_id,author_id,display_name,issued_at,previous_name_id,author_signature}`. It is a closed object: an unknown field is rejected. It is self-authenticating and portable between holders.

| Field | Rule |
| --- | --- |
| `name_id` | `fynr2:` plus lowercase SHA256 hex of P("name-record-id", the record without `name_id` and `author_signature`) |
| `author_id` | The author's root canonical `did:key` |
| `display_name` | A string that satisfies the [name rules](#name-rules), or null. Null withdraws the name |
| `issued_at` | The signing time, in the protocol's [date format](./02-protocol.md#value-formats) |
| `previous_name_id` | Null for the author's first record; otherwise the `name_id` of the record it replaces |
| `author_signature` | Made by `author_id` over P("name-record", the record without `author_signature`) |

P is the [signing input](./02-protocol.md#signing-input) of the protocol. The signature uses the protocol's [strict verification profile](./02-protocol.md#strict-verification-profile).

- A delegate key MUST NOT sign a name record. A posting delegation grants no authority over names.
- `previous_name_id` is an assertion by the author. It lets a reader see a gap or a fork in the author's records. It does not decide which record is current.
- The exact JCS record is at most 4096 bytes.

### Name rules

A non-null `display_name` MUST satisfy all of the following. Character properties are those of the Unicode Character Database, version 15.0.0.

| Rule | Requirement |
| --- | --- |
| Normalization | The string is already in Unicode Normalization Form C (NFC). A verifier rejects a string that is not; it never normalizes a signed name |
| Length | 1 to 64 Unicode scalar values and at most 256 UTF-8 bytes |
| One line | No character of general category Zl (line separator) or Zp (paragraph separator). Line feed and carriage return are excluded as Cc |
| Excluded characters | No character of general category Cc (control) or Cf (format). This covers bidirectional controls and zero-width characters |
| Assigned characters only | No character of general category Cn (unassigned, including noncharacters), Co (private use) or Cs (surrogate) |
| White space | No leading or trailing character with the Unicode White_Space property, and no two consecutive U+0020 SPACE characters |

The rules limit what a name can do on screen. They do not make a name safe, unique or truthful.

### Verification

A verifier accepts a name record only when all of the following hold:

1. The record matches the closed `NameRecord` schema.
2. `display_name` is null or satisfies the name rules.
3. The recomputed `name_id` equals the stated one.
4. `author_signature` verifies under `author_id`.
5. `issued_at` is not more than 60 seconds ahead of the verifier's clock. This is the protocol's general [clock tolerance](./02-protocol.md#time).

A record that fails any check is invalid. It is never shown and never selected.

### Current record

The current record of an author, among the valid records a holder or client knows for that `author_id`, is:

1. the record with the greatest `issued_at`;
2. on a tie, the record with the ASCII-smallest `name_id`.

The current record is a local result over known records. It does not prove that no later record exists elsewhere. A current record with a null `display_name` means the author has withdrawn the name.

## Holder rules

- A holder keeps the current record of each author. It MAY keep earlier records as history.
- A holder serializes acceptance per author, so that the current record follows the selection rule, never the arrival order.
- **Accepted-post rule.** A holder accepts a name record only for an `author_id` of which it has accepted at least one public post, signed by that author or by a valid delegate. Names are free, so they ride on an identity that has paid for at least one post.
- **Rate limit.** A holder accepts at most one new record per author in any 24 hours, measured by its own clock at acceptance. A holder MAY set a looser limit and MUST disclose it. An identical retry does not count.
- A holder MAY refuse or withhold a name record under its disclosed policy or a legal restriction, as for any content. Such a decision is local to that holder.
- Name records are not messages. They carry no receipt and no fee. They never appear in listings, `/v1/changes`, settlement or the Lifetime Vault, and they have no retention period.

## Routes

A holder MAY offer these routes. Reads need no account, payment or signature, like every public read. Errors use the closed `PublicReadError` body of the [API catalog](./API-catalog.md#status-and-error-interpretation). On every route a holder MAY also return the restriction statuses of [compliance](./04-compliance.md#shared-signals-and-legal-restrictions), 429 `rate_limited` for its disclosed read limits and 503 `unavailable`. Every response is sent with `Cache-Control: no-store`.

### Publish

`POST /v1/names` publishes one name record. The body is the `NameRecord` as `application/json`, at most 4096 bytes. No service-auth is needed, because the record authenticates itself. Publishing is free.

The holder checks the request in this order and returns the first matching status:

| Order | Condition | Status |
| --- | --- | --- |
| 1 | The body is not a valid name record under [verification](#verification) | 422 `invalid_message` |
| 2 | The record is identical to the holder's current record for that author | 200 with the record |
| 3 | The holder's current record for that author would still be selected over the posted record | 409 `stale_state` |
| 4 | The holder has accepted no public post of that author | 409 `not_ready` |
| 5 | The author has exceeded the holder's rate limit | 429 `rate_limited` with `retry_after_seconds` |
| 6 | Otherwise the record becomes the current record in one durable commit | 201 with the record |

### Read one author

`GET /v1/names/{author_id}` returns the holder's current record for that author.

| Status | Meaning at this holder |
| --- | --- |
| 200 | The current `NameRecord`. A withdrawn name is returned as the record, with `display_name` null |
| 400 `invalid_query` | The path is malformed |
| 404 `not_found` | No record for that author, or none that can be disclosed |

The path component is encoded exactly once, as for the [optional index routes](./05-portability.md#finding-declared-references-and-version-successors): unreserved ASCII literal and every colon as uppercase `%3A`, so the path begins `did%3Akey%3Az6Mk`. A 404 is not proof that the author has no name elsewhere.

### Look up by name

`GET /v1/names?display_name={name}` is an advisory lookup. It returns current, non-withdrawn records at this holder whose `display_name` matches the query after NFC and Unicode simple case folding of both strings.

| Parameter | Contract |
| --- | --- |
| `display_name` | Required. After percent-decoding, valid UTF-8 that, after NFC, has 1 to 64 Unicode scalar values and at most 256 UTF-8 bytes |
| `cursor` | Optional. Opaque canonical unpadded base64url encoding of exactly 32 random bytes (43 ASCII characters). Omit for a new snapshot |

The response is a `NamesPage` `{names,next_cursor}`:

- `names` holds at most 50 records, ordered by `author_id` ascending by ASCII, one per author;
- `next_cursor` is null only when the snapshot has been fully scanned.

| Status | Meaning at this holder |
| --- | --- |
| 200 | A `NamesPage`, which MAY be empty |
| 400 `invalid_query` | A malformed query, a missing or invalid `display_name`, or an unknown or repeated parameter |
| 400 `invalid_cursor` | A malformed, unknown, expired or mismatched cursor |

Query encoding and cursors follow the listing rules of portability:

- [Query validation](./05-portability.md#listing-and-date-filters) step 1 applies: the raw query is at most 16384 bytes, values are decoded exactly once and `+` is not a space.
- [Snapshot pagination](./05-portability.md#snapshot-pagination) applies to the snapshot, its 15 to 60 minute lifetime, bounded state and cursors. A cursor is bound to this holder, this route, the normalized query and the snapshot.
- A page returns each listed author's record that is current when the page is served. An author whose current record no longer matches is skipped.

Results are candidates from this holder only. A result is never a claim that a name is unique, and an empty page is not proof that no author uses the name. A lookup reveals the reader's interest to the holder.

## Client rules

### Verification and display

- A client MUST verify every name record under [verification](#verification) before showing its name, and MUST check that its `author_id` is the key being shown.
- When it knows records from several holders, a client applies the [current record](#current-record) rule across all valid records it knows.
- A client MUST show a name together with the short key fingerprint, always. The short fingerprint is the first 16 lowercase hexadecimal digits of SHA256 of the UTF-8 `author_id`, shown in four groups of four. The full `author_id` MUST be available to the reader on request.
- A client MUST NOT present a name as unique, official or identity-verified. A signed name gets at most a neutral "signed by this key" mark.
- Where the core requires the canonical target to be available to the reader, as for [signed references](./02-protocol.md#signed-structured-references), a display name is shown in addition to that target, never instead of it.

### Petnames

A reader MAY assign a local petname to a key. A petname takes precedence over the author's display name and is marked as the reader's own. Petnames are client state and are never published by this profile.

### Following

- Following stores `author_id` values. A follow list is local client state.
- A client builds the Following view from `GET /v1/author-messages` across the reader's providers.
- A follow is never tied to a name. A renamed key stays followed, and a key that adopts a followed author's name gains nothing.

### Key succession

If a followed key publishes a [key succession](./02-protocol.md#key-succession), the client offers to follow the new key and shows that the link was asserted by the old key. It never follows the new key automatically. When successions for one old key conflict, the client offers neither. A succession does not move a name: the new key's name is its own record.

### Collisions

A client marks a collision when two different keys on screen, or a visible key and a followed key, have names that match after NFC and Unicode simple case folding. A client MAY also mark names that are confusable under its own rules.

### Escaping and bidirectional isolation

A display name is untrusted text. A client MUST escape it for the context it is placed in and MUST isolate it from the surrounding bidirectional context. A name is never parsed as Markdown or HTML.

## What this profile is not

- **No registry.** Nobody assigns, reserves, sells or arbitrates names.
- **No uniqueness.** Any number of keys can use the same name. A holder does not reject a name because another key uses it.
- **No identity proof.** A signed name proves only which key signed it.
- **No social graph on the wire.** There are no follower lists, follow objects, follower counts or subscription routes. Following stays in the client.
- **No core change.** A provider is conformant without this profile, and posts, fees, settlement and retention are unchanged.
