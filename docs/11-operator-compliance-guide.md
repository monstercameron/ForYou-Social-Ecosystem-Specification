# Operator compliance guide (nonnormative)

This guide is nonnormative guidance for operators. It never overrides docs 01–07 and 09, the API catalog or the schemas; where it differs from them, they prevail. It describes one workable way to run the free rights and claims channel, case management, per-market assessment, incident handling and funding disputes required in outline by [compliance](./04-compliance.md). Uppercase requirement keywords below state what an operator adopting this guide's procedure does; they create no conformance requirement for other implementations.

Legal summaries are an issue checklist, not a legal opinion. They were checked against the linked official guidance on 2026-11-11. Each operator remains responsible for its actual role, establishment, markets, users, processing and fund flows.

## Accountability and legal classification

Applicable law may extend beyond server location. No universal legality label, guaranteed erasure across strangers, or automatic exemption from decentralization is available. No regulator or project maintainer can be represented as certifying compliance without actual authorization.

The per-record fee is an anti-spam admission hurdle that the provider collects as a collection agent for the ForYou Foundation. That description does not determine the legal nature of an operator, transaction or obligation: assess the actual payment flow, representations, recipient relationships, retention commitments and applicable consumer, financial, tax and privacy law. Do not imply the fee label waives rights or guarantees lawful operation.

An author may prepay BTC or ETH into a provider-local balance, from which that provider debits each admitted post's fee and settles it to the Foundation. Balances are scoped to that author, provider and network, are not transferable between providers or users, and are not a protocol token. Those labels do not resolve whether an operator's activities constitute custody, payment services, stored value or another regulated activity. Before offering balances in a market, assess the actual wallet control, beneficial ownership, safeguarding, money-transmission or payment licensing, sanctions, tax, consumer and recordkeeping obligations with qualified local counsel, including the operator's position as a collection agent holding amounts owed to the Foundation. Make the disclosures listed in [custody and balance disclosure](./04-compliance.md#custody-and-balance-disclosure) before acceptance.

An author root key establishes control of a protocol identity, not necessarily the ownership of assets sent by someone else. Give third-party payers and other affected claimants a free, separately verified rights route; investigate competing claims and independently verify standing and destination authority before return or redirection. Protect legitimate requests during account suspension or root-key loss, without disclosing another person's private information or allowing account takeover.

Only credit a balance after the applicable network confirmation or finality conditions and authenticated transfer attribution. Preserve the obligation and user-visible transaction history through uncertainty, failure, reconciliation and reorganization. Payment receipt, account authorization and any legal disposition of funds are separate decisions.

## Per-market assessment before operation

Maintain a role-by-market assessment for ingress, public storage and download, optional indexing, owner exports and payments. For each record: operator or entity, features and audiences, establishments and targeted markets, service classification, applicable laws and sources, controller/processor analysis, required contacts or representatives, reporting/notice/appeal obligations, age and child-safety measures, lawful processing bases, transfer mechanisms, retention and preservation duties, payment/tax/consumer obligations, counsel reviewer, review date and next review. Record unknowns explicitly. Review at least every 90 days and after a material law, feature, audience or business change. Dates are review targets; statutory deadlines take precedence.

Unresolved material duties block offering the affected feature in that market. Restrict features or service exposure where lawful and effective; do not assume geoblocking conclusively removes jurisdiction. Seek clarification on conflicting obligations, document the decision, and cease the affected activity if no lawful design exists. Never export a domestic restriction to unrelated users merely for implementation convenience.

