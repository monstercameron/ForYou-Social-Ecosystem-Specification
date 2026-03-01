# Vision and Product Model

## Objective

Define what ForYou is trying to achieve and what user experience the protocol enables.

## Scope

This document covers:

- user-facing purpose
- product principles
- high-level system behavior
- intended value proposition

This document does not define protocol message formats, node APIs, or implementation details.

## Product Statement

ForYou is intended to be a paid publishing network with user-controlled reading.

In the baseline model:

- users publish content into a shared network
- publishing happens through any compatible client
- network operations are funded by usage-based payments
- users normally fund a provider plan once and then consume posting allowance over time
- the chosen plan covers publication, propagation, indexing, storage, and any retention commitment advertised by the chosen provider
- publish revenue should fund both the chosen provider and shared network service work over time
- readers control discovery through their own clients, filters, and ranking systems

## User Promise

From the user's perspective:

- fund a wallet with BTC or ETH
- fund a posting plan with a chosen provider
- choose a compatible client
- publish many posts to the network without making a fresh chain payment every time
- let each reader decide locally how to view it

The network handles publication. Readers decide visibility.

## Why Crypto

ForYou uses BTC and ETH to support:

- censorship resistance
- payment independence
- reduced intermediary control
- resistance to platform or state pressure through centralized services

## Foundational Principle

ForYou separates publishing from ranking:

- the network distributes authentic content and metadata
- the user owns the algorithm that decides what deserves their attention
- local ranking is the default model
- third-party ranking services are optional, not mandatory

## Core Goals

- Open publishing:
  users should be able to publish without relying on a single platform operator
- Simple publishing:
  the act of publishing should feel straightforward even if the underlying protocol is sophisticated
- Personalized discovery:
  users should be able to receive relevant content without a centrally controlled feed
- Attention ownership:
  users should control the ranking logic, models, and preference inputs that shape their feed
- Durable content access:
  the system should support retained access to content and metadata over time
- Transparent operations:
  network rules, fees, and governance should be visible and inspectable
- Sustainable infrastructure:
  the system should fund storage, indexing, and relay functions through explicit economics

## Product Principles

- Protocol first:
  core behavior should be defined at the protocol layer where possible
- Client choice:
  different clients should be able to compete on ranking, presentation, and user experience
- Model choice:
  users should be able to swap local models or use third-party ranking services when they choose
- Verifiable data:
  content references, payments, and signatures should be independently verifiable
- Minimal centralization:
  no single operator should be required for normal network use
- Local-first intelligence:
  ranking should happen on-device by default, with remote AI used only when the user opts in or device limits require it
- Simple outside, flexible inside:
  the user-facing model should stay simple while fees, ranking systems, and clients can evolve over time
- Payment independence:
  publishing should not depend on centralized payment processors that can be pressured to deny service

## Baseline User Flow

1. get BTC or ETH
2. fund a provider plan
3. open any compatible client
4. write a post
5. approve the publish action
6. publish to the network
7. let readers discover the post through their own clients

## Separation of Responsibilities

- Network:
  accepts and distributes valid posts
- Client:
  publishes, displays, and manages user settings
- Ranking layer:
  orders content for a reader
- User:
  controls preferences, filters, and attention

## User Experience Themes

- public posting
- signed social interactions
- AI-assisted relevance
- user-owned attention algorithm
- portable identity and content references
- multi-client access across web, mobile, and desktop
- reader-side filtering instead of global content gating

## Social Interaction Model

ForYou should not model only publishing and reading.

It should model:

- content
- signed public interaction events
- encrypted private portable state
- device-local transient preference state

Shared social context should come from signed interaction events.

Derived counts, summaries, and rankings may be computed by clients or providers, but they should not replace the underlying signed interaction history as the primary source of truth.

Private curation should not be forced into a false choice between fully public protocol state and lost-on-this-device local state.

User-owned ranking only works long term if private curation can survive device loss and sync across a user's own clients without becoming public network metadata.

## Interaction Categories

- Content lifecycle:
  `post`, `withdraw`
- Response:
  `reply`, `quote`, `counterpoint`
- Amplification:
  `recommend`
- Public relationship:
  `follow_source`, `follow_topic`, `subscribe_thread`
- Private curation:
  `mute`, `hide`, `block`, `bookmark`, `trust_source`, `boost`, `downrank`, `private_tag`, `private_note`
- Extension curation:
  `add_to_list`, `add_to_collection`, `pin_to_profile`, `add_to_reading_queue`
