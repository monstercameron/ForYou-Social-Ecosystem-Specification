# Payments and Economic Model

## Objective

Define how the network charges for actions, verifies payments, and funds operators.

## Scope

This document covers:

- supported payment systems
- feeable actions
- fee calculation
- reward distribution
- launch payment constraints and future extensions

## Economic Actions

- Message submission
- Lightweight public interaction submission controls
- Possible future extension actions outside the launch baseline, including advertisement submission

## Payment Model

The network uses BTC- and ETH-based settlement to fund provider-issued network service plans.

Launch should stay simple and avoid introducing additional payment assets or staking requirements for basic posting.

For launch, paid publishing should not require a direct L1 payment per message in the normal case. Instead, users should fund a provider plan in BTC or ETH and consume metered allowance units from that plan when they publish or create portable public interactions.

## Launch Settlement Baseline

For launch, the minimum interoperable settlement baseline is:

- BTC or ETH funds a provider-issued publish plan or allowance balance
- portable public writes consume allowance units against that funded plan
- providers and clients may use cheaper BTC/ETH rails for plan funding, but the settlement asset remains BTC or ETH

Launch should not require:

- custodial balances as protocol payment truth
- staking as a prerequisite for basic posting

Providers may offer convenience flows around that baseline, but publish-plan funding only reaches final settlement when it is backed by a canonical BTC or ETH payment reference that satisfies the provider's published plan rule.

Secondary settlement paths may be standardized later, but they should be treated as extensions rather than launch-critical assumptions.

## Funding Rails

ForYou is BTC/ETH-settled. That does not mean every user action must be funded by an L1 BTC/ETH transaction.

Launch should allow multiple funding rails for plan funding, while keeping the settlement asset limited to BTC or ETH.

Baseline rail definitions:

- BTC L1:
  a standard Bitcoin on-chain transaction reference
- BTC Lightning:
  a Lightning invoice or payment reference accepted by the provider
- ETH L1:
  a standard Ethereum on-chain transaction reference
- ETH L2:
  a rollup or L2 payment reference accepted by the provider

Launch interoperability `MUST` support BTC L1 and ETH L1 funding proofs for plan funding.

Providers `SHOULD` support at least one lower-fee rail (Lightning or a major ETH L2) if they advertise low annual-plan pricing such as the reference $10/year plan.

If a provider only supports L1 funding, it should publish a minimum funding amount that covers expected L1 fee volatility so users are not surprised by a funding transaction that costs more than the plan.

## Payment Rationale

The network uses BTC and ETH to support:

- censorship resistance
- payment independence
- reduced intermediary control
- resistance to platform or state pressure through centralized services

## Custody Models

Plan funding and plan usage can be implemented in different custody models. The spec should make these explicit because they change the censorship-resistance properties.

Baseline custody categories:

- Self-custody funding:
  the user funds a plan directly from a wallet they control, and the provider never holds a long-lived custodial balance on behalf of the user
- Custodial balance funding:
  the user deposits funds into a provider-controlled account and the provider debits an internal ledger
- Assisted self-custody:
  the user controls keys, but the client or provider offers guided flows for buying, swapping, or routing payments

Launch expectations:

- Providers `MUST` disclose whether a plan is funded by self-custody payments or by custodial balances.
- Clients `SHOULD` surface that disclosure during plan funding.
- Censorship-resistance claims are strongest under self-custody funding, and weakest under custodial balances.

## Baseline Verification Model

Baseline payment flow:

1. a user funds a provider plan using BTC or ETH
2. a verification path parses the funding reference for the declared chain and rail
3. the verification path verifies existence, amount, recipient, and acceptable confirmation state
4. the provider credits the user's plan or allowance after verification
5. each accepted public network write debits units from that funded plan and returns a provider-signed submission receipt
6. flow and indexing participants use that receipt during message acceptance

Launch note:

- funding may be performed over different rails, but verification must produce a normalized proof shape
- once a provider has credited a plan and is issuing receipts or tokens, normal publishing should be low-latency

## Required Definitions

- Chargeable event:
  define what action causes a fee to be owed
- Payment proof:
  define what evidence must accompany a message
- Confirmation rule:
  define when a referenced payment is considered valid enough for acceptance
- Pricing rule:
  define how fees are calculated and updated
- Distribution rule:
  define how collected value is routed to operators or treasury functions

## Launch Fee Publication Rule

At launch, an accepting provider should publish a clear service schedule for each supported plan and fee class.

That schedule should include at least:

