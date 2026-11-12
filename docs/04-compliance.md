# Compliance: restriction semantics and operator disclosure

## Scope and boundary

This document is normative. It defines only what an interoperable implementation needs:

- how a provider restricts or removes a record locally, and what the public sees;
- what an operator discloses;
- how data-rights requests relate to the absence of an author-delete message;
- disclosure during owner export;
- custody disclosure;
- the free rights and claims channel.

Operating procedures (intake forms, case management, per-market checklists, incident handling, funding disputes) are in the nonnormative [operator compliance guide](./11-operator-compliance-guide.md).

Three concepts are independent and MUST be kept separate:

| Concept | Decided by | Effect |
| --- | --- | --- |
| Cryptographic validity | The signed bytes and [the protocol](./02-protocol.md) | Identical for every verifier |
| Availability and restriction | Each operator, for its own service | Local to that operator |
| Filtering and ranking | Each reader or application | Local to that reader |

- A restriction MUST NOT alter a signed record, its signature or its `message_id`, and does not make a valid message invalid.
- Cryptographic validity creates no right to hosting. An operator is not required to serve content it cannot lawfully handle, and no requirement in this specification requires violating applicable law.
- The protocol defines no global blacklist, real-name registry or content authority. The ForYou Foundation has no authority over content at any provider other than the Lifetime Vault it operates.
- Each operator remains responsible for the law that applies to its actual role, markets and fund flows. An implementation MUST NOT present conformance to this specification as legal compliance or certification.

In this document an **account** is the provider-local record keyed by `author_id` that holds that author's per-network prepaid balances and admission history at one provider. An account is not a protocol identity, exists at one provider only and is never transferable.

## Shared signals and legal restrictions

A provider MAY restrict or remove a retained record under its disclosed policy or applicable law. The action is local to that provider.

