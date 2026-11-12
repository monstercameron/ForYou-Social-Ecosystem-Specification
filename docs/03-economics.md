# Fees, settlement, distribution and retention

## Purpose

The protocol charges a specification-set fee for each distinct post, comment or update. The fee is an anti-spam hurdle. It does not buy audience reach or ranking, and it is not a price set by a provider.

| Rule | Value |
| --- | --- |
| Who sets the fee | The specification: a schedule approved by the release keys |
| Who collects it | The admitting provider, from the author's provider-local prepaid balance |
| Who receives it | The ForYou Foundation, in full, through [settlement](#settlement) |
| Who is paid later | Providers, through quarterly [distribution](#distribution): a part of their own settled fees that grows with quality and proven retention |
| Who retains records | The provider for its declared period (at least one year) and the Foundation's [Lifetime Vault](#retention-and-the-lifetime-vault) with no scheduled expiry |
| What readers pay | Nothing |

A provider MUST NOT charge an author more or less than the scheduled fee for admission, and MUST NOT keep any part of it. A provider MAY sell separate services built on public posts; those are outside this protocol.

## Denominations and versioned fee schedule

Bitcoin is accounted in **integer millisatoshis (msat)**: one on-chain satoshi equals 1,000 msat. A millisatoshi is a bookkeeping unit, not a spendable Bitcoin output. Ethereum is accounted in **integer wei**. There is no conversion or offset between the two assets. Every displayed balance and fee MUST name its asset and unit.

For a valid post intent `I`, `billable_bytes` is the exact byte length of `UTF8(JCS(I))`. It includes text, reply, version and reference fields and media-slot metadata, and excludes `message_id`, the submission receipt and the final signature. Compute with exact integer arithmetic:

```text
kilobyte_units = (billable_bytes + 1023) // 1024
fee = base_fee + per_KiB_fee * kilobyte_units
```

`base_fee` and `per_KiB_fee` are the FeeSchedule fields `base_fee_base_units` and `per_kib_fee_base_units`. A FeeSchedule is `{schedule_id,profile_major,profile_minor,revision,network,denomination,base_fee_base_units,per_kib_fee_base_units,effective_at,expires_at}`. `profile_major` and `profile_minor` equal the message version; in this release they are exactly 2 and 0. `revision` starts at 1 and increases by exactly one per network. `denomination` is `millisatoshi` for `bitcoin-mainnet` and `wei` for `ethereum-mainnet`. `schedule_id` is `fyfs2:` plus lowercase SHA256 hex of P("fee-schedule-id", the schedule excluding `schedule_id`).

Fee schedule 1 (revision 1):

| Network | Unit | `base_fee` | `per_KiB_fee` |
| --- | --- | --- | --- |
| `bitcoin-mainnet` | msat | 0 | 136 |
| `ethereum-mainnet` | wei | 0 | 48900000000 |

These amounts are about US$0.0001 per started KiB at the reference prices used when the genesis manifest was prepared (US$73,500 per bitcoin and US$2,045 per ether). They are fixed amounts in native units. Their fiat value changes with the market. No oracle or automatic conversion is defined. A post of the maximum size (1 MiB) costs 1,024 times the per-KiB fee. The `effective_at` and `expires_at` of schedule 1, and therefore its `schedule_id`, are fixed in the [genesis manifest](./06-governance.md#genesis-manifest).

Schedule rules:

- A schedule is valid only together with a `FeeScheduleApproval` `{schedule_id,approved_at,drift,release_signatures}`. `drift` is true only for a replacement under the drift rule. Each entry of `release_signatures` is `{release_key_id,signature}` over P("fee-schedule-approval", the approval excluding `release_signatures`). Entries are sorted by `release_key_id`. At least the [release threshold](./06-governance.md#release-keys) MUST verify. Neither a provider nor the Foundation can create, select, delay or decline a schedule.
- At least one of the two rates MUST be positive. Under revision n+1, the fee of a 1 KiB post and the fee of a 1 MiB post MUST each be at least half and at most twice their fee under revision n for that network. A verifier rejects a schedule outside this bound even when it is approved.
- Revisions are spaced in time, so the bound cannot be stacked. For one network, `effective_at` of revision n+1 MUST be at least 90 days after `effective_at` of revision n (30 days when `drift` is true). `approved_at` of revision n+1 MUST NOT be earlier than `effective_at` of revision n. The fee can therefore at most double or halve in 90 days on the calendar, or in 30 days under the drift rule.
- Both networks are revised together with one activation instant. `approved_at` MUST be at least 60 days before `effective_at`, or 14 days when `drift` is true.
- `approved_at` is asserted by the release keys. Clients and providers SHOULD ignore a schedule they first see after its `effective_at` until they have fetched it from `GET /v1/foundation/fee-schedules` and verified it against the release key set.
- The schedule in force for a network at time t is the approved schedule with the greatest `effective_at` not later than t. `expires_at` is the planned review instant. A schedule stays in force after it until a successor takes effect, so a missing successor never stops admission.
- A signed, unexpired quote keeps its schedule and amount until the quote expires, even after the schedule is replaced. A quote expires at most 3,600 seconds after its `preflight_at`. A schedule change never invalidates an issued receipt.
- Schedules are reviewed on the calendar in [governance](./06-governance.md#release-and-fee-schedule-calendar). The target is US$0.0001 per started KiB. Outside the calendar a replacement is allowed only under the **drift rule**: for either network, the fee's value has been below half or above twice the target on each of 30 consecutive days. The value is measured as the daily median of at least three public price sources named in the proposal, and their series is published with it.

Reject overflow, unsupported networks or schedules and invalid encodings before any mutation. Never round msat amounts away.

## Funding a provider-local balance

An author funds a prepaid balance with a chosen provider in Bitcoin or Ethereum and authorizes one debit per post. The exact objects and routes are in the [protocol](./02-protocol.md#funding-the-provider-local-balance).

- The balance is a custodial claim on that one provider. It is not a token, is not portable between providers, and is not held by the Foundation. Clients MUST disclose custody, insolvency and recovery risk before funding.
- Custody is bounded. A provider MUST NOT issue a deposit invoice that would raise an author's confirmed plus pending balance on a network above 1,000,000 times the fee of a 1 KiB post (136,000 satoshis or 0.0489 ETH under schedule 1).
- A deposit invoice funds the author's balance, not a particular post. A third party MAY pay it.
- A provider credits a balance only after it independently verifies the transfer: correct network, recipient, exact amount, success, and six Bitcoin confirmations or finalized Ethereum inclusion. Pending funds are never spendable.
- Each qualifying transfer is consumed once, atomically, across all of the provider's accounts. Each invoice produces at most one credit.
- Underpayments, overpayments, duplicates and late transfers are never silently credited or forfeited. They go to the provider's free claims channel and receive one durable disposition.
- Funding and withdrawal network fees are separate from the protocol fee and are disclosed before payment.
- Use exact integer arithmetic. Never create a negative balance, spend pending funds or cover one author's balance with another's.
- Unused balance remains a liability of the provider. The provider MUST offer withdrawal of unused funds through `POST /v1/withdrawals`. It MUST explain network fees and minimum outputs beforehand. It MUST NOT apply expiry, dormancy deductions or recurring debits.
- A chain reorganization freezes the affected unspent funds until reconciled. It never invalidates issued receipts, removes accepted posts or creates a negative balance. The provider carries any deficit.

A signed balance or credit is the provider's assertion. It does not prove solvency.

`POST /v1/withdrawals` uses fresh root [service-auth](./02-protocol.md#administrative-request-authentication) and a `WithdrawalRequest` `{provider_id,author_id,network,amount_base_units,recipient,request_id}`. It returns 202 for a new request and 200 for an exact retry, each with a provider-signed `WithdrawalStatus` `{provider_id,author_id,network,amount_base_units,recipient,request_id,status,transfer,updated_at,provider_signature}` under P("withdrawal-status", the status excluding `provider_signature`). `status` is `pending`, `sent` or `failed`. `transfer` is null until `sent`. The amount is reserved from the available balance when the request commits. It is restored once if the status becomes `failed`. Insufficient available balance returns 402 `insufficient_balance`.

## Quote and debit

1. The author composes the whole post and computes its intent and message ID.
2. The provider returns a signed FeeQuote for that exact intent under the schedule in force.
3. The client independently recomputes `billable_bytes` and the fee, verifies the schedule approval and bound, and compares provider, author, message ID, network, amount and expiry with what the user approved. It MUST reject any mismatch.
4. After the author authorizes the debit, the provider commits quote use, balance check, idempotency record, debit and signed receipt in one durable transaction.

Rules:

- If validation, capacity or the commit fails, no debit occurs.
- Admissions are keyed by `(provider_id, author_id, message_id)`. A retry returns the original receipt before any freshness, balance or capacity check. No retry debits twice.
- A changed intent needs a new quote. Each update and each comment pays its own full fee.
- A prepared but unpublished intent can be finalized at the admitting provider until 30 days after the receipt `issued_at`. After that, the provider refuses first finalization. "Finalization" in this document is the public acceptance defined in the [protocol](./02-protocol.md#acceptance-retries-and-conflicts).
- Every debited fee is owed to the Foundation from the moment of the debit, whether or not the post is later finalized. The debit reduces the author's balance. It is not provider revenue.
- The one exception is a provider-caused failure. When the provider itself caused finalization to fail, it restores the fee once to the same balance and omits that receipt from its settlement claims. The receipt then never becomes `settled` and the post never becomes public.
- `GET /v1/admissions/{message_id}` with fresh root service-auth returns 200 with the committed SubmissionReceipt for that author and message, or 404 `not_found`. A provider MUST also offer a free confidential claims channel to a funded author who cannot obtain a receipt.
- Receipts carry a random `receipt_id`. They never contain funding transaction identifiers, account identifiers or wallet secrets.

Statuses: `POST /v1/fee-quotes` returns 200 with the FeeQuote. `POST /v1/admissions` returns 201 with the SubmissionReceipt for a new admission and 200 for a retry. Errors use the common error body: 402 `insufficient_balance`, 403 `delegation_revoked`, 409 `quote_conflict`, 422 `quote_expired`, `invalid_message`, `message_too_large` or `bad_authorization`.

## Settlement

Settlement moves every collected fee to the Foundation and lets anyone check that a receipt was paid for. This makes the fee a hurdle also for a provider that admits its own posts. A provider prepays the Foundation on-chain. It then draws that credit down with signed claims, and an independent committee of monitors audits the claims against the chain. A receipt counts as paid only when it is settled.

### Settlement deposits

- A provider funds its settlement account with on-chain transfers to the Foundation's [certified recipient](./06-governance.md#foundation-key-certificate) for the network. A deposit is at least 10,000 satoshis or 10^15 wei. A smaller transfer is not counted. The minimum lets small providers settle with occasional transfers instead of one per period.
- Every deposit carries the 32-byte commitment `SHA256(P("settlement-deposit", {provider_id,network}))`. Here `provider_id` is the provider's **first key**, the key it held before any key succession. This holds on every network, also on a network where the provider's first claim is signed by a later key.
  - On Bitcoin the transaction MUST contain exactly one `OP_RETURN` output whose data is exactly those bytes, in addition to the payment output.
  - On Ethereum the transaction input data MUST be exactly those bytes, and the recipient MUST be an address with no contract code and no delegation designation.
- A deposit counts when all of these hold:
  - it has six Bitcoin confirmations or finalized Ethereum inclusion;
  - it is a successful native transfer to the recipient of a Foundation key certificate;
  - its block time is not earlier than that certificate's `valid_from` and earlier than the `closed_at` of any closure of that key.
- A deposit is credited in base units: satoshis times 1,000, or wei.
- `deposited(p, network)` is the sum of all counted deposits carrying provider p's commitment. Anyone can compute it from the chain.
- Deposited credit is not refundable and has no expiry. It belongs to the chain, not to a key. After a provider [key succession](./02-protocol.md#key-succession), the new key signs the next claims of the same chain, and deposits keep carrying the first key's commitment.
- Monitors accept a provider succession under one rule:
  - an old key has successions to one new key only. Another succession for the same old and new key with a different `effective_at` is allowed and is not a conflict, because the claim names the one it uses;
  - the new key is not the old or new key of a succession from a different old key, and no committee monitor has witnessed or followed a settlement claim signed by it other than as the continuation of this chain. A claim signed by the new key that monitors refused, including the naming claim while it waits for the succession to be verified, does not count;
  - a later succession from the new key to a third key is allowed.

  Deposits carrying the new key's own commitment are never counted for this chain. Nothing a third party sends can therefore affect a succession, and no deposit is counted for two chains.

### Claims and leaves

Each receipt is one leaf object:

```text
SettlementLeaf = {receipt_hash, schedule_id, amount_base_units, issued_at}
```

`receipt_hash` is the lowercase SHA256 hex of the UTF-8 JCS bytes of the complete SubmissionReceipt, including its signature. A leaf therefore binds one exact receipt without revealing its message.

A `SettlementClaim` is `{claim_id,provider_id,network,sequence,previous_claim_id,period_start,period_end,declaration_id,succession_id,receipt_count,total_base_units,cumulative_base_units,receipts_root,provider_signature}`.

| Field | Rule |
| --- | --- |
| `claim_id` | `fysc2:` plus lowercase SHA256 hex of P("settlement-claim-id", the claim excluding `claim_id` and `provider_signature`) |
| `provider_signature` | Over P("settlement-claim", the claim excluding `provider_signature`) |
| `sequence` | 1 for the provider's first claim on the network, then increasing by exactly one |
| `previous_claim_id` | null for sequence 1, otherwise the `claim_id` of the preceding claim |
| `period_start`, `period_end` | Half-open UTC interval of at most 24 hours. `period_start` is not earlier than the previous claim's `period_end`. Gaps are allowed; a period with no receipts needs no claim |
| `declaration_id` | A [RetentionDeclaration](#provider-retention) signed by the claim's own `provider_id`. It governs every receipt in the claim. A claim names either the same declaration as the previous claim, or one whose `effective_at` is not earlier than the previous claim's `period_end` and not later than this claim's `period_start`. For sequence 1 only the second bound applies. A declaration therefore takes effect on a chain when a claim first names it, and it cannot be backdated over periods already claimed |
| `succession_id` | null, except on the first claim signed by a new provider key. That claim names the [KeySuccession](./02-protocol.md#key-succession) from the previous claim's key to its own. The succession's `effective_at` is not earlier than the previous claim's `period_end` and not later than this claim's `period_start` |
| `receipt_count` | Number of leaves, 1 to 10,000. A busier provider uses shorter periods |
| `total_base_units` | Sum of the leaves' amounts |
| `cumulative_base_units` | The previous claim's `cumulative_base_units` plus `total_base_units` |
| `receipts_root` | Root hash of the sum tree below |

Leaf rules:

- `issued_at` lies in `[period_start, period_end)`.
- `schedule_id` names a schedule that was in force for the network at `issued_at` or at some instant in the 3,600 seconds before it, and `amount_base_units` is a possible fee under it: `base_fee + per_KiB_fee × k` for an integer k from 1 to 1,024.
- Every receipt the provider issued in the period is in the claim, except a receipt whose fee it restored under the provider-caused failure rule.

The leaves form a Merkle sum tree, so that an inclusion proof also proves that the leaf's amount is counted in the total.

- Sort leaves by `receipt_hash` in ascending order. Two leaves with the same `receipt_hash` are invalid.
- A node is a pair `(hash, sum)`. A leaf node is `(SHA256(0x00 || P("settlement-leaf", SettlementLeaf)), amount_base_units)`.
- An interior node over children L and R is `(SHA256(0x01 || L.hash || U128(L.sum) || R.hash || U128(R.sum)), L.sum + R.sum)`, where `U128` is the 16-byte big-endian encoding. A sum of 2^128 or more is invalid.
- The tree shape is that of [RFC 6962 section 2.1](https://www.rfc-editor.org/rfc/rfc6962#section-2.1): for n > 1 leaves, the left subtree holds the largest power of two smaller than n and the right subtree the rest.
- `receipts_root` is the root hash in lowercase hexadecimal, and `total_base_units` MUST equal the root sum.
- An audit path lists the sibling nodes `{hash,sum}` from the leaf up to the root. Whether each sibling is the left or the right child follows from `leaf_index` and `receipt_count` by the same split rule.

A receipt is claimed by the key that issued it. A provider that changes its key signs a key succession and cuts its period at the succession's `effective_at`:

- an honest provider stops issuing receipts with the old key at the succession;
- the old key signs the claims that cover every receipt it issued. It may sign claims until the first claim signed by the new key;
- the first claim signed by the new key names the succession in `succession_id`, and names a retention declaration signed by the new key;
- from that claim on, the chain belongs to the new key. Monitors refuse as `unknown_provider_key` a claim signed by a key other than the previous claim's key, unless it names a succession from that key to its own.

Monitors accept the succession under the rule in [settlement deposits](#settlement-deposits). Which key signs a claim is decided by the claim chain, not by the time rule for signatures in [key succession](./02-protocol.md#key-succession). A receipt is verified under the key that signed it, and it is paid when a settlement proof whose claim is signed by that same key settles.

The declaration and succession rules depend only on the claim, the claim before it and the object the claim names by its content ID. Nothing a provider signs later can change whether a claim satisfies them. This is what lets anyone prove such a fault, and it is used in the [handover](#the-settlement-committee) below.

A claim is **funded** when `deposited(p, network) >= cumulative_base_units`. A provider MUST deposit enough before it publishes a claim. Claims are published documents, not chain transactions, so daily claims cost nothing on-chain.

A provider publishes its claims. It does not submit them to anyone for approval. `GET /v1/settlement-claims?network={network}&after_sequence={n}` returns a `SettlementClaimsPage` `{claims}` in sequence order, at most 100 per response. `GET /v1/settlement-claims/{claim_id}/leaves?offset={n}` returns a `SettlementLeavesPage` `{claim_id,offset,leaves}` in tree order, at most 2,000 leaves per response. `GET /v1/settlement-claims/{claim_id}/witnesses` returns a `SettlementWitnessesPage` `{witnesses}` with every witness the provider holds for that claim. A provider MUST publish each claim within 24 hours after `period_end`.

### The settlement committee

Settlement is decided by one body under one rule. The body is the **settlement committee**: the list of monitors named in the [DistributionPolicy](#distribution) in force. The policy is approved by the release keys and names at least five monitors. None of them is controlled by the Foundation or by any provider. The Foundation receives the deposits but has no vote: it cannot approve, delay or reject a claim.

Each committee monitor audits every claim a provider publishes, on its own, from public data:

- the `claim_id`, the provider signature, and the provider key (the key of the previous claim, or its successor under the [key succession](./02-protocol.md#key-succession) the claim names, which the monitor has fetched and verified);
- the sequence, `previous_claim_id` and `cumulative_base_units` against the claim it witnessed at the previous sequence;
- the period rules, and that it first saw the claim not earlier than `period_end` and not more than 90 days after it;
- that `declaration_id` and `succession_id` satisfy the rules above, using the objects they name;
- every leaf rule, and that no `receipt_hash` appears in an earlier claim of that provider;
- the recomputed root, count and total;
- that the claim is funded on the chain: `deposited(p, network) >= cumulative_base_units`.

Within 24 hours after a claim is published, each committee monitor MUST decide and publish one of the two objects below. Signing and publishing are one act. A monitor MUST put a witness, refusal or hold on its page in the same step in which it signs it. It MUST NOT hand a witness to anyone before it is on its page.

- a `SettlementWitness` `{witness_id,claim_id,provider_id,network,sequence,period_end,total_base_units,cumulative_base_units,receipts_root,credit_base_units,witnessed_at,witness_signature}`. `witness_id` is the monitor's `did:key`. `credit_base_units` is `deposited(p, network)` minus `cumulative_base_units` at that time. It is signed under P("settlement-witness", the witness excluding `witness_signature`). `witnessed_at` MUST NOT be earlier than `period_end`;
- a `SettlementRefusal` `{witness_id,claim_id,provider_id,network,sequence,reason,refused_at,witness_signature}` signed under P("settlement-refusal", the refusal excluding `witness_signature`). `reason` is exactly one of `bad_signature`, `bad_chain`, `bad_period`, `bad_leaf`, `duplicate_receipt`, `bad_totals`, `unfunded` or `unknown_provider_key`.

A monitor MUST NOT refuse for any other reason, and in particular not because of a message's content or author. A witness is final; a refusal is not.

- A monitor audits a claim it refused as `unfunded` again every 24 hours for 7 days.
- A monitor MUST audit a refused claim again when it obtains public data it lacked (a schedule, declaration or succession it had not yet fetched).
- A later witness supersedes its refusal.
- For a real fault the provider publishes a corrected claim with the same `sequence`.
- A provider MUST NOT replace a claim whose only problem is funding or an object not yet published. It deposits enough or publishes the object instead.

A monitor serves what it signed at `GET /v1/witnesses?provider_id={did}&network={network}&after_sequence={n}`. The response is a `MonitorWitnessesPage` `{witnesses,refusals,holds,claims}`, where `claims` are the signed claim objects its witnesses and holds refer to. The monitor delivers each witness to the provider with `POST /v1/settlement-witnesses` (201 new, 200 already held, 404 `not_found` for an unknown claim, 422 `invalid_message`).

**Catching up.** A committee monitor that holds no witness at a sequence where a quorum of the committee has witnessed one claim adopts that claim. It verifies the claim's `claim_id`, provider signature, chain link and cumulative total, the other monitors' witnesses and the deposits on the chain. It then publishes its own witness for the claim, without applying the lateness and leaf rules. A monitor that witnessed a *different* claim at such a sequence keeps its witness and publishes the equivocation. From then on it treats the settled claim as the predecessor when it audits later sequences.

**A settled claim settles its ancestors.** Every monitor that witnesses a claim has checked its link to the claim before it. A quorum on a claim is therefore a quorum on the whole chain up to it, and a claim is settled when it, or any later claim that chains from it, has a quorum. A monitor that adopts or follows a settled claim treats all of that claim's ancestors as its predecessors in the same way, whatever it had witnessed at those sequences. Any hold it published at those sequences ends. Two different claims at one sequence still cannot both be settled. The honest witnesses of a claim all hold its ancestors, and too few honest monitors are left to give a quorum to anything that chains from a rival.

**One witness per sequence, and it is final.** A monitor witnesses at most one claim for a given provider, network and `sequence`. It never withdraws or replaces that witness. It audits a second, different claim at that sequence only if it refused the first. A monitor that witnessed the first refuses every other claim at that sequence with reason `bad_chain`.

Two different claims at one sequence of one provider chain are **equivocation**. A monitor that holds two such claims, each of which passes the audit and at least one of which a committee monitor has witnessed, publishes a proof at `GET /v1/equivocations?provider_id={did}`. The response is an `EquivocationsPage` `{proofs}`. Each proof is an `EquivocationProof` `{claims,predecessor,successions}`: the two signed claims, the signed claim at the previous sequence (null for sequence 1) and every `KeySuccession` the two claims name. Anyone can check a proof without trusting the monitor. It is valid when:

- both claims verify, and they have the same `network`, `sequence` and `previous_claim_id` and different `claim_id` values;
- for sequence 1, both have the same `provider_id`;
- otherwise `predecessor` verifies, and each claim follows it under the rules above for `sequence`, `previous_claim_id`, the period, `cumulative_base_units` and `succession_id`. In particular its provider key is the predecessor's key with a null `succession_id`, or follows from it by the succession the claim names.

A claim signed by an unrelated key that copies an honest claim's `previous_claim_id` is therefore not a proof. A provider that equivocates can leave a sequence with no quorum. That chain then cannot continue. The remedy is the provider's own: a new provider key and a new chain.

A claim is **settled** when a **quorum** of the committee has witnessed it or a later claim that chains from it. A quorum is more than two-thirds of the committee: 4 of 5, 5 of 7. Any two quorums share more than one-third of the committee. Two different claims at one sequence can therefore both be settled only if more than one-third of the monitors each signed both, against the rule above.

The trust assumption of settlement is therefore that **fewer than one-third of the committee monitors are faulty** (one of five, two of seven). It is stated here, and the release keys choose and can replace the committee. A committee of seven or more is RECOMMENDED. One silent monitor of five (two of seven) does not stop settlement. More silent monitors do, and the release keys then replace the committee as described in [distribution](#distribution). Until they have, new receipts cannot settle, and after 7 days they are no longer `pending_settlement`. This is the liveness limit of the design.

**Handover.** A committee change is bounded so that it cannot weaken settlement. Write n for the committee size, q for the quorum and f for the largest number of faulty monitors the assumption allows (the largest integer below n/3). A change does one of two things:

- it replaces monitors, keeping the size and replacing at most `q - f - 1` of them (two of five, two of seven); or
- it adds monitors, removing none and adding at most `q - f - 1`.

Changes are at least 30 days apart. Verifiers and monitors MUST reject a policy whose committee breaks these bounds against the policy it follows. From the new policy's `effective_at`, a monitor that is no longer on the committee MUST NOT sign witnesses.

A newly named monitor takes over the settled history instead of re-deciding it. It signs nothing before `effective_at`. Before it signs anything for a provider chain, it does two things at or after `effective_at`:

- it fetches the witness pages of every continuing monitor (their witnesses, refusals and holds);
- it collects the departed monitors' witnesses, and holds signed by departed members of the outgoing committee, from any source (their pages, the providers, the vault). A witness or hold authenticates itself.

Then, sequence by sequence:

- where a quorum of the outgoing committee witnessed one claim, it adopts that claim as in catching up, together with the key successions the adopted claims name;
- where it knows of committee witnesses but no quorum, it may witness a claim only if two conditions hold. The claim passes its audit (all the committee checks except the first-seen lateness rule), **and every other claim it knows of at that sequence is proven invalid by facts that cannot change**. Such facts are:
  - a bad signature or `claim_id`;
  - a broken link to the adopted predecessor;
  - a period longer than 24 hours or overlapping the predecessor's;
  - leaves that show a bad leaf under a release-approved schedule, bad totals or a duplicate receipt;
  - a `declaration_id` or `succession_id` that breaks its rule, shown by the claim, the adopted predecessor and the object the claim names.

  Each of these is fixed by the claim, the adopted predecessor and objects named by content ID or approved by the release keys. Nothing a provider signs later can create such a proof or remove it. A claim is not proven invalid when the newcomer cannot obtain its leaves or an object it names, or when it fails only for funding, for a period that has not ended, or for a key the monitor does not accept as the chain's successor. A newcomer **knows of** a claim only when it holds the provider-signed claim object itself and either a witness for it from a present or past committee member or a hold (below) from a member of the outgoing committee. A witness or hold for a claim whose signed object nobody produces is ignored, so a faulty monitor cannot block a chain with a claim that does not exist;
- when it therefore witnesses nothing at a sequence, it publishes a signed `SettlementHold` `{witness_id,provider_id,network,sequence,claim_ids,held_at,witness_signature}` under P("settlement-hold", the hold excluding `witness_signature`). The hold lists every claim it knows of there (at most 64). The monitor serves it together with those signed claim objects. A hold stands until all but one of its claims are proven invalid. Holds make a block durable: a monitor named later sees the holds and claim objects of the continuing monitors and is bound by the same rule. A claim therefore cannot be completed by waiting for a second committee change. An honest provider's correction of a claim with a provable fault is not blocked. A provider that published two claims that are not provably invalid leaves the sequence unsettled unless the outgoing committee completes a quorum;
- where no outgoing witness exists, it audits normally.

It adopts the history published before `effective_at` by that instant, since the policy is announced at least 14 days ahead. For any sequence at which it knows of a claim whose `period_end` is earlier than `effective_at`, it waits until 48 hours after `effective_at`. It then fetches the continuing monitors' pages again, and only then applies the rules above. This covers every witness an outgoing monitor signed before the change. Monitors publish as they sign, and at least one honest monitor that witnessed any outgoing-quorum claim stays on the committee and serves its page. A newcomer therefore always learns of that claim before it could witness a different one at its sequence. Handover trusts a quorum of the outgoing committee once more, for the history it hands over.

**What can still block a sequence.** Every fault that the claim, its predecessor and the objects it names can show is provable. A committee change therefore never blocks an honest provider's correction of such a fault, even when a faulty monitor witnessed the faulty claim. A sequence is left without a quorum across a handover only by the provider's own doing:

- it published two claims that both pass the audit (equivocation);
- it published a different claim at a sequence instead of funding the one it published;
- it withholds the leaves, or an object named by a claim, for a claim that a monitor witnessed;
- it published a claim that names a declaration or succession that does not exist. No proof of its absence can exist; or
- it named a succession onto a key that had already signed a settlement claim or is part of a succession from a different old key.

The remedy is then the provider's own, as for equivocation: a new provider key and a new chain. The handover is the newest part of this design and the part that most needs independent review before any deployment.

### Proofs and receipt states

`GET /v1/settlements/{receipt_id}` is a public route on every provider and on the vault. It returns 200 with a `SettlementProof` `{claim,leaf,leaf_index,audit_path,witnesses,chain?}` or 404 `not_found`. `chain`, when present, is the list of later claims that link `claim` to the claim the witnesses are for. It is in sequence order and at most 1,000 long. A provider that needs a longer link asks the monitors to witness an intermediate claim by catching up.

A verifier holding a receipt:

1. checks that `leaf.receipt_hash` is the hash of the receipt, that `schedule_id`, `amount_base_units` and `issued_at` equal the receipt's, and that the claim's `provider_id` and `network` match the receipt;
2. verifies the claim's `claim_id` and provider signature. When `chain` is present, it verifies each claim in it the same way, and checks that each one names the one before it as `previous_claim_id` and has:
   - the next `sequence`;
   - the same `network`;
   - a cumulative total increased by its own total;
   - the same `provider_id` and a null `succession_id`, or a `succession_id` naming a `KeySuccession` from the earlier claim's key to its own. The verifier fetches and verifies that succession, and requires its `effective_at` to be not earlier than the earlier claim's `period_end` and not later than this claim's `period_start`.

   It then takes the last claim of `chain` as the witnessed claim in step 4;
3. recomputes the root node from the leaf and `audit_path`, and requires its hash to equal `receipts_root` and its sum to equal `total_base_units`;
4. counts the valid `SettlementWitness` objects whose fields equal the claim's, from distinct monitors, **one committee at a time**. The claim is settled when the witnesses come from either:
   - a quorum (more than two-thirds) of the committee in force at the verifier's own clock; or
   - during the 30 days after a committee change, a quorum of the committee that was in force before it, counting only witnesses whose `witnessed_at` is earlier than the change's `effective_at`.

   Witnesses of the two committees are never added together.

The amount in a leaf is checked against the message by whoever holds the message: a reader recomputes the fee from the message bytes and rejects a receipt whose amount differs, as required in [clients](./07-clients.md).

| State | Condition | Treatment |
| --- | --- | --- |
| `settled` | Steps 1–4 succeed | The fee is proven paid. Eligible for admission trust |
| `pending_settlement` | Not settled; the verifier obtained the message from that provider's own public read routes; the receipt `issued_at` is not in the future and less than 7 days before the verifier's clock; the verifier trusts the provider locally; and the verifier has no delinquency record for that provider | Not proof of payment. A client MAY treat the record as admitted on its own trust in the provider, marked as pending |
| `unsettled` | Anything else | MUST NOT be classified as admitted |

A receipt is **delinquent** when the verifier obtained its message from that provider's own public read routes and the receipt is still not settled 7 days after its `issued_at`. A message obtained anywhere else with an unsettled receipt is `unsettled`, never pending and never delinquent. Nobody can therefore frame a provider with a receipt whose fee the provider restored, and a provider cannot avoid delinquency by serving its messages only through others.

A verifier that finds a delinquent receipt MUST keep a delinquency record `(provider, receipt_id)` until that receipt settles, also across a provider key succession. Discarding the message does not discard the record. While the verifier has such a record, none of that provider's receipts is `pending_settlement` for it. The honest path takes at most 48 hours (a 24-hour period and the 24-hour witness deadline after prompt publication). The 7 days leave room for a corrected claim and slow monitors.

A verifier also checks that a receipt's `issued_at` is within 300 seconds after and 60 seconds before the message `timestamp`.

`pending_settlement` is a statement about the verifier's trust in a provider, never evidence that a fee was paid. A provider that issues receipts and does not settle them is caught within 7 days by every verifier that fetched one of them from it. A provider nobody trusts gains nothing by issuing receipts. Only `settled` shows that money reached the Foundation. A verifier that later obtains a valid proof reclassifies the record as `settled`. It re-evaluates a settled record when the committee changes.

A settlement proof shows that a quorum of the committee audited the fee as paid to the Foundation's recipient on the chain. It does not prove the provider's solvency, the truth of the content or the receipt time. The Foundation cannot unsettle, block or forge it.

## Distribution

The Foundation returns part of each provider's settled fees to that provider every calendar quarter. The better its measured quality and the longer its proven retention record, the larger the part. The amount depends only on that provider's own figures, and it is always less than the provider settled, so admitting posts never pays for itself.

`DistributionPolicy` is `{policy_id,revision,vault_share_bp,monitor_share_bp,max_retention_years,min_reports,monitors,approved_at,effective_at,release_signatures}`. `policy_id` is `fydp2:` plus lowercase SHA256 hex of P("distribution-policy-id", the policy excluding `policy_id` and `release_signatures`).

- The policy is approved by the [release threshold](./06-governance.md#release-keys) under P("distribution-policy", the policy excluding `release_signatures`). It is not approved by the Foundation, because the Foundation keeps whatever is not distributed.
- A policy takes effect only at the start of a quarter (UTC), and `approved_at` is at least 60 days before `effective_at`.
- The one exception to the timing is a **committee replacement**. A policy that differs from the one in force only in `monitors` (and `revision`, dates and signatures) MAY take effect outside a quarter start with 14 days' notice, within the [handover](#the-settlement-committee) bounds and not less than 30 days after the previous committee change. This lets silent or faulty monitors be replaced quickly.
- Statement entries, `proven_quarters` and accrued amounts belong to a chain and are keyed by its first key.
- `monitor_share_bp` MUST be at most 1000 and at most `vault_share_bp`.
- `vault_share_bp` MUST be at least 2500.
- `monitors` MUST name at least five monitors, none controlled by the Foundation or by a provider they report on.
- `min_reports` MUST be at least 3.

Distribution policy 1:

| Parameter | Value |
| --- | --- |
| `vault_share_bp` | 5000 |
| `monitor_share_bp` | 500 |
| `max_retention_years` | 10 |
| `min_reports` | 3 |

For each provider p, network and quarter, with exact integers:

```text
settled_fees(p)  = sum of total_base_units of p's settled claims counted in the quarter
keep_bp          = 10000 - vault_share_bp
retention_bp(p)  = 5000 + 5000 * retention_years(p) // max_retention_years
amount(p)        = settled_fees(p) * keep_bp * quality_bp(p) * retention_bp(p) // 10000^3
```

Under policy 1 a provider with a perfect score keeps 27.5% of its fees in its first year and 50% once it has ten proven years. A provider with no usable quality score keeps nothing.

- A settled claim is counted in the quarter that contains its `period_end` when it was settled by that quarter's cut-off, 14 days after the quarter ended. Otherwise it is counted in the first later quarter whose cut-off finds it settled. "Settled" here is the committee-quorum rule of [settlement](#the-settlement-committee), which anyone can check.
- `retention_years(p)` is `min(max_retention_years, declared_years, 1 + proven_quarters // 4)`.
  - `declared_years` is the smallest `retention_seconds // 31536000` among the declarations named by p's claims counted in the quarter.
  - `proven_quarters` counts the quarters, up to and including this one, in which p had `settled_fees` of at least the minimum deposit (10,000,000 msat or 10^15 wei) and a `quality_bp` of at least 5000. It is carried in each statement and follows a verified provider key succession. When p has no entry in the previous statement, the count is carried from the most recent earlier statement that has an entry for p. An old key that did not serve therefore earns nothing for its age.
- A statement is computed under the policy in force at the end of its quarter. For quality, every monitor that was a committee member on any day of the quarter counts for the days of its membership.
- `quality_bp(p)` is computed from the QualityReports about p whose periods lie inside the quarter and whose `created_at` is not later than the cut-off. Each committee monitor publishes its own reports at `GET /v1/quality-reports?provider_id={did}&quarter_end={time}` (a `QualityReportsPage` `{reports}`). The Foundation therefore cannot lose or withhold them. The statement entry lists the `report_ids` it used, and anyone can fetch the monitors' reports and recompute. A committee monitor MUST report on every provider that had a settled claim in the quarter. Quarters are calendar quarters in UTC.
  - For each such monitor, its reports about p MUST NOT overlap in time.
  - The required coverage is at least 60 days of the quarter. When the provider's first settled claim or the monitor's committee membership began or ended inside the quarter, it is instead at least two-thirds of the days on which both the provider was active and the monitor was a committee member.
  - If the reports meet the required coverage, the monitor's score is the average of their known [reference scores](./09-quality.md#interpretation-and-optional-reference-score) weighted by the days each covers, rounded down. Otherwise the monitor has no score for p.
  - `quality_bp(p)` is the lower median of the monitors' scores, or 0 when fewer than `min_reports` monitors have one.
- The amount is paid to the payout recipient in the provider's declaration. An amount below 10,000 satoshis or 10^15 wei, or one with no payout recipient, is not paid but accrued. It is added to the provider's next statement entry as `accrued_base_units` and paid once the total reaches the minimum. Bitcoin payouts are whole satoshis; the msat remainder stays accrued.
- The committee is paid by rule, not by the Foundation's choice. `received × monitor_share_bp // 10000` is divided into equal seats, one per committee monitor, rounded down. `received` is the sum of `settled_fees` over all providers.
  - A seat is paid to its monitor only if, by the quarter's cut-off, that monitor has published a witness for at least 95% of the claims counted in the quarter whose `period_end` fell inside its committee membership. A witness published by catching up counts. Sequences with a published equivocation proof are left out.
  - A silent monitor and one that refuses what the committee settles therefore forfeit the seat. A monitor that witnesses an unfunded claim is exposed by its peers' refusals and by anyone's audit of the chain.
  - The test is computable from the monitors' public pages. An unpaid seat stays with the Foundation.
- Everything else stays with the Foundation for the Lifetime Vault and its operation.

Because `quality_bp` and `retention_bp` are at most 10000, `amount(p) <= settled_fees(p) × keep_bp / 10000`. Every admitted post therefore costs its provider at least the vault share of its fee, whoever the author is, and no arrangement of providers changes that, because no provider's amount depends on another's.

Within 30 days after each quarter the Foundation publishes one signed `DistributionStatement` per network: `{statement_id,foundation_id,network,period_start,period_end,policy_id,received_base_units,distributed_base_units,monitor_payments,entries,foundation_signature}`. `monitor_payments` lists `{monitor_id,amount_base_units,payout}` for each committee monitor, sorted by `monitor_id`. Each entry is `{provider_id,settled_fees_base_units,quality_bp,report_ids,retention_years,proven_quarters,amount_base_units,accrued_base_units,payout}`, sorted by `provider_id`. `accrued_base_units` is the balance still owed after this statement. `payout` is the on-chain transfer made for it (the same transfer object as a deposit transfer), or null when nothing was paid. `statement_id` is `fyds2:` plus lowercase SHA256 hex of P("distribution-statement-id", the statement excluding `statement_id` and `foundation_signature`). The signature covers P("distribution-statement", the statement excluding `foundation_signature`).

Anyone can recompute every entry from the providers' public claims and witnesses, their declarations, the monitors' published quality reports and the earlier statements. Anyone can also check each payout on the chain. A monitor that misses its duties is unpaid for the quarter and is replaced through a committee replacement.

A distribution payment is a Foundation payment to a provider. It is not a refund to authors and creates no author entitlement.

## Retention and the Lifetime Vault

### Provider retention

Each provider chooses how long it retains records and declares it.

`RetentionDeclaration` is `{declaration_id,provider_id,retention_seconds,payout_recipients,effective_at,provider_signature}`. `declaration_id` is `fyrd2:` plus lowercase SHA256 hex of P("retention-declaration-id", the declaration excluding `declaration_id` and `provider_signature`). The signature covers P("retention-declaration", the declaration excluding `provider_signature`). `payout_recipients` is an object with an optional recipient per supported network. `GET /v1/retention` returns a `RetentionDeclarationsPage` `{declarations}`, newest first.

- `retention_seconds` MUST be at least 31536000 (one year). There is no maximum.
- A record's governing declaration is the one named by the settlement claim that contains its receipt. Its `retain_until` is the receipt `issued_at` plus that declaration's `retention_seconds`. Until that claim exists, the provider keeps the record. A reader can rely on a retention period only once the claim that names the declaration exists. A provider SHOULD name its newest declaration that fits the claim; the one the claim names governs. A declaration cannot be backdated, for three reasons: a claim names it, monitors refuse a claim whose period has not ended, and a declaration cannot take effect inside a period already claimed.
- A new declaration applies to later claims only. A provider MAY keep any record longer than it declared. It MUST NOT drop a record before its `retain_until`.
- Until `retain_until`, the provider MUST keep one complete, independently verifiable copy and serve it on the public read routes, subject to provider-local legal restrictions.
- After `retain_until`, the provider MAY drop the record. A dropped record returns 410 `retention_expired` on direct retrieval and is omitted from listings.
- Before accepting and debiting a post, the provider MUST have the capacity to hold it for the declared period. A provider that cannot meet its declaration MUST stop new admissions and keep serving existing records.

Each version of a post is a separate record with its own `retain_until`.

### Lifetime Vault

The Lifetime Vault is an archive funded and owned by the Foundation.

- A provider MUST deliver every finalized public message to the vault with `PUT /v1/vault/messages/{message_id}` within 7 days after its receipt is settled. The request body is a `VaultDelivery` `{message,proof}`: the complete signed message and its `SettlementProof`.
- The request needs no authentication, because the message authenticates itself. A monitor, the author or anyone else MAY deliver a message the provider failed to deliver.
- Monitors named in the distribution policy MUST follow each provider's `GET /v1/changes` and deliver any settled message the vault lacks. A provider therefore cannot keep a public message out of the vault.
- The vault stores only paid messages. It verifies the ID and signatures, that the receipt's amount equals the fee for the message bytes under the receipt's schedule, and that the receipt is `settled` under the committee rule. The delivery carries the `SettlementProof`. After a committee change the vault refreshes the witnesses it holds from the new committee's monitors.
- The vault returns:
  - 201 for a new record and 200 for one already held, each with a signed `VaultReceipt` `{foundation_id,message_id,stored_at,foundation_signature}` under P("vault-receipt", the receipt excluding `foundation_signature`);
  - 409 `not_ready` when the receipt is not yet settled;
  - 422 `invalid_message` for a record that fails verification;
  - 403 with a restriction status when the Foundation is legally barred from holding it.
- `GET /v1/vault/receipts/{message_id}` returns the receipt publicly, so anyone can check delivery.
- The vault MUST NOT refuse a valid message for any reason other than a legal restriction that binds the Foundation.
- The vault retains every delivered message with no scheduled expiry and serves the same public read routes as a provider, under the same free-read rules. Its `provider_id` in listings and sync pages is the `foundation_id` of the certificate valid at the time of the response.
- The vault can fail, be restricted or lose data like any operator. It is an obligation of the Foundation, not a guarantee of perpetual availability.
- Each quarter the Foundation publishes a signed `VaultStatus` `{foundation_id,period_start,period_end,record_count,stored_bytes,funding,foundation_signature}` under P("vault-status", the status excluding `foundation_signature`). `funding` lists, per network, `{network,received_base_units,spent_base_units}`: the base units the Foundation kept from fees and spent in the quarter.

There is no author-delete message. Downloaded copies can persist anywhere.

### Foundation publications

The Foundation serves these public routes on the vault origin. None needs an account. Each response is a closed object of the operations schema.

| Route | Response |
| --- | --- |
| `GET /v1/foundation/genesis` | The `GenesisManifest` |
| `GET /v1/foundation/certificates` | `FoundationCertificatesPage` `{certificates,closures,key_set_updates}` |
| `GET /v1/foundation/fee-schedules` | `FeeSchedulesPage` `{schedules:[{schedule,approval}]}`, every revision |
| `GET /v1/foundation/distribution` | `DistributionPage` `{policies,statements}`, at least the last 8 quarters |
| `GET /v1/foundation/vault-status` | `VaultStatusPage` `{statuses}`, at least the last 8 quarters |
| `GET /v1/foundation/log/objects/{object_hash}` | The logged object itself, as the JSON that hashes to `object_hash`, or 404 `not_found`. Every logged object is public |
| `GET /v1/foundation/log?after={index}` | `FoundationLogPage` `{entries,head}` with the entries whose `index` is greater than `after` (omit `after` to start at index 0), at most 1,000 entries, and the latest signed head |
| `GET /v1/foundation/log/heads?after_size={n}` | `FoundationLogHeadsPage` `{heads}`, every signed head with a greater `size`, at most 1,000 |
| `GET /v1/foundation/log/proof/{object_hash}?size={n}` | `FoundationLogProof` `{index,size,audit_path}` against the log's first n entries, or 404 `not_found` |
| `GET /v1/foundation/quality-reports?provider_id={did}&quarter_end={time}` | `QualityReportsPage` `{reports}`; the reports the Foundation used for the quarter ending at that canonical UTC time, copied from the monitors |

### Reads and availability

Readers do not pay, and a popular post never causes an extra author debit. There are no per-message read budgets. The minimum anonymous read and listing rates, caching rules and overload behavior are in [portability](./05-portability.md#read-capacity-and-caching). Providers fund their own storage, egress and repair from distribution payments and from their own services.

Operators SHOULD disclose shared ownership, hosting and other correlated failure domains instead of describing two endpoints as independent because their URLs differ.