| Market checklist | Assessment and implementation required |
| --- | --- |
| EU/EEA | Classify intermediary/hosting/platform roles and size-dependent duties; implement applicable DSA notice/action, reasons, complaint and transparency requirements. Determine GDPR lawful bases, controller relationships, data-subject rights, security, impact assessments where required and international transfers. |
| UK | Assess links with the UK and regulated service scope; complete required illegal-content and children's access/risk assessments and safety processes. Map applicable privacy and age-assurance duties independently. |
| United States | Assess relevant federal and state obligations. For applicable copyright safe harbors, implement eligibility conditions, designated-agent and notice/counter-notice handling. Separately assess child safety/reporting, privacy, consumer protection, sanctions and payment licensing obligations. |
| Australia | Assess whether the actual service is an age-restricted social media platform, applicable account-age measures and other online-safety obligations. Do not assume a decentralized service is excluded. |
| Other markets | No inferred approval: complete the same assessment before targeting them, including data localization, prohibited content, age, payment and consumer requirements. |

Disclosure requirements in the core do not exempt nonprofit, volunteer or individual services from laws applicable to their actual activities.

## Funding disputes, recourse and privacy

A confirmed deposit funds a provider-local balance; it is not a payment for a specific post or a guarantee that a later admission will succeed. For a valid authorized admission, the operator either durably records the single debit and retrievable signed admission receipt together, or leaves the corresponding funds available in that balance. If service cannot be provided, supply an accessible, free dispute and return route subject to separately verified claims and applicable law. Publish expected response times and escalation channels; do not promise that a protocol can compel an insolvent or dishonest operator to pay. A missing response alone proves neither payment nor dishonesty, and a signed complaint is the complainant's assertion, not an adjudicated finding.

Investigate underpayments, overpayments, duplicates, late transfers, misdirected transfers and disputed attribution using a documented exception process. Do not silently treat an unmatched transfer or excess as forfeited, impose an undisclosed penalty, credit the same transfer twice, or disclose a claimant's evidence to another claimant without authority. Preserve evidence and any rights and remedies under applicable law; provide a separately verified way to claim or contest the transfer, including for third-party payers. Return amounts, network costs and resolution of competing claims depend on applicable law and the rules in [economics](./03-economics.md). A confirmation reorganization does not invalidate an already issued admission receipt or reverse a published message; the amount debited for that receipt remains owed to the Foundation under [settlement](./03-economics.md#settlement).

Before payment and before sharing a complaint, warn that public-chain transactions, provider deposit addresses, timing, transaction amounts, exchange records and an author DID can be correlated. A fresh address does not make a transaction anonymous, and even a redacted transaction identifier can allow re-identification from public information. A third party can fund an invoice, subject to applicable law and independently verified claims, without obtaining posting authority merely by paying. Do not put DIDs, private account identifiers, drafts, customer references or dispute details into on-chain transaction data. Minimize and protect the off-chain mapping of a deposit to an author, and limit its use and retention to documented lawful purposes.

Evidence for a failed admission or dispute remains private by default. A person may choose to disclose evidence to an independent monitor after a specific, informed warning about permanent publication and linkability, subject to the rights of other affected people and applicable law. Obtain any necessary authorizations separately; neither payment nor filing a complaint is blanket consent to publish another person's financial information. A monitor verifies the scope and authenticity of what it can, labels unresolved claims and omissions, and avoids publishing confidential records, personal data, transaction-to-DID links or protected material without a lawful basis. An invoice, transfer and lack of a response, even if authentic, do not by themselves establish provider fault or entitle a monitor to the provider's private ledger.

## Notices, decisions and appeals

Provide accessible `POST /v1/notices`, `POST /v1/rights-requests`, `POST /v1/appeals` and web or alternative routes without requiring a paid membership, blockchain transaction, root key or account merely to submit. Anonymous safety reports can initiate review, while legally prescribed notices retain their prescribed requirements. Do not encourage uploads or public replication of prohibited evidence. Screen authority and scope of orders; preserve authenticated evidence privately with restricted access.

### Bounded intake and recovery

**Request.** The three HTTPS routes accept the closed IntakeRequest schema, respectively requiring kind `notice`, `rights_request` or `appeal`. Rights requests add requested_right; appeals add decision_reference.