- plan identifier
- duration or renewal model
- included allowance units or allowance rate
- unit cost by action tier
- supported chain
- minimum funding amount
- recipient reference
- schedule version or effective time
- custody model disclosure:
  self-custody, custodial, or assisted self-custody
- revenue split disclosure:
  provider share, network service share, and any reserve share
- auditability disclosure:
  where the provider publishes transparency and accounting artifacts for receipts and tokens

Clients should quote this schedule before the user approves funding or publication.

## Reference Heavy Plan

The spec should define a reference heavy-user plan so the product model is concrete.

Reference target:

- annual plan
- target user profile:
  up to 25 Tier 1 public content writes per day for 365 days
- target consumer benchmark:
  approximately USD 10 per year, quoted in BTC or ETH equivalent by the provider at purchase time

This benchmark is a product target, not immutable protocol truth. Providers may charge different amounts, durations, or allowance mixes, but the launch UX should be designed around funding a plan once and posting many times.

## Launch Funding Proof

For launch, a funded plan should carry enough payment information for the receiving path to verify:

- declared chain
- funding reference
- observed amount
- intended plan or funding class
- intended recipient reference

This proof may begin as a client-supplied funding object and be normalized by verification afterward.

## Submission Receipt Model

For launch, portable public writes should normally carry a provider-signed submission receipt rather than their own direct L1 payment reference.

A submission receipt should minimally bind:

- provider identity
- plan or allowance identifier
- receipt identifier
- units consumed
- covered message identifier
- provider signature

This lets the user fund in BTC or ETH once while still making each public write auditable and meterable.

## Submission Token Model

For launch, lightweight public interactions should also support a reusable provider-signed submission token.

A submission token should grant bounded, time-limited admission for Tier 2 interactions so the user does not need a fresh provider signature on every tap.

A submission token should minimally bind:

- provider identity
- plan or allowance identifier
- token identifier
- actor identity
- permitted interaction scope
- bounded unit budget
- validity window
- provider signature

Submission tokens should be actor-scoped and tier-scoped rather than target-scoped. A provider should not need to pre-approve each individual follow target, topic, or recommended post in order for the user to spend a valid Tier 2 capability.

This allows providers to keep abuse controls while removing the synchronous provider bottleneck from every recommend, follow, or subscribe action.

## Receipt and Token Auditability

Provider signatures alone do not prove that a provider is solvent, honest, or correctly metering allowance units.

For launch, the spec should distinguish between:

- local correctness:
  a message carries a valid provider signature, so the receiving path can verify admission
- economic auditability:
  independent parties can verify the provider is not issuing unlimited receipts or tokens beyond funded capacity

Launch should support auditability through:

- published provider plan schedules and recipient references
- published funding references for each plan class
- a provider transparency log for issued receipts and tokens

Baseline auditability direction:

- a provider `SHOULD` publish a signed periodic accounting report for each plan class:
  funded amount, units issued, and remaining budget
- a provider `SHOULD` publish a signed append-only log root (Merkle or similar) that can prove inclusion of a given receipt or token identifier
- hosts and clients `MAY` apply stricter trust policies to providers that do not publish auditable accounting artifacts

Launch does not require a full on-chain slashing system, but it should make dishonest providers visible and avoid treating unauditable providers as universally equivalent to auditable ones.

Launch audit artifact example (non-normative):

```json
{
  "provider_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
  "plan_id": "annual-heavy-2026",
  "window": "2026-03-01",
  "funding_total": "0.0001",
  "units_issued": 9000,
  "units_remaining": 123,
  "audit_log_root": "b64url-log-root",
  "audit_log_size": 104857,
  "signature": "base64-provider-signature"
}
```

Receipts and tokens may carry `audit_log_root` and `audit_proof_ref` pointers so independent parties can verify inclusion of a specific `receipt_id` or `token_id` in the provider's published transparency artifacts.

## Interaction Cost Model

For launch, ForYou should distinguish between:

- Tier 1 paid public writes:
  post, reply, quote, and counterpoint
- Tier 2 lightweight public interactions:
  recommend, follow_source, follow_topic, and subscribe_thread
- Private portable state:
  encrypted curation and preference sync that is not public ranking truth
- Device-local transient state:
  client-local preference behavior outside canonical protocol payment rules
- Extension actions:
  advertisement and other future fee-bearing extension types

Tier 1 actions are fee-bearing protocol actions.

Tier 2 actions are public and portable, but they should consume fewer allowance units than Tier 1 actions and should not require a separate base-layer BTC or ETH payment reference per interaction at launch.