For the public read routes in [portability](./05-portability.md#public-download-and-provider-exit), a provider MUST answer for a restricted, removed or expired record exactly as follows:

| Situation | HTTP status | JSON body |
| --- | --- | --- |
| Policy refusal, reason may be disclosed | 403 | `{status:"policy_restricted"}` |
| Legal refusal, reason may be disclosed | 403 | `{status:"legal_restricted"}` |
| Existence may be disclosed, reason may not | 403 | `{status:"restricted"}` |
| Existence may not be disclosed | 404 | `{status:"not_found"}` |
| Retention period ended and the record was dropped, direct GET only | 410 | `{status:"retention_expired"}` |
| Rate or work limit | 429 | per the owning route |
| Service or capacity unavailable | 503 | per the owning route |

- A restriction body contains only the `status` field. It MUST NOT contain case identifiers, reporter details, evidence, counts of hidden records or free text. An error body is at most 1024 UTF-8 bytes.
- The nonrevealing 404 MUST use the same body and disclosure behaviour as the 404 returned for an unknown object.
- A provider MUST NOT return 410 for a record whose existence it may not disclose; the restriction response takes precedence over `retention_expired`.
- A provider MUST NOT disguise a rate or capacity failure as a restriction, or a restriction as a rate or capacity failure.
- Listings omit restricted records without a marker and MUST NOT disclose how many records were withheld.
- A restriction takes effect on the provider's own responses when it is committed. Copies cached under the direct-GET cache bound in [portability](./05-portability.md#public-download-and-provider-exit) MAY persist until that bound elapses; bytes already delivered cannot be recalled.
- A provider subject to a restriction MUST NOT serve the restricted record through a proxy, cache, replica or fallback it controls.
- The Lifetime Vault applies the same statuses. Its restrictions are local to the vault.

Client and relay interpretation:

- Clients MUST distinguish timeout, `not_found`, `retention_expired`, rate or capacity exhaustion, `policy_restricted`, `legal_restricted` and `restricted`. For `restricted`, a client MUST NOT infer or state a legal basis.
- A 404, 403 or 410 describes one provider. It is not proof of global absence, deletion or illegality, and it is not an instruction to any other provider or client.
- A client MAY query other providers the user selected. A client MUST NOT forward confidential case details when it does so.
- Each provider decides independently whether a restriction applies to it. One provider's refusal does not require another provider to suppress the record.

Shared deny-list or hash-list signals are evidence for an operator to assess. They MUST carry issuer, scope, provenance, version and a correction route. An operator MUST NOT publish restricted lists or evidence and MUST NOT apply an author-wide block solely on an unverified signal.

A record stores text and external links, never media bytes. Restricting a record restricts the locally stored link; it does not remove the remote file.

### Recovery of acknowledged controls

A control is a committed restriction, legally required removal or delegation revocation.

- Before acknowledging a control as effective, the operator MUST durably commit its scope and ordering. If durability cannot be established, the operator MUST report failure and MUST NOT acknowledge success.
- Control state MUST be recoverable independently of ordinary content backups.
- After a restore, failover or suspected rollback, the operator MUST keep affected public delivery, owner disclosure and delegated issuance closed until current control state is verified. Uncertainty fails closed with 503.
- Restored data MUST NOT restore a removed record, lift a restriction or revive a revoked delegation. Only a separately authorized, durably recorded action lifts a reversible restriction.
- Recovery state MUST NOT be published as a list of restricted identifiers and is not a shared registry.

The guide describes one [checkpoint design](./11-operator-compliance-guide.md#recovery-checkpoint-procedure) that satisfies these rules.

## Operator manifest and privacy

Every operator that offers admission, public download or the Lifetime Vault MUST publish `/.well-known/foryou-operator.json`, an `OperatorManifest` signed over P("operator-manifest", the object excluding `signature`). The requirement does not depend on whether the service is commercial.

| Field | Requirement |
| --- | --- |
| `operator_id` | The operator's `did:key` |
| `manifest_version` | Positive integer, strictly increasing per operator |
| `issued_at`, `expires_at` | `expires_at` at most 30 days after `issued_at` |
| `service_roles` | Roles the operator performs |
| `service_endpoints` | HTTPS endpoints covered by the manifest |
| `supported_profiles` | Wire versions supported |
| `policy_url`, `policy_digest` | The operator's policy and its digest |
| `legal_contact`, `abuse_contact`, `privacy_contact` | Contacts; role addresses are sufficient |
| `appeal_url` | Entry point of the free rights and claims channel |
| `markets_assessed` | Markets the operator states it has assessed |

- A manifest is a disclosure signed by the operator. It is not a compliance certificate, and no global registration exists.
- A manifest and any public message MUST NOT contain user locations, identity documents, notices, private reports, account-to-wallet mappings or age evidence.
- Clients MUST verify the signature against a locally trusted or user-approved operator key, and MUST persist the highest verified `manifest_version` and its signed-body digest per operator.
- Clients MUST reject a lower `manifest_version` even if its signature is unexpired. The same version with a different body is equivocation: the client MUST stop treating the manifest as current until the user reviews the operator key and policy.
- A trust reset MUST be an explicit user action.

The provider's retention period is published separately in its signed `RetentionDeclaration`; see [economics](./03-economics.md#retention-and-the-lifetime-vault).

## Custody and balance disclosure

An author prepays BTC or ETH into the account balance at one provider. The provider debits each admitted record's protocol fee from that balance as a collection agent. It owes the full debited amount to the Foundation under [settlement](./03-economics.md#settlement). The fee amount comes only from the release-approved [fee schedule](./03-economics.md#denominations-and-versioned-fee-schedule).

Before accepting a deposit, a provider MUST disclose all of the following:

| Disclosure | Content |
| --- | --- |
| Custody | The provider holds the balance; neither the protocol nor the Foundation guarantees the provider's solvency |
| Scope | The balance is specific to one `author_id`, one provider and one network, is not transferable between providers or authors, and is not a protocol token |
| Fee | Each admitted record is charged the schedule amount; the provider does not keep it and cannot change it |
| Crediting | A deposit is credited only after the confirmation or finality condition in [the protocol](./02-protocol.md) |
| Costs outside the fee | Network transaction costs of deposits and withdrawals, stated separately from the protocol fee |
| Loss | Provider insolvency, custody failure or legal restriction can impair recovery of an unspent balance |
| Remedy | The free rights and claims channel and the remedies in [economics](./03-economics.md) |
| Linkability | Public-chain deposits can be correlated with the provider and, through provider records, with the author DID |

- A provider MUST NOT describe the protocol fee, the schedule or any asset conversion as terms it sets, and MUST NOT charge a different protocol fee than the schedule amount.
- A provider MUST NOT present an unconfirmed or orphaned deposit as spendable.
- A provider MUST keep each account's deposit, debit and withdrawal history available to the authenticated author for as long as the account has a balance or an open claim. It serves that history, signed, at `GET /v1/account-history/{network}/{after}`, defined with [funding](./02-protocol.md#funding-the-provider-local-balance).
- A provider MUST NOT treat an unmatched, excess or late transfer as forfeited without the claims process below.
- Control of an author root key proves control of the protocol identity. It does not prove ownership of funds sent by someone else; a third-party payer uses the claims channel.
- A provider MUST NOT place DIDs, account identifiers or dispute details in on-chain transaction data.

Whether an operator's activity is custody, a payment service or another regulated activity is decided by applicable law, not by these labels.

## Personal-data lifecycle

The protocol has no author-delete or withdrawal message. An edit is a new record with `payload.supersedes`; it does not erase the earlier version. At the provider, each accepted record is retained until its `retain_until` under the provider's declaration. In the Lifetime Vault it is retained without scheduled expiry. Both are defined in [economics](./03-economics.md#retention-and-the-lifetime-vault). Anyone may keep an independent copy.

These protocol facts do not waive erasure, correction, access or other legal rights. Such rights are exercised as follows:

- A data-rights request is made to each operator separately through its free rights and claims channel. It is never a protocol message and never requires a fee, a balance or a root key.
- The Foundation is the operator of the Lifetime Vault and handles requests concerning the vault's copy through its own channel.
- An operator that grants a request acts on its own copy by restriction or removal and then answers with the statuses in [shared signals and legal restrictions](#shared-signals-and-legal-restrictions). A legally required removal overrides the retention duty for that record at that operator.
- A person who is not the author MUST be able to make a request without holding any protocol key.
- An operator MUST NOT state or imply that its action deletes the record from other providers, the vault or independent copies.
- A removed record MUST NOT be restored by backup recovery, replica repair or re-delivery from another operator the removing operator controls.
- No operator is required to notify, and no protocol message exists to notify, other providers of a removal.

## Current disclosure during owner export

Owner export is the optional [owner export profile](./10-owner-export-profile.md). An operator that offers it MUST apply these rules.

- An export job or signed manifest is not a continuing disclosure grant. The operator MUST recheck the authenticated recipient, job and file ownership, and current permission to disclose each included record on manifest delivery, file delivery, retries, resumed chunks and incremental transfers.
- Temporary public unavailability alone does not revoke the owner's export entitlement for records still retained. Account suspension does not remove the export entitlement either.
- A preservation hold requires preservation, not automatic disclosure or automatic denial. The requested disclosure is evaluated separately.
- Owner authentication does not override a disclosure prohibition and does not authorize disclosure of case evidence.
- The operator MUST serialize the release of each bounded response chunk against committed controls. When a control prevents further disclosure, the operator MUST stop releasing bytes and invalidate affected staged artifacts and resumptions. It does so at every cache, replica and file-delivery service it controls, before acknowledging the control as effective.
- The operator MUST NOT serve a prepared export after the underlying record was removed or restricted from disclosure. Where permitted it MAY prepare a replacement export with new integrity commitments and an accurate incomplete indication. It MUST NOT alter a signed manifest or file in place, silently omit promised records, or describe the original export as complete.
- The operator MUST NOT disclose withheld identifiers or counts when that disclosure is itself prohibited.
- An incremental manifest MUST NOT direct reuse of a locally cached entry whose disclosure is now prohibited.
- Bytes already released cannot be recalled, and the operator MUST NOT claim to erase a recipient's existing copy.
- After a restriction is lifted, disclosure requires a fresh decision and a new artifact; an invalidated job or token is never revived.

## Rights and claims channel

Every operator MUST offer a free channel for notices, data-rights requests, appeals and funding claims.

| Rule | Requirement |
| --- | --- |
| Cost | No fee, paid membership, balance or blockchain transaction to submit |
| Identity | No root key or account required merely to submit; third-party payers and people described in another author's record MUST be able to use it |
| Entry point | Published as `appeal_url` in the operator manifest, with at least one alternative that does not depend on the HTTP routes below |
| Reserved routes | `POST /v1/notices`, `POST /v1/rights-requests`, `POST /v1/appeals`, `GET /v1/intake/{request_id}`, `GET /v1/intake-forms/{form_id}/{form_version}` |
| Request bound | An intake request is at most 256 KiB of UTF-8 JCS; larger requests are rejected |
| Caching | Every intake response carries `Cache-Control: no-store` |
| Nondisclosure | An unknown and a nondisclosable submission receive the same 404 |
| Saturation | 429 with retry information or 503; an operator MUST NOT acknowledge a submission it has not durably stored |

- The reserved routes are OPTIONAL. An operator that implements them MUST use the `IntakeRequest`, `IntakeReceipt`, `IntakeRecovery` and `IntakeForm` definitions in the [operations schema](../schemas/operations.schema.json), and MUST follow the optional [bounded intake and recovery profile](./11-operator-compliance-guide.md#bounded-intake-and-recovery).
- A receipt proves that the operator received a submission. It does not prove the truth of a claim, the standing of the submitter or any entitlement.
- Before disclosing case information or acting on a claim, the operator MUST verify the claimant's authority separately. A message ID, case ID, email address or payment alone is not authority.
- A public restriction status does not replace the private reasons, notice and appeal owed to an affected party under applicable law.