| Field | Bound |
| --- | --- |
| operator_id, request_id, accept_until, kind, form_id, form_version, form_digest | Common required fields; operator_id MUST match the selected endpoint |
| locators | At most 16 strings of at most 4096 UTF-8 bytes each |
| statement | Inert text, at most 65536 UTF-8 bytes |
| evidence_refs | At most eight `{locator,description}` objects, bounded to 4096 and 2048 UTF-8 bytes |
| regional_fields | At most 32 string fields, each value at most 4096 UTF-8 bytes, restricted to the operator's published form ID and version |
| contact (optional) | `{kind:"email",address}` with at most 320 ASCII bytes; not verified identity |
| Whole request | At most 256 KiB of uncompressed exact UTF-8 JCS and depth eight, regardless of field limits |

Reject duplicate keys, unknown envelope fields and binary attachments. Schema character bounds are preliminary; enforce the UTF-8 byte limits separately. A locator or decision reference is not proof the target exists or the submitter has authority.

**Recovery secret.** For each submission, the client generates a fresh 32-byte CSPRNG recovery secret, encodes it as canonical unpadded base64url recovery_key, and computes request_id as canonical base64url of SHA256(P("intake-id", `{operator_id,recovery_key}`)). Send recovery_key only in the `ForYou-Intake-Key` HTTPS header, never in a URL, body or receipt. Verify canonical encodings and recompute request_id before lookup. Do not forward this header across redirects or retain it in logs, traces, analytics, crash reports, notifications or ordinary exports. The operator stores the derived request_id and accepted artifacts, not the raw secret. The client may retain the secret in protected owner-controlled storage for recovery and MUST explain that losing it ends this recovery method; any backup or export of the secret requires explicit user control and protection. The secret authorizes recovery only of this submission's own request and receipt; neither it nor a case ID grants party status, access to another person's data or authority to act on the underlying content.

**Acceptance and receipt.** For a new request, require `now < accept_until <= now + 600 seconds` using a checked clock. This bounds initial submission replay; it is not a legal filing deadline. Before acknowledging, atomically persist the exact request, route, first durable received_at and signed IntakeReceipt `{operator_id,request_id,request_digest,received_at,status:"received",signature}`; request_digest is SHA256 of the exact request JCS bytes, and signature covers P("intake-receipt", receipt excluding signature).

| Case | Response |
| --- | --- |
| New request durably stored | 201 with the receipt |
| Exact retry of a committed request, after verifying the secret, before new-request expiry or capacity checks | 200 with the original receipt |
| Same ID with a different body or route | 409 without mutation |
| Absent expired request | 410; never creates a new submission |
| Durable intake unavailable | 503 without claiming receipt |
| Rate or work limit | 429 with retry information |

The receipt proves receipt only, not the truth, sufficiency, standing or entitlement of a claim. Do not backdate received_at from client fields; preserve original time through queueing and retry, and assess legal timeliness under the applicable procedure. Keep idempotency records through the promised recovery period and until accept_until is irreversibly past under protected clock and recovery state.

**Recovery route.** `GET /v1/intake/{request_id}` requires the same secret header and returns IntakeRecovery `{request,receipt}` only for that submission after current disclosure checks. It returns neither case details nor other parties' material. Unknown and nondisclosable records use the same bounded 404; case IDs and public message IDs are never recovery credentials. Publish the recovery retention period before submission: at least 30 days and while the submission remains pending, unless a specific lawful restriction prevents retention or disclosure. A separately verified alternative rights route remains available after secret loss, expiry or suspension; losing the secret does not extinguish underlying rights. No automatic redirects or public bearer URLs carry the secret.

**Client verification.** For both POST and recovery GET, the client verifies the receipt schema and signature under the pinned expected operator, exact operator_id and request_id, and request_digest against the exact locally submitted or recovered JCS request. On retry it also compares the original route and body; on recovery it verifies the returned request/receipt pair and locally retained request when available. A mismatch is not an acknowledgment. All intake POST and GET responses, including errors, carry `Cache-Control: no-store`; shared, browser, service-worker and CDN caches MUST NOT store or replay them. Reapply secret authorization and current disclosure on every recovery, and never put secrets in cache keys or logs.