Private portable state should normally be bundled into a client, provider, or user-chosen sync offering rather than charged as a public interaction event.

Private portable state should not consume Tier 1 or Tier 2 public-interaction allowance by default.

If a provider offers hosted encrypted private-state sync, that service may have its own storage limits or subscription terms, but users should not have to spend public social-interaction budget to mute, block, bookmark, or preserve notes across their own devices.

Device-local transient state is not a protocol payment event.

## Launch Lightweight-Interaction Baseline

At launch, lightweight public interactions should use funded allowance consumption and admission controls rather than individual base-layer settlement.

They should also support asynchronous UX.

Providers accepting Tier 2 interactions `MUST` apply one or more of:

- funded allowance-unit debits
- bounded interaction quotas
- identity-level rate limits
- equivalent admission controls that impose real cost, friction, or throughput limits

The protocol should require signed interaction messages and a valid submission receipt for portable public interactions, while allowing provider diversity in plan shapes and local throughput controls.
The protocol should allow Tier 2 interactions to use a valid submission token in place of a fresh per-message provider signature.

For launch:

- clients `SHOULD` allow a lightweight interaction tap to succeed locally before provider reconciliation completes
- providers `SHOULD` allow short-window batching or deferred reconciliation for Tier 2 interactions when doing so does not break abuse controls
- clients `MUST` surface whether a lightweight interaction is only local, queued for reconciliation, or confirmed portable
- providers `SHOULD` expose explicit reconciliation failure reasons such as exhausted allowance, expired token, or policy rejection
- providers `SHOULD` issue target-agnostic Tier 2 submission tokens rather than requiring per-target approval
- exhausted Tier 2 allowance `SHOULD` result in queuing, temporary provider-local treatment, or a prompt to refresh the plan
- exhausted Tier 2 allowance `MUST NOT` force a direct L1 payment flow for a single lightweight interaction in the normal UX path

Portable public interaction streams that are not backed by funded allowance debits should be treated as provider-local behavior, not as high-trust network-wide social evidence.

## Ranking-Signal Rule

Raw Tier 2 interaction volume `MUST NOT` be treated as a high-trust universal ranking signal.

Clients and providers `SHOULD` prefer:

- receipts backed by funded plans over unaudited free interaction streams
- trust-weighted interpretation
- graph-quality weighting
- age and history weighting
- reader-local relevance

This keeps public lightweight interactions useful without making bot volume equivalent to earned trust.

## Verification Output

A verification result `SHOULD` include:

- `chain`
- `funding_reference`
- `observed_amount`
- `observed_at`
- `acceptance_state`
- `verifier_id`

Optional fields:

- `block_reference`
- `recipient_reference`
- `payment_class`
- `reason_code`

Example:

```json
{
  "chain": "bitcoin",
  "funding_reference": "tx-123",
  "observed_amount": "0.0001",
  "observed_at": "2026-03-01T15:00:00Z",
  "acceptance_state": "provisional",
  "verifier_id": "verifier-us-east-1",
  "payment_class": "standard_post"
}
```

## Acceptance States

- `provisional`
  funding or direct payment is observed but not yet fully confirmed according to local node policy
- `verified`
  funding or direct payment meets baseline requirements for message acceptance
- `rejected`
  funding, direct payment, or submission receipt is invalid, insufficient, malformed, or otherwise unacceptable

Nodes `SHOULD` make their provisional-versus-final acceptance policy explicit.

## Recipient Verification Rule

For launch, verification should confirm not only that a funding payment exists, but that it pays an acceptable recipient for the declared plan or payment class.

A funded plan should not be treated as valid merely because value moved somewhere on-chain. It must match the provider's published recipient reference and minimum amount for that plan or action.

## Launch Confirmation Policy

For launch, the baseline confirmation policy is:

- Bitcoin:
  `provisional` at 1 block confirmation
- Bitcoin:
  `verified` at 3 block confirmations
- Ethereum:
  `provisional` after inclusion in a canonical block with successful execution
- Ethereum:
  `verified` at 12 block confirmations

Additional launch rules:

- Nodes `MAY` require stricter thresholds for higher-value actions.
- Nodes `MUST` reject transactions that are missing, reverted, malformed, or insufficient in amount.
- Clients `SHOULD` surface whether a newly funded plan is still provisional.
- Once a plan is fully funded and credited, normal message submission should not require users to wait for fresh chain confirmation on every post.

## Verification Resilience