- Extension action:
  `tip`, `bounty`

Launch note:

- There is intentionally no `like` action in the launch baseline.
  `like` is ambiguous (bookmark vs public boost vs private ranking signal).
  For launch, those intents are separated into:
  `recommend` (public amplification), `bookmark` (private portable save), and private ranking controls such as `boost`, `downrank`, and `trust_source`.

`follow_source` and `trust_source` are intentionally different.

- `follow_source` is public portable social context.
- `trust_source` is private curation state used by the reader's own ranking logic.

## Interaction State Classes

For launch, ForYou should separate visibility and portability from submission cost.

The baseline state classes are:

- Public portable state:
  shared, signed protocol events that contribute to public social context
- Private portable state:
  encrypted user-owned state that syncs across the user's own clients or chosen sync services
- Device-local transient state:
  unsynced local cache, temporary UI state, and other non-portable behavior

This keeps the network socially expressive without pretending that public visibility and syncability are the same thing.

Public portable state includes:

- post
- withdraw
- reply
- quote
- counterpoint
- recommend
- follow_source
- follow_topic
- subscribe_thread

Private portable state includes:

- mute
- hide
- block
- bookmark
- trust_source
- boost
- downrank
- private_tag
- private_note

Device-local transient state includes:

- draft ranking features
- temporary cache decisions
- unsynced reading position or session data

## Submission Cost Classes

Within public portable state, launch should still distinguish between:

- Tier 1:
  paid public content writes such as post, reply, quote, and counterpoint
- Tier 2:
  lightweight public interactions such as `recommend`, `follow_source`, `follow_topic`, and `subscribe_thread`

Tier 1 actions create public content and should remain fee-bearing.

Tier 2 actions create shared social context, but they should be cheap, weak by default, and protected by funded allowance debits, batching, quotas, rate limits, or trust weighting.

Private portable state should not become public ranking truth and should not need to masquerade as public interaction traffic just to survive across devices.

## Interaction Taxonomy Mapping

The interaction categories above are intent-based UX grouping.

The protocol also has visibility and cost classes (`public portable`, `private portable`, `Tier 1`, `Tier 2`).
These axes are orthogonal, so launch docs should keep both visible.

Launch baseline mapping:

```text
ACTION             INTENT           VISIBILITY/PORTABILITY         COST CLASS
---------------------------------------------------------------------------
post               lifecycle        public portable                Tier 1
withdraw            lifecycle        public portable                Tier 1
reply              response         public portable                Tier 1
quote              response         public portable                Tier 1
counterpoint        response         public portable                Tier 1

recommend           amplification    public portable                Tier 2
follow_source       relationship     public portable                Tier 2
follow_topic        relationship     public portable                Tier 2
subscribe_thread    relationship     public portable                Tier 2

mute               private curation  private portable (encrypted)   none
hide               private curation  private portable (encrypted)   none
block              private curation  private portable (encrypted)   none
bookmark            private curation  private portable (encrypted)   none
trust_source        private curation  private portable (encrypted)   none
boost              private curation  private portable (encrypted)   none
downrank            private curation  private portable (encrypted)   none
private_tag         private curation  private portable (encrypted)   none
private_note        private curation  private portable (encrypted)   none
```

Extension note:

- Extension actions such as `tip`, `bounty`, `add_to_list`, `add_to_collection`, `pin_to_profile`, and `add_to_reading_queue`
  are not standardized as interoperable protocol messages at launch.
  Clients may still implement them privately (for example in encrypted private portable state), but they should not assume cross-client interoperability until the protocol defines them.

## Launch Interaction Direction

At launch, the protocol should prioritize portable public interaction events that improve shared social context:

- post
- withdraw
- reply
- quote
- counterpoint
- recommend
- follow_source
- follow_topic
- subscribe_thread

At launch, private curation interactions should use encrypted portable state where supported and remain private by default:

- mute
- hide
- block
- bookmark
- trust_source
- boost
- downrank
- private_tag
- private_note

Tip, bounty, list, collection, reading queue, and profile pinning are strong extension candidates, but they do not need to block the baseline launch interaction model.

Launch ranking and discovery should not treat raw Tier 2 interaction volume as a high-trust global signal. Those interactions are useful as weak context, trust-weighted input, and reader-local evidence rather than as universal popularity truth.

Launch clients should also support export, import, or encrypted sync of private curation state so the user's attention model is not destroyed by device loss.

## Open Decisions

- What user guarantees are mandatory at launch beyond valid publication and reader-controlled visibility?