**Retries after policy change.** Apply current lawful disclosure controls to an exact POST retry before returning its receipt as well. Authenticate the secret and compare the previously committed exact route and body before applying new-submission form-version or eligibility checks; a retired form or changed new-intake policy cannot erase a timely acknowledged retry. Retain the accepted form's exact field definitions and version needed to interpret its historical submission; never silently reinterpret it under a later form. Where disclosure is prohibited, use the same nonrevealing refusal as for an unknown record and preserve the separately verified rights pathway.

**Durability.** Before acknowledging an intake receipt, protect its committed request, route, original received_at and idempotency binding in a separately protected recovery domain with an authenticated checkpoint or equivalent recoverable journal. After rollback, failover or restoration from an older backup, reconcile through the latest acknowledged intake checkpoint before reopening affected intake and recovery; missing or uncertain state fails unavailable, never absent. Preserve lawful deletion, retention and restriction decisions and the separate rights fallback. This prevents a replay from creating a second received_at and protects promised recovery of timely submissions, without implying recovery after loss of all independent copies.

Conflict detection for a changed body under an existing request_id is guaranteed while its idempotency record is retained. After lawful compaction, the protected freshness state prevents an old expired body from becoming a new submission, but is not a permanent registry of every prior ID. Clients MUST generate a fresh secret for every new submission and never reuse it with altered fields.

**Standing.** Receipt does not verify standing. Before disclosing case information, associating a claimant with a party, or executing an action, separately verify the relevant authority using the case's scoped procedure. A root signature proves control of its DID, not every underlying fact; an intake secret proves only control of that submission. A decision reference, case ID, email address or copied notice alone proves neither. Non-account subjects and representatives use proportionate independently verified workflows. An unverified appeal remains pending verification without revealing whether the referenced case exists, while its original intake time is preserved.

**Forms.** Publish supported form IDs, versions, field definitions and alternative channels. Each `(operator_id,form_id,form_version)` identifies one immutable IntakeForm specifying kind, required and allowed regional fields and their meanings.

| Item | Rule |
| --- | --- |
| form_id, form_version | ASCII letters, digits, underscore and hyphen only; at most 128 and 64 characters |
| `GET /v1/intake-forms/{form_id}/{form_version}` | On the pinned HTTPS operator; returns the exact uncompressed inert UTF-8 JCS IntakeForm, at most 1 MiB; no redirects or executable interpretation |
| Field definition | name, required, max_utf8_bytes and inert description; names are unique |
| Descriptions, instructions | At most 2048 and 65536 UTF-8 bytes |
| form_digest | Lowercase SHA256 hex of the exact form bytes |

Before new intake, verify the operator, offered form, kind, route, digest, unique names and each required or allowed field and byte limit; a change requires a new version. The client retains the exact bytes or authenticated digest with the submission; the request digest in the signed receipt binds form_digest. Preserve the accepted definition for historical interpretation even after retirement. The generic envelope does not itself establish statutory sufficiency; required declarations and verification follow the applicable procedure. Evidence references are untrusted pointers, never permission for automatic fetching, callbacks, mirroring or executable content. Additional evidence uses a separately authorized bounded confidential channel; a technical form limit does not eliminate required alternatives. Send no sensitive information to an unverified contact; any verification message is minimal and rate-limited.

The form's operator_id MUST equal the pinned operator, and its form_id and form_version MUST exactly equal both the requested path components and the intake request fields; its kind MUST equal the request kind and corresponding route. Refuse mismatches instead of silently selecting a different form.

