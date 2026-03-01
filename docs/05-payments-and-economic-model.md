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
- direct per-message BTC or ETH settlement remains an allowed fallback, not the preferred user path

Launch should not require:

- Lightning-specific payment logic
- rollup-specific payment logic
- custodial balances as protocol payment truth
- staking as a prerequisite for basic posting

Providers may offer convenience flows around that baseline, but publish-plan funding only reaches final settlement when it is backed by a canonical BTC or ETH payment reference that satisfies the provider's published plan rule.

Secondary settlement paths may be standardized later, but they should be treated as extensions rather than launch-critical assumptions.

## Payment Rationale

The network uses BTC and ETH to support:

- censorship resistance
- payment independence
- reduced intermediary control
- resistance to platform or state pressure through centralized services

## Baseline Verification Model

Baseline payment flow:

1. a user funds a provider plan using BTC or ETH
2. a bridge node parses the funding transaction reference for the declared chain
3. the bridge node verifies transaction existence, amount, recipient, and acceptable confirmation state
4. the provider credits the user's plan or allowance after verification
5. each accepted public network write debits units from that funded plan and returns a provider-signed submission receipt
6. flow and indexing participants use that receipt during message acceptance

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
- transaction identifier
- observed amount
- intended plan or funding class
- intended recipient reference

This proof may begin as a client-supplied funding object and be normalized by bridge verification afterward.

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

## Bridge Verification Output

A bridge verification result `SHOULD` include:

- `chain`
- `transaction_id`
- `verification_status`
- `observed_amount`
- `observed_at`
- `confirmation_state`
- `bridge_id`

Optional fields:

- `block_reference`
- `recipient_reference`
- `payment_class`
- `reason_code`

Example:

```json
{
  "chain": "bitcoin",
  "transaction_id": "tx-123",
  "verification_status": "verified",
  "observed_amount": "0.0001",
  "observed_at": "2026-03-01T15:00:00Z",
  "confirmation_state": "provisional",
  "bridge_id": "bridge-us-east-1",
  "payment_class": "standard_post"
}
```

## Acceptance States

- `verified`
  funding or direct payment meets baseline requirements for message acceptance
- `provisional`
  funding or direct payment is observed but not yet fully confirmed according to local node policy
- `rejected`
  funding, direct payment, or submission receipt is invalid, insufficient, malformed, or otherwise unacceptable

Nodes `SHOULD` make their provisional-versus-final acceptance policy explicit.

## Recipient Verification Rule

For launch, bridge verification should confirm not only that a funding payment exists, but that it pays an acceptable recipient for the declared plan or payment class.

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
- Clients `SHOULD` surface whether a newly funded plan or a direct-payment fallback is still provisional.
- Once a plan is fully funded and credited, normal message submission should not require users to wait for fresh chain confirmation on every post.

## Receipt and Funding Reuse Policy

- A funded plan may cover many submissions within its published allowance and duration.
- A provider-signed submission receipt `MUST NOT` be reused across multiple distinct message submissions.
- A direct one-time payment fallback `MUST NOT` be reused across multiple distinct message submissions.
- If receipt reuse or invalid allowance reuse is detected, nodes `SHOULD` reject the later submission.

## Launch Baseline

Launch fee model:

- one or more provider-published plan classes for recurring usage
- a clear unit schedule for Tier 1 and Tier 2 actions
- no individual base-layer fee per normal public interaction at launch
- no direct L1 fallback requirement for individual Tier 2 interactions in the normal UX path
- no mandatory staking dependency for basic posting
- BTC and ETH plan funding as the normal launch path
- direct per-message BTC and ETH settlement only as a fallback path for Tier 1 or other heavier writes
- no advertisement fee class in the minimum launch interoperability baseline
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

- run the bridge, relay, index, and storage functions directly
- subcontract those functions operationally
- share revenue with other operators outside the protocol

Launch should not require trustless multi-party fee splitting in order to publish successfully.

## Launch Failure and Retry Baseline

For launch:

- a client may retry submission of the same `message_id` using the same submission receipt or direct-payment fallback reference when the earlier attempt did not result in acceptance
- a one-time receipt or one-time payment fallback must not be reused for a different `message_id`
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
