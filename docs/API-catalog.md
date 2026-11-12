# API and error catalog

This is a navigational index for specification release 1.0, not a separate wire profile. The linked specifications and schemas own the exact request and response rules. A schema alone does not establish an implemented service or a payment guarantee.

## Public reads

Public read requests require no reader account, payment or signature. Servers apply current lawful disclosure, availability and rate controls. A provider's response is not proof of network-wide completeness. The Lifetime Vault serves the same routes.

| Route | Scope and response | Authority |
| --- | --- | --- |
| `GET /v1/messages/{message_id}` | Exact retained signed post. 410 `retention_expired` after the provider's declared retention ends. | [Public download](./05-portability.md#public-download-and-provider-exit) |
| `GET /v1/messages` | Paginated provider-local retained posts, including all deliverable versions. | [Listing filters](./05-portability.md#listing-and-date-filters) |
| `GET /v1/author-messages` | Same listing, filtered by a canonical `author_id`. | [Author lookup](./05-portability.md#finding-authors-and-replies) |
| `GET /v1/replies/{message_id}` | Optional advisory exact `reply_to` lookup; candidates, not a global thread. | [Replies](./05-portability.md#finding-authors-and-replies) |
| `GET /v1/references/{target}` | Optional advisory lookup of posts declaring the exact signed reference target. | [Reference lookup](./05-portability.md#finding-declared-references-and-version-successors) |
| `GET /v1/versions/{message_id}` | Optional advisory immediate-successor candidates by exact `supersedes`. | [Version lookup](./05-portability.md#finding-declared-references-and-version-successors) |
| `GET /v1/changes` | Incremental sync by provider-local acceptance `sequence`; returns a `ChangesPage`. | [Incremental sync](./05-portability.md#incremental-sync) |
| `GET /v1/settlements/{receipt_id}` | `SettlementProof` that the receipt's fee was paid to the Foundation: sum-tree path plus committee witnesses, or 404. | [Settlement](./03-economics.md#proofs-and-receipt-states) |
| `GET /v1/settlement-claims` | The provider's signed claim chain by `network` and `after_sequence`. | [Claims](./03-economics.md#claims-and-leaves) |
| `GET /v1/settlement-claims/{claim_id}/leaves` | The leaves of one claim in tree order. | [Claims](./03-economics.md#claims-and-leaves) |
| `GET /v1/settlement-claims/{claim_id}/witnesses` | The committee witnesses the provider holds for one claim. | [Claims](./03-economics.md#claims-and-leaves) |
| `GET /v1/retention` | The provider's signed `RetentionDeclaration` objects, newest first. | [Retention](./03-economics.md#provider-retention) |
| `GET /v1/successions/{did}` | Key successions whose `old_id` is that DID. | [Key succession](./02-protocol.md#key-succession) |
| `GET /.well-known/foryou-operator.json` | Signed operator disclosure; not a compliance certificate. | [Operator manifest](./04-compliance.md#operator-manifest-and-privacy) |

Listings and advisory indexes use the bounded `DiscoveryPage` and the date/from/until/limit/cursor semantics in portability. An expired cursor returns `400 invalid_cursor`. A null cursor means that provider's snapshot scan ended, not that the network was exhausted.

## Admission, funding and authorization

| Route | Authentication and role | Authority |
| --- | --- | --- |
| `POST /v1/fee-quotes` | Signed author/delegate preflight for the exact intent under the release-approved schedule; returns a signed quote. | [Quote and admission](./02-protocol.md#quote-and-atomic-admission) |
| `POST /v1/admissions` | Signed quote-bound authorization; atomic debit and receipt for new work. | [Quote and admission](./02-protocol.md#quote-and-atomic-admission) |
| `POST /v1/messages` | Submit the completed signed post with its receipt. 201 for a new durable acceptance, 200 for an identical retry. | [Acceptance](./02-protocol.md#acceptance-retries-and-conflicts) |
| `POST /v1/service-challenges` | Bounded pre-authentication issuance of a one-use root challenge. | [Service authentication](./02-protocol.md#administrative-request-authentication) |
| `POST /v1/deposits` | Root-authenticated request for a provider-signed deposit invoice. | [Funding](./02-protocol.md#funding-the-provider-local-balance) |
| `POST /v1/deposits/observe` | Root-authenticated transfer hint; 202 while pending, or the signed credit. | [Funding](./02-protocol.md#funding-the-provider-local-balance) |
| `GET /v1/balances/{network}` | Root-authenticated signed balance status; not a solvency proof. | [Funding](./02-protocol.md#funding-the-provider-local-balance) |
| `POST /v1/withdrawals` | Root-authenticated withdrawal of unused balance; returns a signed `WithdrawalStatus`. | [Funding](./03-economics.md#funding-a-provider-local-balance) |
| `GET /v1/admissions/{message_id}` | Root-authenticated lookup of a committed receipt. | [Quote and debit](./03-economics.md#quote-and-debit) |
| `POST /v1/settlement-witnesses` | A monitor delivers a self-authenticating `SettlementWitness`. | [Settlement committee](./03-economics.md#the-settlement-committee) |
| `POST /v1/authorization-epochs` | Root-authenticated delegation epoch enrollment. | [Delegation](./02-protocol.md#delegation-revocation-and-time) |
| `POST /v1/authorization-epochs/control` | Root-authenticated `freeze` or `rotate`. | [Delegation](./02-protocol.md#delegation-revocation-and-time) |
| `POST /v1/authorization-epochs/state` | Root-authenticated signed epoch state. | [Delegation](./02-protocol.md#delegation-revocation-and-time) |
| `POST /v1/revocations` | Root-authenticated delegation revocation; free and idempotent. | [Delegation](./02-protocol.md#delegation-revocation-and-time) |
| `POST /v1/successions` | Publish a self-authenticating `KeySuccession`. | [Key succession](./02-protocol.md#key-succession) |

A committed admission retry is recovered before new-work freshness, balance or capacity checks. A rejected new admission does not debit the balance.

## Foundation and vault

The Foundation serves these routes on the vault origin; providers do not. The vault also serves the public read routes that [portability](./05-portability.md#lifetime-vault) lists for it.

| Route | Role | Authority |
| --- | --- | --- |
| `PUT /v1/vault/messages/{message_id}` | Anyone delivers a finalized signed message with its settlement proof; returns a signed `VaultReceipt`, or 409 `not_ready`. No authentication. | [Lifetime Vault](./03-economics.md#lifetime-vault) |
| `GET /v1/foundation/quality-reports` | The quality reports the Foundation used for a quarter, copied from the monitors. | [Publications](./03-economics.md#foundation-publications) |
| `GET /v1/vault/receipts/{message_id}` | Public proof of vault delivery. | [Lifetime Vault](./03-economics.md#lifetime-vault) |
| `GET /v1/foundation/genesis` | The `GenesisManifest`. | [Genesis manifest](./06-governance.md#genesis-manifest) |
| `GET /v1/foundation/certificates` | Foundation key certificates, closures and release key-set updates. | [Publications](./03-economics.md#foundation-publications) |
| `GET /v1/foundation/fee-schedules` | Every fee schedule with its release approval. | [Publications](./03-economics.md#foundation-publications) |
| `GET /v1/foundation/distribution` | Release-approved distribution policies and quarterly statements. | [Publications](./03-economics.md#foundation-publications) |
| `GET /v1/foundation/vault-status` | Quarterly vault status. | [Publications](./03-economics.md#foundation-publications) |
| `GET /v1/foundation/log`, `GET /v1/foundation/log/heads`, `GET /v1/foundation/log/proof/{object_hash}`, `GET /v1/foundation/log/objects/{object_hash}` | The append-only log of Foundation-signed objects, its signed heads, its inclusion proofs and the objects themselves. | [Foundation log](./06-governance.md#foundation-log) |

## Monitors

Served by each committee monitor.

| Route | Role | Authority |
| --- | --- | --- |
| `GET /v1/witnesses` | The settlement witnesses, refusals and holds the monitor has signed, with the signed claims they refer to, by provider, network and sequence. | [Settlement committee](./03-economics.md#the-settlement-committee) |
| `GET /v1/equivocations` | Equivocation proofs the monitor holds for a provider. | [Settlement committee](./03-economics.md#the-settlement-committee) |
| `GET /v1/quality-reports` | The monitor's own quality reports for a provider and quarter. | [Distribution](./03-economics.md#distribution) |
| `GET /v1/quality-reports/{report_id}/methodology` | The exact methodology text of one report; its SHA256 is the report's `methodology_digest`. | [Distribution](./03-economics.md#distribution) |
| `GET /v1/quality-reports/{report_id}/observations` | The exact `QualityObservationSet` of one report; its SHA256 is the report's `observations_digest`. | [Distribution](./03-economics.md#distribution) |
| `GET /v1/foundation-evidence` | `FoundationEvidence` the monitor holds about the Foundation's log, closures and deposits. | [Foundation log](./06-governance.md#foundation-log) |

## Optional owner export

A provider is conformant without these routes. A provider that offers owner export follows the [owner export profile](./10-owner-export-profile.md).

| Route | Scope | Authority |
| --- | --- | --- |
| `POST /v1/exports` | Owner-authenticated export job; the request ID is idempotent and the job ID is not a credential. | [Export transport](./10-owner-export-profile.md#owner-export-transport) |
| `GET /v1/exports/{job_id}` | Owner-authenticated job status. | [Export transport](./10-owner-export-profile.md#owner-export-transport) |
| `GET /v1/exports/{job_id}/index` | Owner-authenticated exact source index bytes. | [Export transport](./10-owner-export-profile.md#owner-export-transport) |
| `GET /v1/exports/{job_id}/parts/{part_number}/{offset}` | Owner-authenticated bounded part chunk. | [Export transport](./10-owner-export-profile.md#owner-export-transport) |
| `GET /v1/exports/{job_id}/files/{part_number}/{entry_number}/{offset}` | Owner-authenticated bounded data-file chunk. | [Export transport](./10-owner-export-profile.md#owner-export-transport) |

## Optional display names

A provider or replica is conformant without these routes. A holder that offers them follows the [display names profile](./12-display-names-profile.md). Reads need no account. A name is a label signed by a key, never a unique or verified identity.

| Route | Scope | Authority |
| --- | --- | --- |
| `POST /v1/names` | Publish a self-authenticating `NameRecord`; free. 201 when it becomes current, 200 for the identical current record, 409 `stale_state`, 409 `not_ready` without an accepted post of that author, 422 `invalid_message`, 429 `rate_limited`. | [Publish](./12-display-names-profile.md#publish) |
| `GET /v1/names/{author_id}` | The holder's current `NameRecord` for that author, including a withdrawn (null) name, or 404 `not_found`. | [Read one author](./12-display-names-profile.md#read-one-author) |
| `GET /v1/names?display_name={name}` | Advisory lookup after NFC and simple case folding; a `NamesPage` of at most 50 candidates from this holder only, never a uniqueness claim. | [Look up by name](./12-display-names-profile.md#look-up-by-name) |

## Reserved rights-intake routes

These route names are reserved and OPTIONAL in core. Their procedure is described in the nonnormative [operator compliance guide](./11-operator-compliance-guide.md#bounded-intake-and-recovery).

| Route | Scope |
| --- | --- |
| `POST /v1/notices` | Bounded notice intake; no account or root key required. |
| `POST /v1/rights-requests` | Bounded rights-request intake; submission does not establish standing. |
| `POST /v1/appeals` | Bounded appeal intake. |
| `GET /v1/intake/{request_id}` | Recover the submitter's own request using the private `ForYou-Intake-Key` header. |
| `GET /v1/intake-forms/{form_id}/{form_version}` | Retrieve an immutable intake form definition. |

There is no author-delete route. A legal restriction or removal applies within the acting provider's scope and does not prove that other copies disappeared.

## Status and error interpretation

The owning route contract takes precedence. Error bodies are the closed `PublicReadError` object of the operations schema. The body is `{status}` with one of the names below. On 429 and 503 it also carries `retry_after_seconds` (an integer from 1 to 86400).

| Status | Defined interpretation |
| --- | --- |
| 200 / 201 | Existing result or newly committed result, as the route specifies. |
| 202 | Pending work, as the route specifies: export preparation, deposit observation or withdrawal. Not proof of finality. |
| 400 | Malformed syntax or query: `invalid_query`, `invalid_cursor`. |
| 401 | Missing, expired or invalid service-auth or provider signature: `unauthenticated`. |
| 402 | `insufficient_balance` on admission or withdrawal. |
| 403 | Disclosable restriction: `policy_restricted`, `legal_restricted` or `restricted`; or `delegation_revoked` on admission. Takes precedence over 410. |
| 404 | Unknown or nondisclosable object, or a path that is not a route of this service: `not_found`. Not proof of global absence. |
| 405 | A method the route does not define. The response has an `Allow` header naming the defined methods and an empty body; no status name is defined for it. |
| 409 | State conflict: `id_collision`, `not_ready`, `export_invalidated`, `quote_conflict`, `stale_state`, `request_conflict`. `not_ready` means a precondition is not met yet: export bytes requested while the job is preparing, a vault delivery whose receipt is not yet settled, or a display name published by an author with no accepted public post at that holder. |
| 410 | `retention_expired` for a post whose declared provider retention ended, or `export_expired` for an export job. The record may still be in the Lifetime Vault. |
| 416 | `range_not_satisfiable`: an export chunk offset exceeds the authorized total. |
| 422 | Semantic rejection before any debit: `id_mismatch`, `message_too_large`, `invalid_message`, `quote_expired`, `bad_authorization`. |
| 429 | A disclosed rate or work limit: `rate_limited`. |
| 503 | Unavailable service, state or capacity: `unavailable`. Never a manufactured success. |

The schema's status list also contains `too_large`. No route in release 1.0 returns it; it is reserved, and a server MUST NOT send it.

Every error and status response carries `Cache-Control: no-store`, including the 404 for an unknown path and the 405 for an undefined method. A server MUST NOT answer either with a body that is not the `PublicReadError` object, apart from the empty 405 body.

Public restriction bodies and disclosure limits are defined in [shared signals](./04-compliance.md#shared-signals-and-legal-restrictions). Rate limits MUST NOT silently alter filters or produce empty successful results.