**Capacity.** Before allocating durable state, enforce disclosed aggregate and per-source limits on request bytes, pending-case and stored-byte counts, queues, concurrency, parsing, cryptography and notifications. Reserve separately funded capacity for authenticated follow-up, appeal recovery and emergency triage; a caller-selected urgency label cannot bypass limits. Return bounded 429 with retry information or 503 on saturation without inventing acknowledgment. Publish independently provisioned emergency and statutory fallback channels. These controls mitigate abuse but cannot promise availability under distributed attack or extinguish substantive rights.

### Case management

An internal case has a random unguessable ID and states received, triaged, investigating, decided, appealed, reviewed, closed. A decision records:

| Decision field | Values |
| --- | --- |
| operator, affected locators, scope, decided_at | As decided |
| basis_kind | law, terms or security, with the specific basis |
| action | none, restrict, remove, deindex, preserve, restore |
| review_at | Where the action is temporary |
| reasons, appeal route, applicable deadlines | As owed to the affected party |

Notify affected parties where lawful; explain withheld notice under the applicable exception. Access to cases requires verified ownership or party authorization, not knowledge of a message ID. Externally published aggregates MUST NOT reveal reporters, victims or prohibited content. A signed decision proves who issued it, not that it is correct or binding on another operator.

Case authorization is specific to the case, operation and fields, not merely membership in a party role. A verified reporter may receive their own submission and the status and reasons authorized for them; an affected publisher or other subject receives only the material authorized for their notice, rights request or appeal. Neither role automatically receives another party's identity, contact details, private attachments, identity-verification evidence, internal notes or security information. An assigned reviewer receives only the scope needed for that assignment; an unrelated staff account has no case access. Check authorization on every view, attachment, download and export, before revealing existence. Use explicit field allowlists with unknown fields denied by default; nested records and attachments inherit their own restrictions. Record any exceptional disclosure's authority, recipient, purpose and scope privately. Redacted views MUST be identified as views; never edit a signed source record and claim its original signature authenticates the changed bytes. These controls also apply to notifications, appeal handoffs and case audit logs.

Provide a free appeal, correction and restoration route and an audit trail. Qualified human supervision or review is mandatory wherever applicable law requires it, including applicable DSA complaint safeguards; feasibility may qualify only additional voluntary independent review. Deadlines, evidence and notice forms follow the applicable regional process, not one invented universal timer. Court preservation, copyright counter-notices and emergency reporting require distinct workflows. Document reasons if lawful preservation prevents deletion; isolate the retained material and prohibit unrelated processing.

### Evidence handling

