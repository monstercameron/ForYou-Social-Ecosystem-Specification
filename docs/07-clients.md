# Core client integration

## Scope

A client is any software that publishes or downloads records: a script, CLI, website or application. This document states the protocol-visible obligations of a client. Other topics have their own owners:

- byte formats and limits: [the protocol](./02-protocol.md);
- fees and settlement: [economics](./03-economics.md);
- routes: [portability](./05-portability.md).

Role-specific rules apply only to a client performing that role. A reader-only client has no funding or publishing obligations.

The specification defines no screens, feeds, ranking, likes, follows, notifications or preference synchronization. An application MAY build them from downloaded records and MUST NOT present them as network state.

## Keys

- A publishing client MUST generate the author root key with a cryptographically secure generator.
- Before the first publication, the client MUST warn the user that:
  - control of the root key is control of the identity;
  - a lost key cannot be recovered;
  - a compromised key cannot be revoked under the same DID.

  It MUST offer an encrypted backup controlled by the user.
- The client MUST NOT transmit the root private key or a backup secret to a provider and MUST NOT place either in a record.
- A `KeySuccession` served at `GET /v1/successions/{did}` is an advisory link from an old key to a new one. The client MUST verify both signatures, MUST treat conflicting successions for one `old_id` as unresolved, and MUST NOT present a succession as recovery of a lost key.

## Funding safety checks

Before sending funds to a provider-local balance, a client MUST:

| Check | Requirement |
| --- | --- |
| Invoice | Verify the deposit invoice signature under the selected provider's key and that its network, address and expiry match the request |
| Network | Refuse a network or funding method the release does not define; Bitcoin and Ethereum balances are separate |
| Disclosure | Have received the provider's [custody and balance disclosure](./04-compliance.md#custody-and-balance-disclosure) |
| On-chain data | Place no DID, account identifier or draft content in the transaction |

A client MUST NOT:

- describe a deposit as available before the provider's signed committed credit;
- resend a deposit automatically after a timeout; it reconciles the original transfer first;
- treat a third party's payment as granting that party posting authority;
- describe the protocol fee as a provider price. The fee is the schedule amount and is owed in full to the Foundation.

## Publish

1. **Fix the intent.** Compose the text, up to 16 media slots and up to 32 `payload.refs`, fix the exact intent `I` and compute its `message_id`. A **media-only post** has empty `text` and at least one media slot; a post with empty `text` and no slot is invalid.
2. **Check the schedule.** Select the fee schedule in force. Verify its `FeeScheduleApproval` against the pinned release key set and threshold, and check the revision bound against the previous revision. A client MUST reject a schedule that fails either check and MUST NOT invent or estimate a fee.
3. **Recompute the fee.** Compute `fee = base_fee + per_KiB_fee × ceil(billable_bytes / 1024)` in the schedule's integer units. `billable_bytes` is the UTF-8 byte length of the canonical JCS intent `I`, including all slot and reference metadata and excluding `message_id`, the receipt and the enclosing message signature.
4. **Check the quote.** Verify the provider's signed quote and reject it unless its amount, `schedule_id` and intent match the local calculation exactly. An unexpired quote keeps its amount across a schedule change.
5. **Authorize.** The author or a delegate with post scope signs the quote-bound authorization for the exact intent. The client MUST obtain the user's approval of the exact content and fee first. Any change to a signed intent field changes the `message_id` and requires a new quote and a new authorization.
6. **Admit.** The provider debits the confirmed balance and commits the signed admission receipt atomically. No blockchain transaction occurs per record. A failed admission leaves the balance unchanged.
7. **Finalize.** Attach the receipt, sign the complete message and submit it before the preparation deadline defined in [the protocol](./02-protocol.md). A client MUST NOT report a record as published before the provider accepts the finalized message.

Retry rules:

- The client MUST keep the exact signed admission request and quote until the outcome is known.
- An ambiguous admission response is resolved by retrying the same authorized intent. The client MUST NOT create a second authorization for the same content to resolve it.
- A previously accepted identical message remains retrievable on retry.

Updates and replies:

- An update sets `payload.supersedes` to the immediate prior version's `message_id`. It has the same author and an identical `reply_to` (both absent is identical). It pays the full fee as a separate record. It neither changes nor deletes its target. There is no author-delete message.
- If verified evidence shows the target has a different author or a different `reply_to`, the client MUST reject the update relationship before authorization.
- A comment sets `reply_to` to the verified parent's `message_id`. Cost and authorship rules are the same as for any record.

References and slots at publication:

- Each `payload.refs` entry is exactly `{id,target}`. `id` is 1–32 characters of lowercase ASCII letters, digits, underscore or hyphen. `target` is a canonical message ID or author `did:key`. The client MUST reject duplicate reference IDs and duplicate targets. Reference IDs and media slot IDs are separate namespaces.
- Each media slot has a unique `id`, an HTTPS `url`, a `kind`, the lowercase `sha256` of the exact media bytes, optional `alt_text` of at most 2000 Unicode scalar values and optional `size_bytes`. The publishing client computes `sha256`, and `size_bytes` when it sets it, from the exact bytes before signing.
- Media bytes and upload credentials MUST NOT be placed in a record. Admission never fetches a slot URL or a reference target.

