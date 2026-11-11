# Governance, Foundation and releases

## Authority and consistency

The [documentation index](./README.md) lists which documents are normative and which topic each owns. Each topic has one owning document. A cross-reference adds no override. The JSON Schemas define structure and the owning prose defines semantics; both MUST be satisfied. Examples, reviews and tests are nonnormative. A contradiction between normative documents is a defect. An implementation MUST NOT claim conformance on the affected point until a release corrects it.

Four kinds of authority exist and are separate:

| Authority | Held by | Covers |
| --- | --- | --- |
| Release | Maintainers holding the release keys | The frozen artifact set, fee schedules, distribution policies, and certification of the Foundation key |
| Economic | The ForYou Foundation, key `foundation_id` | Receiving fees, distribution, Lifetime Vault |
| Settlement | The committee of monitors named in the release-approved policy | Auditing claims against the chain and witnessing them |
| Trust | Each client and operator | Which release keys, providers and monitors to trust |

## Foundation

The **ForYou Foundation** is a protocol actor identified by `foundation_id`, a `did:key` certified by the release keys through a [Foundation key certificate](#foundation-key-certificate). There is no protocol token.

| The Foundation | Object or duty | Defined in |
| --- | --- | --- |
| Has no part in fee schedules | Schedules are approved by the release keys alone | [Fee schedule](./03-economics.md#denominations-and-versioned-fee-schedule) |
| Receives 100% of protocol fees | Prepaid settlement deposits from providers | [Settlement](./03-economics.md#settlement) |
| Has no part in settlement decisions | Claims are settled by the monitor committee alone | [Settlement](./03-economics.md#the-settlement-committee) |
| Distributes fees to providers | Quarterly `DistributionStatement` under the release-approved `DistributionPolicy` | [Distribution](./03-economics.md#distribution) |
| Funds, owns and operates the Lifetime Vault | Public read routes, no scheduled expiry | [Retention](./03-economics.md#retention-and-the-lifetime-vault) |

The Foundation has no authority over, and its signature MUST NOT be treated as deciding:

- message validity, canonical bytes or signature verification;
- author or provider identity, delegation or key succession;
- content moderation at any provider other than the vault it operates;
- which providers, monitors or release keys a client trusts;
- the content of a release. The Foundation cannot change a wire format, a fee formula or its own powers by signature; those change only through a release.

The Foundation cannot approve a fee schedule; only the release keys can. It cannot approve, delay or reject a settlement claim; only the committee witnesses claims. It MUST NOT refuse a valid message at the vault except under a legal restriction. It MUST NOT operate or control an admitting provider or a committee monitor. It has no access to provider-local balances.

### Public accounting

The Foundation MUST publish, without requiring an account:

| Item | Frequency | Content |
| --- | --- | --- |
| Recipient addresses | Before use | In the `FoundationKeyCertificate`, at `GET /v1/foundation/certificates` |
| `DistributionStatement` | Each calendar quarter, per network | Signed statement of fees received, the amount distributed and each provider's entry, as defined in [distribution](./03-economics.md#distribution) |
| `VaultStatus` | Each calendar quarter | Records and bytes held, and fees retained and spent in the quarter |
| `DistributionPolicy` | At least 60 days before the quarter it governs; 14 days for a committee replacement, within the handover bounds | Approved by the release threshold; includes `vault_share_bp`, `monitor_share_bp` and the named monitors |

Anyone can check received fees against the public chains and the providers' published, committee-witnessed claims. A statement that does not reconcile is evidence for clients, operators and maintainers; it does not invalidate any message or receipt.

### Release keys

The release keys are the root of trust of a ForYou network. A release pins:

- the **release key set**: at least five `did:key` identities controlled by parties independent of each other and of the Foundation;
- a **release threshold** of at least two-thirds of the set, rounded up.

A threshold-signed object carries `release_signatures`, an array of `{release_key_id,signature}` sorted by `release_key_id` with each key at most once. It is verified against the key set that was in force at the object's own signed time (`approved_at`, a certificate's `issued_at`, `closed_at`, a policy's `approved_at`). A key-set update is verified against the set it replaces, and at least that set's threshold number of entries MUST verify. An object signed under an earlier set stays valid after the set changes only if its hash is listed in the `prior_objects` of the update that replaced that set. A retired set therefore cannot issue backdated objects.

The release keys sign release manifests, the genesis manifest, fee-schedule approvals, distribution policies, Foundation key certificates and closures, key-set updates and advisories. They sign no settlement object and hold no funds. A colluding threshold could still certify a hostile Foundation key or close an honest one. The size and independence of the set are the defence, and every such object is public.

Losing more keys than the set can spare (two of five at a four-key threshold) stops certificates, closures and schedule revisions. Settlement continues, but the only way forward is then a new genesis manifest agreed by the remaining maintainers, which is a new network. Maintainers SHOULD use at least seven keys and replace a lost key by a key-set update at once.

The set changes only by a `ReleaseKeySetUpdate` `{update_id,sequence,previous_update_id,release_key_ids,release_threshold,prior_objects,effective_at,release_signatures}`, signed by the threshold of the **previous** set under P("release-key-set-update", the update excluding `release_signatures`).

- `update_id` is `fyku2:` plus lowercase SHA256 hex of P("release-key-set-update-id", the update excluding `update_id` and `release_signatures`).
- `prior_objects` is the sorted array of the lowercase SHA256 hex of the UTF-8 JCS bytes of every release-signed object issued under the outgoing set that remains valid.
- `sequence` starts at 1 and increases by one. `previous_update_id` is null for sequence 1 and otherwise names the preceding update. `effective_at` is later than the preceding update's.

A client applies updates in order from the set in the genesis manifest. An update a client has applied is final for that client. Two valid updates with the same `sequence` and different `update_id` values are evidence that the outgoing set signed twice. A client that has applied neither MUST stop and apply none until a new release resolves it. A client that already applied one keeps it and publishes the other. A retired set therefore cannot undo an update that clients have applied.

### Foundation key certificate

The Foundation's signing key is an operational key controlled by the release keys.

- `FoundationKeyCertificate` is `{certificate_id,foundation_id,recipients,issued_at,valid_from,valid_until,release_signatures}`. `recipients` gives the settlement recipient for each network. `valid_from` is at least 30 days after `issued_at`, except in the genesis manifest, and `valid_until` is at most 366 days after `valid_from`. `certificate_id` is `fyfc2:` plus lowercase SHA256 hex of P("foundation-key-certificate-id", the certificate excluding `certificate_id` and `release_signatures`). The signatures cover P("foundation-key-certificate", the certificate excluding `release_signatures`).
- The 30 days apply to every certificate, so a recipient address can never change at short notice, whatever the reason given. After a closure for compromise, deposits to the closed key stop counting at once. Providers draw on their existing credit until the new certificate becomes valid.
- A Foundation key is **open** until a closure names it. A verifier accepts an object signed by an open key when the object's signed time (`stored_at`, `signed_at` or a statement's or status's `period_end`) lies inside the validity of one of that key's certificates. The Foundation signs vault receipts, distribution statements, vault status and log heads. It signs nothing that decides settlement. A key MAY be renewed by a further certificate.
- `FoundationKeyClosure` is `{foundation_id,closed_at,head,voided,release_signatures}`, threshold-signed under P("foundation-key-closure", the closure excluding `release_signatures`).
  - `head` is a complete `FoundationLogHead` signed by the key being closed.
  - `voided` is a sorted array of `object_hash` values of logged objects that the release keys have shown to be false, for example a statement that does not follow the formula. Each MUST be published with that evidence.
  - The release keys MUST publish a closure when a key is retired, and at once on suspected compromise.
  - `closed_at` MUST NOT be earlier than `head.signed_at`, so a closure cannot be backdated behind the log.
- After a closure, an object signed by that key is accepted only with an inclusion proof against `head.root` for a tree of `head.size` entries, and only if its hash is not in `voided`. A leaked or retired key therefore cannot produce backdated objects.
- A closure is authoritative once it verifies. A signed head with a greater `size` than `head.size` does not invalidate it, because the closed key could have signed that head afterwards with a false time. Such a head is evidence. A monitor that holds one it received before the closure was published MUST publish both, and the release keys then issue a corrected closure or explain the difference. The same applies to two heads that show a rewritten log: monitors publish them and the release keys MUST close that key.
- A deposit counts when it pays the recipient of a certificate at or after that certificate's `valid_from` while its key is open, so a certificate that merely runs past `valid_until` without a closure does not stop funding.
- The release keys MUST keep a certificate valid at all times. They SHOULD keep a second, standby certificate for a different key and different recipients valid as well, so that a closure for compromise never leaves providers without a recipient to deposit to. If none is valid, settlement and fee schedules are unaffected, and vault receipts and distribution wait.
- A `KeySuccession` alone MUST NOT change the `foundation_id` a client accepts.

The holder of a recipient key could send received fees back into a provider's settlement account. The Foundation MUST NOT do so. Every deposit and every outgoing transfer is public on the chain, and policy monitors MUST report any deposit funded from a recipient address.

### Foundation log

The Foundation keeps an append-only log of every object it signs: vault receipts, distribution statements and vault status. Every logged object can be fetched by its hash.

- Entry i is a `FoundationLogEntry` `{index,kind,object_hash}`, where `kind` is `vault_receipt`, `statement` or `vault_status`, `object_hash` is the lowercase SHA256 hex of the object's UTF-8 JCS bytes including its signature, and `index` counts from 0.
- The log root over the first `size` entries is the Merkle Tree Hash of [RFC 6962 section 2.1](https://www.rfc-editor.org/rfc/rfc6962#section-2.1) with SHA-256, where leaf i is the 32 bytes of entry i's `object_hash`.
- At least once every 24 hours in which the log grew, the Foundation signs a `FoundationLogHead` `{foundation_id,size,root,signed_at,foundation_signature}` under P("foundation-log-head", the head excluding `foundation_signature`). Heads are served with the log. Two valid heads from one key where the smaller log is not a prefix of the larger are proof that the log was rewritten.
- The log is served at `GET /v1/foundation/log`, its heads at `GET /v1/foundation/log/heads` and inclusion proofs at `GET /v1/foundation/log/proof/{object_hash}?size={n}`, as listed in [economics](./03-economics.md#foundation-publications). A proof is the RFC 6962 audit path for the entry in a tree of `size` leaves.
- Monitors named in the distribution policy MUST mirror the log, keep every signed head and report any inconsistency.

### Genesis manifest

A network exists once the release keys sign a `GenesisManifest`: `{release,release_key_ids,release_threshold,foundation_key_certificates,fee_schedules,fee_schedule_approvals,distribution_policy,signed_at,release_signatures}`. It is served at `GET /v1/foundation/genesis` and signed under P("genesis-manifest", the manifest excluding `release_signatures`). It fixes:

- the release key set;
- the first Foundation key and recipients;
- fee schedule 1 with its dates and `schedule_id` values for both networks;
- distribution policy 1.

`release` is `"1.0"`. Clients pin the manifest's release key set. Until it is signed there is no ForYou network and no party can accept funds under this specification. The repository's [settlement example](../examples/settlement.example.json) contains a synthetic manifest for testing only.

If the Foundation is unavailable, settlement is unaffected: it is decided by the committee from the chain, as defined in [settlement](./03-economics.md#the-settlement-committee).

## Version identifiers

| Identifier | Value in this release | Meaning |
| --- | --- | --- |
| Specification release | 1.0 | The frozen document, schema and vector set |
| Wire message version | `{major:2, minor:0}` | Signed in every message; selects schema and verifier |
| Signing prefix | `ForYou/1/` | Domain-separation prefix for signatures |
| ID prefixes | `fy1:`, `fyd1:`, `fye1:`, `fyfs2:`, `fysc2:`, `fyrd2:`, `fyks2:` and others | Opaque type tags; they do not track the release or wire version |
| Fee schedule | `schedule_id` | Immutable identity of one approved schedule |

These identifiers are independent. A release MUST NOT rename an existing identifier, label or route.

## Versioning and unknown fields

- Every signed object is closed: it contains exactly the fields its version defines. Any new field, including an optional one, requires a new minor version.
- An implementation MUST select the schema and verifier for a message's signed `{major, minor}` before interpreting it, MUST reject a version it does not support, and MUST reject an unknown field under a supported version.
- An implementation MUST NOT strip, reserialize, relabel or downgrade signed content to make it acceptable.
- A minor version is additive: every object valid under the previous minor version of the same major version stays valid. It is still unreadable to an implementation that does not support it.
- A change that makes a previously valid representation invalid, or changes signing or verification rules, requires a new major version and a published migration plan.
- A frozen artifact MUST NOT be replaced in place under its existing version or digest.
- The end of support for an old version does not invalidate its historical signatures. Clients that verify historical records keep the version-specific verifiers.

A release consists of a manifest listing every artifact path with its SHA-256 digest, the specification release, the wire versions, the release key set and its threshold. At least the threshold number of release keys MUST sign the manifest. The key identifiers, algorithm and verification procedure MUST be published. Release keys are distinct from `foundation_id`. Clients choose which release keys they trust; a signature alone does not prove authority. No change on the main branch activates anything.

## Release and fee schedule calendar

| Event | Rule |
| --- | --- |
| Minor (additive) release | At most one every 6 months |
| Major (breaking) release | At most one every 12 months, with a migration plan |
| Fee schedule review | Every 6 months, Bitcoin and Ethereum together |
| Fee schedule publication | At least 60 days before activation; 14 days under the drift rule |
| Fee schedule activation | One instant for both networks |
| Provider adoption of a schedule | Mandatory at the activation instant; a provider cannot choose, decline or delay it |
| Quote issued before activation | Keeps its amount until the quote expires |
| Support for the previous major version | At least 12 months after its successor |
| Deprecation notice | At least 90 days before removal |
| Proposal review | At least 30 days, with two independent implementation reviews |
| Emergency advisory | Expires or receives public review within 7 days |

- A release MAY be delayed or skipped. A review does not require a change.
- A security release MAY occur outside the cadence with a published rationale. It MUST NOT change a fee.
- A shorter deprecation interval is permitted only for a security restriction whose advisory states the reason, the affected function and the alternative.
- Nothing is activated remotely. Operators and clients install releases themselves. A provider that does not apply the schedule in force issues quotes that conforming clients reject.

## Fee schedule governance

The fee formula belongs to a release. The rates are set by release-approved schedules within the bounds in [economics](./03-economics.md#denominations-and-versioned-fee-schedule). Neither belongs to a provider.

- A schedule is valid only with a `FeeScheduleApproval` signed by the release threshold. Clients MUST reject a schedule without it, or one outside the revision bound.
- Both networks' schedules are revised together with one activation instant. A schedule revision needs no new specification release; a change to the fee formula does.
- A schedule stays in force after its `expires_at` until a successor takes effect.
- A proposal MUST state the `schedule_id`, base fee and per-KiB fee for each network, the activation instant, the reference prices used and a reproducible calculation.
- From the activation instant, every new quote uses the new schedule. A quote issued earlier keeps its amount and schedule until its signed expiry; a provider MUST NOT substitute a different amount.
- A schedule change MUST NOT reprice a confirmed balance, an issued receipt or a published record.
- There is no exchange-rate oracle and no automatic adjustment. The only off-calendar change is the drift rule in [economics](./03-economics.md#denominations-and-versioned-fee-schedule): 30 consecutive days below half or above twice the target, 14 days' notice, both networks together.
- An emergency advisory MUST NOT change a fee or a recipient address.

Schedule 1 and its amounts are fixed in [economics](./03-economics.md#denominations-and-versioned-fee-schedule).

## Proposals, maintainers and advisories

- A proposal has a public identifier, motivation, threat analysis, economic and privacy impact, interoperability tests and review history. Acceptance requires the review in the calendar and a public maintainer rationale recording dissent and compatibility consequences.
- Maintainers MUST disclose conflicts of interest and recuse themselves from decisions on their own exceptions. Maintainer succession uses a published nomination and review process and documented release-key revocation.
- Anyone MAY fork the specification under its license. A fork that pins a different release key set is a different network for settlement purposes.
- An emergency security advisory is signed by the release keys and identifies affected versions and mitigations. It MUST NOT impose a content ban, move funds, seize an account, change a fee or change ranking. Clients and operators choose whether to act on it.
- Security reports have a private contact, an acknowledgment target of three business days and coordinated disclosure.

## Future cryptographic migration

This release supports only the Ed25519 `did:key` representation in [the protocol](./02-protocol.md). A `KeySuccession` is an advisory identity link; it does not preserve a DID, and recovery after loss of a key is impossible.

Adding or replacing an algorithm requires a new major version that defines:

- stable algorithm and key identifiers, canonical encodings, verification rules and test vectors;
- domain separation binding the algorithm identifier, version, key identity and signed object;
- rejection of unknown algorithms, malformed keys and conflicting algorithm labels;
- how old and new records coexist and how historical signatures stay verifiable.

A verifier MUST NOT retry a failed signature under another algorithm and MUST NOT accept an unsigned algorithm negotiation. A client MUST keep its highest trusted policy unless the user explicitly resets it.

## Quality evidence and independence

[Quality evidence](./09-quality.md) owns report formats. Governance adds:

- Any party MAY publish a signed quality report. A signature identifies the reporting key; it does not establish independence or accuracy.
- A report affects fee distribution only when its monitor is named in the signed `DistributionPolicy`, and only as defined in [distribution](./03-economics.md#distribution). No report triggers any other payment, global trust decision or mandatory ranking.
- The Foundation MUST publish, with each `DistributionPolicy`, the named monitors, their selection criteria and any funding or ownership relationship between a monitor and the Foundation or a provider.
- A default provider or monitor list MUST identify who controls it, its criteria and its update policy. Clients MUST let the user inspect, replace or disable defaults.

## License

The specification, schemas, examples and tests are licensed under the MIT License; the [LICENSE](../LICENSE) file is the grant.

## Release checklist

Fee amounts, assets and the fee recipient are decided. Release 1.0 is frozen only when all of the following are published:

| Requirement | Evidence |
| --- | --- |
| Independent implementations | Two independently written implementations pass the vectors and interoperate end to end, including settlement proofs |
| Security review | An independent review of the protocol and both implementations, with findings resolved or disclosed |
| Legal review | Review of the Foundation's role, the collection-agent model and contributor provenance for every artifact |
| Measured capacity | Measured results against the anonymous read floor in [portability](./05-portability.md#read-capacity-and-caching) and the settlement and vault delivery deadlines |

## Appendix: Project process (nonnormative)

This appendix records how the project plans its first deployments. It creates no conformance requirement.

The first public pilot runs in explicitly selected markets with named accountable operators that completed the assessment in the [operator compliance guide](./11-operator-compliance-guide.md#per-market-assessment-before-operation). It needs two independently controlled funded providers, two independent client implementations and separately controlled discovery sources. Test users can decline telemetry; published results are aggregate.

| Gate | Evidence |
| --- | --- |
| Protocol | Cross-client BTC and ETH funding, fee calculation, admission, publish and download; updates with verified same-author targets and the three-step fork rule; replies to any version; malformed-input and concurrency tests |
| Settlement | Prepaid deposits, claim chain, sum-tree proofs, committee audit and witnessing, equivocation handling, `pending_settlement` and `unsettled` handling |
| Retention | Declared retention honoured, 410 after expiry, vault delivery within 7 days after settlement, restore from the vault |
| External media | No pre-consent loads; private-address and DNS-rebinding defenses; no credentials or referrer; whole-object digest verification before decoding |
| Exit | Restore and new publication with the old provider and preferred directory offline |
| Recovery | Root backup restore, delegate revocation, recovery of acknowledged restrictions, reorganization and retry states, third-party payer disputes |
| Quality evidence | Independently chosen monitors, published methods, reproducible availability and restore results, disclosed conflicts |
| Compliance | Role and market assessment; exercised notices, appeals, removals and incident response |
| Independence | Provider, directory and index outage exercise; inspectable and replaceable defaults |

Expansion stops if safety response, payment handling, settlement or recovery fail, and the failure and its remediation are published before exposure increases. The Foundation and operators disclose actual funding sources and losses; a fee or prepaid balance is not evidence that a provider or the vault is self-sustaining.