Evidence references are never allowed to trigger unrestricted fetching or execution by a server or agent. Apply [the protocol specification's](./02-protocol.md) destination, redirect and resource controls, inert rendering and no ambient credentials. Treat embedded instructions as untrusted data. Prohibited-material evidence goes only through an authorized, restricted intake and preservation process; never automatically mirror it into normal logs or model context.

## Personal-data inventory and rights handling

Inventory public posts, identifiers, content hashes, indexes, logs, backups, funding records and owner-only export records; neither a hash nor encryption automatically makes data anonymous. Define purpose, lawful basis where required, responsible parties, access controls, recipients, transfer safeguards, retention duration and deletion or preservation procedure for each category. Public visibility is not unlimited consent for scraping, profiling or model training. Legal assessment MUST cover independent replication and delivery to the Lifetime Vault; separate app processing has its own responsibilities.

Offer access, export, correction, erasure and restriction requests through separately verified rights processes; no core author-delete operation is implied. Possession of a social root key can establish control of an identity, but people described in someone else's post need an alternative identity-verification path proportionate to the request. Requests MUST NOT require unnecessary identity documents. Honor required response deadlines and extensions with reasons. Remove eligible data from primary stores, indexes, caches, embeddings and derived profiles, and propagate legally required notifications to known processors and recipients. Track acknowledgments and failures; do not guarantee deletion by unknown independent hosts. Backups need a documented expiry and restore-time suppression so deleted records are not silently resurrected. Lawful holds are narrowly scoped, access-controlled and periodically reviewed. A local suppression record may contain personal data; retention MUST be justified.

A provider's retention duty runs to each record's `retain_until` under its signed RetentionDeclaration, as defined in [economics](./03-economics.md#retention-and-the-lifetime-vault). Assess that commitment, and any longer period the operator declares, against applicable storage-limitation and erasure rules before declaring it.

## Age measures

Age measures need to satisfy applicable law while minimizing collection: prefer a narrowly scoped age result from a suitable independently assessed service when legally sufficient; do not promise that a cryptographic age credential automatically meets local requirements. Assess linkability, retention and vendor failures. Client preferences, optional remote ranking and any private sync are separate application services, outside the core protocol, with their own disclosure and data-flow assessment.

## Incidents and personal-data breaches

Designate an accountable incident lead and escalation contacts, including suppliers. Maintain procedures for detection, containment, access revocation, minimally necessary evidence preservation, incident scope and risk assessment, processor-to-controller notification, and regulator and affected-person notices under the actual applicable thresholds and deadlines. Maintain a role and market notification register and timed drills; do not substitute a universal protocol deadline for law. Coordinate recovery, backup suppression and vendor remediation; document reasons for notification or non-notification, restricted investigation records, and an appropriately redacted postmortem. Protect reporters and prevent incident evidence from becoming a second disclosure.

Official references: [Commission breach obligations](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/obligations_en) and [DSA Article 20](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32022R2065). A prior agreement does not prevent necessary prospective privacy or legal changes; provide dated notice and preserve accrued lawful rights without continuing unlawful processing.

### Recovery checkpoint procedure

This is one design that satisfies [recovery of acknowledged controls](./04-compliance.md#recovery-of-acknowledged-controls).

Before acknowledging a disclosure restriction, legally required deletion or delegation revocation as effective, durably commit its authorized scope and ordering in the responsible operator's control state and advance an authenticated recovery checkpoint. Retain the checkpoint and sufficient control state in a separately protected failure and rollback domain from ordinary content backups; another file restored from the same old backup is not independent. The checkpoint identifies operator, control-state generation, committed sequence and integrity commitment. Updates and acknowledgments MUST be ordered so a crash cannot leave an acknowledged control beyond the recoverable checkpoint. If durability cannot be established, report failure or unknown completion and support an idempotent retry; never falsely acknowledge success. Do not put private case evidence or a public list of restricted IDs in the checkpoint. This is operator recovery state, not a global registry or a shared content ban.

After backup restore, failover or suspected rollback, keep affected public delivery, owner disclosure and new delegated issuance closed until the operator verifies the current independently retained checkpoint and reconstructs control state through it, without missing, conflicting or reordered records. Reconcile content, indexes, public snapshots, staged exports and caches against that state before reopening. A well-formed record that follows the verified checkpoint in sequence was committed but never acknowledged: the crash came between the commit and the checkpoint. It is not missing, conflicting or reordered history. Recovery applies such records in order and advances the checkpoint through them before reopening; the caller of each was never told it took effect and retries idempotently. A stored history shorter than the checkpoint, or one whose records up to the checkpoint do not reproduce its integrity commitment, still blocks recovery. Continue serialization with live control updates during recovery; a checkpoint verified before a concurrent update is not permission to skip it. A lost or unverifiable checkpoint, incomplete history or uncertain scope blocks the affected operations with an unavailable result; uncertainty covering the whole operator blocks those operations operator-wide. Unaffected scopes may continue only where their isolation and current control state are independently demonstrated. Restored data does not restore revoked authority. Only a separately authorized, durably recorded action can lift a reversible restriction; a legally required deletion is not silently reversed by backup repair, and delegation revocations remain irreversible under the protocol.

Minimize retained recovery identifiers and apply the retention and hold assessment above. Compaction is allowed only into verified current control state preserving the effects and integrity of all acknowledged controls; it MUST NOT reset freshness or turn missing history into permission. Exercise restoration from a backup older than acknowledged deletion and revocation, checkpoint loss, conflicting generations and control updates concurrent with reopening. Signatures alone do not prove an operator honest or guarantee recovery after loss of every independent copy.

## Shared signals

Deny-list and hash-list signals carry issuer, scope, provenance, version and correction or revocation route; they are evidence to assess, not automatic global law. Restricted lists and evidence MUST NOT be publicly exposed. Evaluate false positives, list poisoning, adversarial reporting and disproportionate geographic scope. No automatic user-wide ban from an unverified signal. Mandatory actions are implemented by the accountable operator under its applicable duties.

Ordinary availability failover remains supported. Do not implement a default "find an unregulated host" bypass for a legal restriction, and do not silently relay sensitive report details during fallback. An unaffiliated client may offer neutral user-selected alternate sources consistent with its own applicable duties. Another host's `legal_restricted` response is not a global stop instruction, and unavailable alternatives are not proof of illegality.

## Quality-monitor privacy and accountability

Independent monitors and provider-funded monitors are separate actors with their own processing and disclosure duties. A monitor MUST disclose its identity, method, observation period, funding, ownership ties and material conflicts so a client can evaluate the report. Publish reproducible raw observations only where lawful and with minimized data; do not disclose private reader histories, IP addresses, account mappings, confidential notices or protected material merely to substantiate a score. A signed report attributes an assertion to its signer; it is not evidence that a regulator, provider or project has certified its truth.

Use bounded, authorized public retrieval and restoration checks, respect current legal restrictions and security limits, and record inaccessible, failed or inconclusive observations honestly instead of classifying every restriction as a provider fault. A monitor's funding source or score gives it no right to private data or to command another provider's content decisions. Any claimed independence requires evidence beyond different keys. Reports and default lists MUST disclose their scope and limitations; clients remain free to choose, reject or replace them. How quality reports enter the Foundation's distribution amounts is defined only in [economics](./03-economics.md#distribution).

## External-media boundary

ForYou stores text and external links, not media bytes. This technical boundary is not a legal exemption: assess obligations concerning linking, indexing, notifications and any app-operated display, proxy or CDN according to actual roles and markets. A notice can restrict or remove a locally stored link under applicable duties; it does not delete the remote file. Communicate only necessary information to a separately responsible media host where appropriate and lawful, without promising its action. A user or app that also operates media hosting assesses that service separately; do not advertise the ForYou protocol as certifying it.

## Verified sources and scope limits

- [European Commission DSA Q&A](https://digital-strategy.ec.europa.eu/en/faqs/digital-services-act-questions-and-answers): obligations depend on the intermediary/platform role, with additional duties for larger services; this is not one universal platform checklist.
- [European Commission data-subject rights](https://commission.europa.eu/law/law-topic/data-protection/information-individuals_en): rights and exceptions, including erasure, portability and informing other controllers in applicable circumstances.
- [Ofcom compliance guide](https://www.ofcom.org.uk/online-safety/illegal-and-harmful-content/guide-for-services): scope and ongoing risk and safety assessment, including services outside the UK.
- [U.S. Copyright Office section 512](https://www.copyright.gov/512/): conditional safe harbors and notice/counter-notice processes, not blanket immunity.
- [Australian eSafety FAQ](https://www.esafety.gov.au/about-us/industry-regulation/social-media-age-restrictions/faqs): applicability of social-media age restrictions requires service-specific assessment.
- [FinCEN CVC guidance](https://www.fincen.gov/resources/statutes-regulations/guidance/application-fincens-regulations-certain-business-models): evaluate actual money-service activities; labels and decentralization do not determine classification.
- [EDPB blockchain guidance](https://www.edpb.europa.eu/documents/guideline/guidelines-022025-on-processing-of-personal-data-through-blockchain_en): identifiable public keys and transaction metadata may be personal data; assess the specific processing and architecture.

These sources are not exhaustive and do not substitute for local legal review. Operators retain responsibility for tracking changed law and updating their implementation.