Retention seen by the author:

- The admitting provider retains the record until the receipt's `issued_at` plus the retention period of the `RetentionDeclaration` named by the settlement claim that contains the receipt.
- The Lifetime Vault retains it without scheduled expiry.

See [economics](./03-economics.md#retention-and-the-lifetime-vault).

## Download and verify

Public read routes need no account, payment or signature. A client MUST verify every record itself, in this order, and stop at the first failure:

| Step | Check | On failure |
| --- | --- | --- |
| 1 | The signed `{major, minor}` is supported; the record matches that version's closed schema | `invalid` |
| 2 | The recomputed canonical `message_id` equals the stated and requested ID | `invalid` |
| 3 | The author signature, or the delegate signature with its delegation, verifies | `invalid` |
| 4 | The provider receipt signature verifies and binds this `message_id`, intent and fee | `invalid` |
| 5 | The receipt's schedule carries a valid `FeeScheduleApproval`, was in force at the receipt `issued_at` or within the 3,600 seconds before it, and the receipt fee equals the locally recomputed fee; the receipt `issued_at` is within 300 seconds after and 60 seconds before the message `timestamp` | `invalid` |
| 6 | Settlement state of the receipt (below) | Not `locally_admitted` |
| 7 | Local trust in the receipt's provider | Per [the protocol](./02-protocol.md) |

The result is one of `invalid`, `cryptographically_valid_untrusted`, `cryptographically_valid_trusted_unaccepted` or `locally_admitted`, as defined in [portability](./05-portability.md#decentralized-operation-and-trust-boundaries). No signature proves that content is true.

Settlement state:

| State | Condition |
| --- | --- |
| `settled` | A `SettlementProof` from `GET /v1/settlements/{receipt_id}` verifies: the sum-tree audit path links the hash of the receipt to the provider's signed claim, and a quorum (more than two-thirds) of one committee (the current one, or the previous one for 30 days after a change, counting only witnesses dated before the change) has witnessed that claim or a later claim linked to it through the proof's `chain` |
| `pending_settlement` | Not settled, fetched from the provider's own read routes, less than 7 days old, from a provider the client trusts locally and has no delinquency record for. Not proof of payment |
| `unsettled` | Anything else |

- `locally_admitted` requires `settled` or `pending_settlement`. Clients and relays MUST NOT classify a record with an `unsettled` receipt as admitted.
- The proof MAY be fetched from the provider or from the vault. Only a message the client fetched from the provider's own public read routes can be `pending_settlement`. A client MUST recheck such a record no later than 7 days after the receipt `issued_at`. A receipt still not settled then is delinquent. The client keeps a delinquency record for that provider until the receipt settles. Meanwhile it treats none of that provider's receipts as pending.
- A `settled` result MAY be cached. A client re-evaluates it when the committee changes, using the providers' current witnesses.

Responses and coverage:

- A client MUST distinguish the statuses in [compliance](./04-compliance.md#shared-signals-and-legal-restrictions) and MUST NOT report a 403, 404 or 410 from one provider as global absence or deletion.
- A client MUST respect a 429 retry delay and the provider's disclosed limits.
- To mirror a provider, use [incremental sync](./05-portability.md#incremental-sync). `sequence` values are provider-local and are not a global order.
- Listings follow [snapshot pagination](./05-portability.md#snapshot-pagination). An ended scan covers one provider and is not proof of completeness.
- Views a client derives from downloaded records are not protocol state and MUST NOT modify signed records.

The synthetic [post and comment example](../examples/post-comment-thread.json) and [version-chain example](../examples/post-version-chain.json) use public test keys only.

## Version chains

- A client MUST verify each record and each `supersedes` edge before joining versions. An edge is verified only when both records are available and have the same author and identical `reply_to`.
- An update whose target is unknown stays a standalone record with an unresolved edge. If the target is later found to have a different author or `reply_to`, the client rejects that edge only; both records remain valid.
- A client MUST bound traversal depth and work and MUST stop on a repeated ID.

Default selection among the known terminal leaves of one verified same-author chain:

| Order | Rule |
| --- | --- |
| 1 | A leaf signed directly by the root key (`signer_id == author_id`, no delegation) beats any delegate-signed leaf |
| 2 | Then the greatest receipt `issued_at` |
| 3 | Then the ASCII-smallest `message_id` |

The selection is a local default over known records. It is not proof of the globally latest version or of the author's preference. A client MUST NOT discard a valid leaf because it lost the selection. An older version that is unavailable is not restored by a newer one.

## Comments and threads

- A record with `reply_to` is a comment on that exact version. A client MUST preserve the signed target and MUST NOT substitute a newer version's ID or text for it.
- Parent author and text come only from the verified parent record, never from the comment.
- A missing or restricted parent does not invalidate the child. An unknown parent stays unresolved.
- A parent reference is a `message_id` resolved only through providers the user approved; it is never fetched as a URL.
- A client MUST deduplicate by `message_id`, reject self-reference, bound traversal and stop on a repeated ID.
- Reply lookups and indexes are advisory. Each returned record needs full verification, and derived counts MUST NOT be presented as network totals.

## Links and navigation

Text is untrusted data. A client MUST accept only `text/plain` and CommonMark 0.31.2 without extensions. It MUST treat raw HTML as literal text. It makes active only the links, images and references the protocol defines.

| Construct | Rule |
| --- | --- |
| Inline link `[text](url)` or autolink `<https://...>` with no title, passing the restricted HTTPS URL profile | MAY be active |
| Bare URL, link with a title, or any other scheme (`http`, `javascript:`, `data:`, `file:`, `blob:`, `mailto:`) | Inert literal text |
| Invalid or overlength URL (more than 4096 characters, non-ASCII, userinfo, backslash) | Inert literal text; never repaired or normalized |
| Internationalized hostname | Shown only as ASCII A-labels |
| `[label](fy-ref:<id>)` | Refers only to the signed `payload.refs` entry with that ID; with no matching entry it is inert text |
| Direct `fy:` link, bare `@name`, hashtag | Inert text; creates no identity, notification or index entry |
| `![label](fy-media:<id>)` | Refers only to the declared media slot with that ID; unknown ID is inert |
| Other Markdown image URL | Inert; MUST NOT trigger a fetch |

- A client MUST NOT fetch, preview, prefetch, preconnect or resolve DNS for an external link while rendering. It contacts the destination only after an explicit user action for that link. Before that, it shows the full checked destination, including its host and any nondefault port.
- Approved navigation opens with `noopener` and no referrer. A blocked or failed navigation MUST NOT become a background fetch.
- A reference label is chosen by the author and can misrepresent its target. A client MUST identify the target by its canonical DID or message ID, or by a name the reader assigned locally, and MUST NOT treat the label as a verified name.
- A reference is resolved only on user action, through approved providers, with full verification. It is not a web address and grants no permission.

## Media slots

Only signed media slots are eligible for display. Media is always external and optional.

- **Consent before fetch.** A client MUST NOT contact a slot URL, including prefetch and preconnect, before a user action or a revocable user preference for that exact origin. A redirect or secondary resource on a new origin needs separate consent.
- **Destination safety.** Apply the URL, destination, redirect and credential controls in [the protocol](./02-protocol.md): no cookies, credentials or referrer.
- **Size.** When the slot has `size_bytes` (integer 1 to 2^53−1), the client MUST abort a download that exceeds it and MUST reject an object whose length differs from it. Without `size_bytes`, the client applies its own transfer bound.
- **Digest.** Before decoding or rendering, the client MUST verify SHA-256 over the complete received object against the slot's `sha256`. A mismatched, oversized or unverifiable object is not rendered.
- **Video.** A client MUST NOT play an object progressively before the whole-object digest verifies.
- **Fallback.** Unavailable or refused media MUST NOT prevent the text from being read.

How a client arranges text and media is a local choice and is not signed state.

## Owner export

Owner export is OPTIONAL and is specified in the [owner export profile](./10-owner-export-profile.md). A client that supports it MUST NOT publish unfinished paid intents contained in an export and MUST NOT describe an export or a key backup as recovery of a compromised identity.

## Implementation advice (nonnormative)

This section is guidance. It creates no conformance requirement.

- **Backup check.** Before the first publication, a client SHOULD let the user restore the root-key backup locally and confirm the derived public identity or a challenge signature. Hardware-protected keys can satisfy this by an equivalent check without exporting the secret.
- **Local secret scan.** Before signing, a client SHOULD scan the proposed text, links and slot metadata locally for obvious credential and sensitive-data patterns and show the findings. The scan is heuristic, and draft content is never sent to a remote scanner.
- **Public-persistence notice.** Before publication, a client SHOULD tell the user that every version is public, has no author-delete operation, is retained by the provider for its declared period and by the Lifetime Vault without scheduled expiry, and can persist in independent copies.
- **Linkability notice.** Before funding, a client SHOULD tell the user that public-chain payments can be correlated with the provider and, through provider records, with the author DID.
- **State tracking.** A client SHOULD track funding and publication progress separately and show the preparation deadline for an admitted but unfinalized intent.
- **Local copies.** A client SHOULD offer the author a protected local copy of each signed version and its receipt.
- **Reply context.** When a reply targets an earlier version than the one selected, a client SHOULD show which version the reply addressed.
- **Link labels.** When a visible label resembles a URL that differs from the destination, a client SHOULD show the real destination beside it.
- **Source coverage.** A client SHOULD show which providers were queried and that results may be incomplete.