ForYou should not depend on one mandatory payment-verification chokepoint.

Launch resilience rules:

- there is no single global bridge
- verification is a role:
  an accepting provider may verify BTC/ETH funding using its own infrastructure, or may consume verification artifacts from multiple verifiers
- if one verifier is down, providers `SHOULD` be able to fail over to another verifier or to local verification
- if a provider cannot verify new plan funding, it `MUST` not issue new allowance credits or receipts for that unfunded plan
- existing already-credited plans should continue working even if verification is temporarily unavailable
- clients `SHOULD` treat "plan funding pending verification" as a recoverable state:
  queue the funding, show clear status, or choose a different provider rather than treating the network as down

## Receipt and Funding Reuse Policy

- A funded plan may cover many submissions within its published allowance and duration.
- A provider-signed submission receipt `MUST NOT` be reused across multiple distinct message submissions.
- If receipt reuse or invalid allowance reuse is detected, nodes `SHOULD` reject the later submission.

## Launch Baseline

Launch fee model:

- one or more provider-published plan classes for recurring usage
- a clear unit schedule for Tier 1 and Tier 2 actions
- no individual base-layer fee per normal public interaction at launch
- no direct L1 fallback requirement for individual Tier 2 interactions in the normal UX path
- no mandatory staking dependency for basic posting
- BTC and ETH plan funding as the normal launch path
- no requirement for per-message direct BTC/ETH settlement in the interoperable launch baseline
- no advertisement fee class in the minimum launch interoperability baseline
- direct per-message BTC/ETH settlement, if supported at all, should be treated as an optional extension rather than as a user-facing fallback path
- no default public-interaction quota charge for encrypted private-state sync

The publish fee covers the baseline network function:

- payment verification
- propagation
- indexing
- storage
- no separate retention or archive fee at launch
- and, when offered, any provider-published retention commitment bundled into the chosen plan

These are fee classes, not permanent fiat promises. Clients `MAY` show estimated fiat equivalents, but the protocol treats fees as network payment requirements.

If an accepting provider advertises retained-provider behavior, that retention commitment is part of the provider's published service offer rather than a second user-facing launch fee.

## Read-Path Economic Model

The protocol should not assume that unlimited anonymous reading is free to operate.

At launch, read and discovery costs may be funded by any combination of:

- the user's chosen publish plan
- a bundled client or provider subscription
- operator-to-operator contracts
- reader-specific service plans
- limited public access tiers subsidized by the operator

The protocol should make room for independent read providers to publish their own service terms instead of forcing every serious read path to be subsidized indefinitely by accepting providers.

## Hybrid Revenue Model

Posts should fund the network through a hybrid revenue model rather than a single-ingress winner-take-all model.

For launch, provider plan revenue should be split conceptually into:

- direct provider share:
  retained by the provider chosen by the user
- network service share:
  contributed to shared service buckets
- optional reserve share:
  retained for refunds, fraud losses, smoothing, or future governance-defined needs

The exact percentages do not need to be frozen in this document yet, but the architecture should assume that publish revenue funds both direct customer-facing service and shared network infrastructure.

Launch disclosure rule:

- if a provider claims participation in shared service buckets, it `MUST` disclose its network service share for the plan class
- if a provider advertises "network-funded discovery/retrieval" behavior, it `SHOULD` publish settlement reports that show actual payouts or contracts

## Service Buckets

The network service share should be accounted for by service class rather than by one undifferentiated pool.

Launch service buckets should include:

- ingress bucket:
  accepts paid submissions, validates messages, and issues submission receipts
- discovery bucket:
  serves candidate metadata and discovery responses
- retrieval bucket:
  serves full content and useful cache responses
- retention bucket:
  honors retained-provider commitments
- verification bucket:
  verifies BTC or ETH funding and supports receipt issuance

This modular structure allows future service classes to be added without redesigning the whole funding model.

## Accounting Windows

For launch, shared service accounting should happen in fixed windows rather than continuously.

Recommended launch baseline:

- one daily or weekly accounting window
- work is measured per service bucket
- bucket rewards are distributed after the window closes

This keeps accounting understandable and leaves room for later refinement.

## Distribution Baseline

Launch does not require a single global treasury or a single mandatory payout coordinator.

However, if the spec claims that publish revenue funds read, discovery, verification, and retention work beyond the accepting provider, then it must define how distribution is computed and audited.

Baseline distribution direction:

