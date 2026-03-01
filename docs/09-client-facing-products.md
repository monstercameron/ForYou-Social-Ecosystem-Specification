# Client-Facing Products

## Objective

Define the user-facing applications and experiences built on top of the protocol.

## Scope

This document covers:

- client product surfaces
- end-user capabilities
- experience-level requirements
- UX implications of protocol choices

## Named Product Surfaces

- ForYou Page:
  personalized timeline and conversation experience
- ForYou Pulse:
  real-time or trending activity experience
- ForYou App:
  unified cross-platform client

## ForYou Pulse Baseline

ForYou Pulse is the explicit discovery surface intended to solve:

- cold start for new users
- "what is happening now" browsing
- exploration outside the user's follow graph

Launch baseline expectations:

- Pulse `SHOULD` be clearly labeled as a discovery surface, not as the user's private ranking profile.
- Pulse `SHOULD` be built from broad candidate modes (recent and/or random sample) across multiple providers when available.
- Pulse `MUST` respect the reader's local filters (mute, block, hide, sensitivity settings), even when the candidate source is remote.
- Pulse `SHOULD` display the provider sources used to generate the candidate set so users can reason about possible bias or gaps.
- Pulse `MUST NOT` require a single mandatory provider or a single mandatory ranking service.

## Client Responsibilities

- compose and submit messages
- display ranked or filtered feeds
- present identity and profile data
- manage payment flows
- retrieve content when requested
- expose public interaction actions where supported
- apply user-level filtering and preferences
- support user control over ranking model selection and ranking-service delegation

## UX Baseline

Clients should make the protocol feel simple even when the network is not.

The baseline user mental model is:

- fund once
- choose or renew a plan occasionally
- choose a client
- write and publish
- readers decide what they see

Normal use should not expose node roles, index providers, or transport details.

## Publisher Journey

For launch, the clean publishing journey is:

1. fund a wallet with BTC or ETH
2. fund or renew a provider plan
3. open any compatible client
4. write a post
5. see allowance or cost impact before submission
6. approve the publish action
7. let the client handle signing and receipt attachment
8. submit to the network
9. receive clear status: `pending` or `published`

## Reader Journey

For launch, the clean reading journey is:

1. choose a client
2. use local ranking by default or opt into remote ranking
3. set personal filters and preferences
4. browse a feed ranked for that user
5. use public actions such as reply, quote, counterpoint, recommend, follow sources, follow topics, or subscribe to threads where desired
6. use private curation such as hide, mute, bookmark, trust sources, boost, or downrank to tune local ranking
7. let those choices shape future ranking without changing the network itself

## Social Interaction UX

Clients should distinguish clearly between:

- public interactions:
  actions that create portable signed social context
- private portable interactions:
  encrypted user-owned state that should sync across the user's own devices without becoming public metadata
- device-local interactions:
  actions that affect only the current device or session

Launch public interaction surfaces should prioritize:

- post
- withdraw
- reply
- quote
- counterpoint
- recommend
- follow source
- follow topic
- subscribe to thread

Launch private portable interaction surfaces should prioritize:

- mute
- hide
- block
- bookmark
- trust source
- boost
- downrank
- private tag
- private note

Clients should present these interaction classes differently:

- Tier 1 paid public writes:
  create visible public content and require fee-bearing submission
- Tier 2 lightweight public interactions:
  create portable public context but should feel immediate and lightweight to the user
- private portable interactions:
  affect the user's own feed, trust, curation, and sync state without becoming public discovery metadata
- device-local interactions:
  affect only the current device or session

## UX Upgrade Direction

The launch UX should:

- present posting as a simple paid action, not as blockchain plumbing
- make plan funding occasional and publication frequent
- treat client choice as normal and expected
- show fee status clearly before publishing
- let lightweight public interactions feel immediate even when provider reconciliation happens later
- preserve private curation across devices through export, import, or encrypted sync
- separate publication success from reader visibility
- explain that visibility depends on each reader's own filters and ranking
- avoid implying global moderation or a single platform feed

## Separation of Responsibilities

Clients should make this model obvious:

- the network publishes
- the client presents
- the ranking system orders
- the user decides

## Ranking UX Requirements

- Local-first ranking:
  clients should default to local ranking when the device can support it
- Model portability:
  clients should let users swap ranking models without losing their preference intent
- Service delegation:
  clients may allow users to route ranking through a third-party service
- Resource-aware fallbacks:
  clients on low-power devices should support smaller local models or user-approved hosted ranking
- Private preference handling:
  clients may use private local metadata, history, and explicit preferences to improve relevance
- Private curation portability:
  clients should preserve private curation through encrypted sync or export rather than trapping it on one device

## Publishing UX Requirements

- Clients `SHOULD` show the estimated posting cost before submission.
- Clients `SHOULD` show remaining allowance or unit impact when a plan-backed publish is the normal path.
- Clients `SHOULD` make plan-funded publication feel like one publish action from the user's perspective.
- Clients `MUST` distinguish between `pending` and `published`.
- Clients `SHOULD` explain that network publication does not guarantee distribution into every reader's feed.
- Clients `MUST NOT` imply that the client operator centrally controls what the entire network can publish.
- Clients `SHOULD` make room for later fee changes, richer content types, and additional publishing options without changing the basic publish flow.
- Clients `SHOULD` support optimistic UI for lightweight public interactions and reconcile them in the background.
- Clients `MUST NOT` route a single lightweight interaction into an immediate L1 payment prompt in the normal UX path.
- Clients `MUST` distinguish between a lightweight interaction that is `local only`, `queued`, or `portable confirmed`.
- Clients `SHOULD` explain reconciliation failures explicitly rather than silently dropping an optimistic interaction.

## Minimum Launch Client Capabilities

A conforming launch client should be able to:

- compose and submit a standard post
- compose and submit a reply
- render and submit supported public interaction types
- quote the current publish plan and allowance impact before submission
- sign the message and attach the applicable submission receipt or submission token
- display `pending` and `published`
- fetch candidate metadata from at least one provider path
- rank locally when feasible or fall back gracefully when local ranking is unavailable
- retrieve full content by `content_address`
- let the user use public follow actions separately from private trust-source preferences
- preserve or sync private curation state across the user's own devices through export, import, encrypted sync, or equivalent portable state handling
- display user identities using human-friendly handles when available, while always retaining the canonical `author_id`
- display a short fingerprint of `author_id` alongside aliases to reduce impersonation risk
- avoid presenting raw recommendation or follow volume as authoritative popularity truth
- render target-unavailable or target-withdrawn states explicitly for quotes, counterpoints, replies, and recommendations

These requirements define compatibility more clearly than product branding or visual style.

## Canonical Publish Example

Example user-facing flow:

- button:
  `Publish`
- pre-submit copy:
  `This will publish your post using your current provider plan. What readers see depends on their own client, filters, and ranking settings.`
- status sequence:
  `Pending`
  `Published`
- failure copy:
  `Publish failed. Check plan status or allowance and try again.`

## Launch Questions

- How should initial plan funding failures and delayed confirmations be surfaced?
- How should lightweight-interaction quotas or credits be surfaced to users when a provider enforces them?

## Open Decisions

- Whether there is an official reference client at launch