- each accounting window produces per-bucket work claims
- work claims are signed by the claiming operator
- independent auditors or operators may recompute totals from sampled evidence
- bucket rewards are distributed proportionally to accepted work within the window
- payout execution may be performed by one or more distributors, but the accounting artifacts should be verifiable independently

Launch requirement target:

- a shared-bucket participant `SHOULD` publish a signed per-window report that includes:
  window identifier, bucket identifier, operator identifier, work total, and evidence pointers
- a provider contributing network service share `SHOULD` publish which distributor(s) it uses and how it verifies their reports

This keeps the launch system workable without pretending the full accounting and payout mechanism is already fully decentralized.

## Work-Unit Baseline

For launch, each bucket should use simple work units that can be measured and audited.

Recommended unit direction:

- ingress bucket:
  count of accepted Tier 1 messages (optionally weighted by size class)
- discovery bucket:
  count of candidate items served (optionally weighted by bytes served)
- retrieval bucket:
  bytes of verified full-content served
- retention bucket:
  retained bytes-days (bytes retained multiplied by days during the window)
- verification bucket:
  count of successful plan-funding verifications that resulted in credited plan allowance

These units are not perfect, but they are more auditable than subjective metrics such as popularity or AI quality.

## Work-Claim Report Example

Launch work-claim reports should be signed and should include evidence pointers.

Example (non-normative):

```json
{
  "window": "2026-03-01",
  "bucket_id": "retrieval",
  "operator_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
  "work_units": 987654321,
  "unit_kind": "bytes_served",
  "evidence": {
    "log_root": "b64url-log-root",
    "log_ref": "ipfs://bafyexample"
  },
  "signature": "base64-operator-signature"
}
```

## Payout Settlement Report Example

If a provider or distributor claims that publish revenue funded shared service work, it should publish a signed settlement report that points to concrete payouts.

Example (non-normative):

```json
{
  "window": "2026-03-01",
  "payer_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
  "chain": "bitcoin",
  "payout_reference": "tx-456",
  "total_paid": "0.0025",
  "payouts": [
    {
      "bucket_id": "discovery",
      "operator_id": "did:key:z6Mk...discovery",
      "amount": "0.0007"
    },
    {
      "bucket_id": "retrieval",
      "operator_id": "did:key:z6Mk...retrieval",
      "amount": "0.0018"
    }
  ],
  "signature": "base64-payer-signature"
}
```

## Rewardable Work Rule

The network should reward only work that is:

- externally useful
- measurable
- auditable
- difficult to fake cheaply

Launch reward measurements should prefer:

- accepted paid submissions
- valid candidate responses served
- successful full-content retrievals served
- retained-provider commitments honored during the accounting window
- valid funding verification and receipt issuance

The network should not reward vague categories such as generic popularity, AI quality, or raw unaudited request volume.

## Anti-Gaming Baseline

Shared-bucket rewards should be hardened against easy farming.

For launch:

- self-generated demand `SHOULD` be discounted or excluded where detectable
- duplicate or replayed submission receipts `MUST` not earn repeated rewards
- suspicious outlier traffic `MAY` be capped, sampled, or discounted
- retention claims should be auditable during the relevant window
- provider-local unfunded interaction streams `MUST NOT` earn high-trust shared-network rewards

This keeps the network share focused on useful service rather than fake load.

## Launch Distribution Baseline

For launch, the accepting provider is the baseline fee recipient.

That provider may:

- run the verification, relay, index, and storage functions directly
- subcontract those functions operationally
- share revenue with other operators outside the protocol

Launch should not require trustless multi-party fee splitting in order to publish successfully.

## Launch Failure and Retry Baseline

For launch:

- a client may retry submission of the same `message_id` using the same submission receipt when the earlier attempt did not result in acceptance
- a one-time receipt must not be reused for a different `message_id`
- failed or abandoned submissions do not imply an automatic on-chain refund
- providers may define customer-service refund policies, but those policies are outside the protocol unless later standardized

## Economic Tensions To Resolve

- BTC and ETH still fund the system, but provider plans are needed to make that usable as social software.
- BTC and ETH have different confirmation and data models.
- Read infrastructure needs explicit funding rather than being treated as a free side effect.
- Dynamic pricing requires trusted inputs or explicit network rules.

The launch design accepts this by making chain settlement periodic and deliberate while making normal public posting low-latency after funding.

## Open Decisions

- How a future secondary settlement path should be standardized without breaking BTC/ETH launch compatibility
- Who is allowed to modify published pricing parameters after launch governance is formalized
- Whether any refund behavior should ever become protocol-standard rather than provider-specific
