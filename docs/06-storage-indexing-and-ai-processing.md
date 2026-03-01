# Storage, Indexing, and AI Processing

## Objective

Define how full content, metadata, retention, and AI-driven discovery work together.

## Scope

This document covers:

- content storage
- metadata indexing
- propagation and retrieval
- retention behavior
- AI consumption of metadata and content

## Data Layers

- Full content layer:
  stores complete message payloads or referenced content objects
- Metadata layer:
  stores searchable fields needed for lookup and discovery
- Local client layer:
  stores user-relevant subsets of the index and cached content

## Responsibilities

- Storage systems:
  provide content addressing, content retrieval, and retention
- Index systems:
  provide searchable metadata and update propagation
- AI systems:
  analyze permitted metadata and optionally retrieve full content for ranking or filtering

## Distribution Model

Baseline distribution model:

- metadata spreads broadly across compliant participating hosts
- full content is fetched lazily by content address
- hosts cache or retain full content according to demand, policy, and locality

This supports broad discovery without requiring every host to mirror every full content object.

This document focuses on network data behavior. Client sequencing and user-facing feed behavior are defined in the reference client flow document.

## Launch Content-Address Scheme

For launch interoperability, `content_address` `MUST` use IPFS CIDv1 addressing:

```text
ipfs://<cidv1>
```

Retention-capable participants must treat "retention" as "pinning or equivalent durable storage." If content is not pinned, garbage collection or eviction will produce broken retrieval even if metadata remains.

Extension note:

- future revisions may standardize additional content-address schemes
- launch interoperability requires IPFS CIDv1 so clients can verify content consistently across hosts

## Metadata Propagation Protocol Class

The spec must not rely on the phrase "metadata spreads broadly" without describing how.

For launch, the intended protocol class is:

- epidemic gossip for recent metadata:
  new accepted metadata is pushed to a bounded fanout of peers
- periodic anti-entropy:
  peers exchange inventories and request missing ranges or chunks to repair gaps
- deduplication by `message_id`:
  replayed or already-seen items are dropped

This is not a single fixed wire protocol yet, but implementations should converge on:

- bounded fanout rather than global flood
- time-bucketed or cursor-based inventories rather than per-item polling
- recovery by inventory reconciliation rather than assuming perfect delivery

## Scaling Model

ForYou should scale by separating lightweight discovery from heavier content retrieval.

The intended scaling pattern is:

- metadata spreads broadly
- full content is loaded on demand
- hot content is cached widely
- cold content is retained more selectively

This is closer to a signed social graph over a swarm of retrievable objects than to a single website serving all content directly.

## Availability Graph

Discovery should follow a refreshable availability graph rather than depend on a single host.

The availability graph combines:

- peer references between hosts
- content availability hints for specific content addresses
- freshness information such as `last_seen`

Simple model:

```text
message_id
  ->
metadata lookup
  ->
content_address
  ->
availability graph
  ->
candidate hosts
  ->
fetch first success
  ->
verify
```

The network should improve availability by:

- learning alternate host paths
- caching successful retrievals
- re-serving useful objects from additional hosts
- keeping metadata much more replicated than full content

## Locality Model

- metadata may be widely indexed even when full content is not widely hosted
- a host may keep metadata while refusing full-content storage or local serving
- clients may fetch full content from alternate hosts where available
- content-addressed verification allows clients to trust the object they fetched without trusting every specific host

## Locality Diagram

```text
valid post
  |
  +--> host A: metadata + full content available
  |
  +--> host B: metadata only
  |
  +--> host C: unavailable locally
  |
  +--> client: fetch from alternate host and verify by content address
```

## Availability-Hint Behavior

- A host may know that content exists without storing it locally.
- A host should be able to return likely alternate hosts for a content address when it has such information.
- Clients should treat availability hints as advisory and try multiple sources when needed.
- Successful retrieval should reinforce local caches and local map knowledge.
- Clients should treat hints older than the launch freshness window as stale unless refreshed.

For launch, the freshness window should default to 7 days. Implementations may use shorter local expiry windows, but should avoid treating very old hints as strong evidence.

This document defines the network behavior of hints and recovery. The exact request and response surfaces for hints and content retrieval are defined in the API document.

## Swarm-Compatible Direction

The long-term retrieval model should become increasingly swarm-compatible:

- one content object may be retrievable from many hosts
- clients may fetch from any reachable host advertising or serving the object
- successful retrieval should increase the number of useful caches over time

The launch network does not need full BitTorrent-style chunk exchange. It should preserve the object model needed for future evolution while relying on canonical host and provider retrieval endpoints today.

## Launch Retention Commitments

For launch, retention should be expressed as provider commitments rather than as magical network guarantees.

Two provider capability levels should be recognized:

- baseline provider:
  participates in publication, propagation, and active retrieval without making a long-retention promise
- retained provider:
  publicly commits to a stated retention floor for accepted metadata and full content

The default retained-provider floor is:

- accepted metadata remains discoverable through that provider for at least 365 days
- accepted full content remains retrievable through that provider for at least 180 days unless local law, valid takedown obligations, or explicit policy prevents continued serving

These are provider-level commitments, not a requirement that every host store every object for the full period.

Hosts may retain content longer, and well-provisioned operators should be encouraged to do so.

## Durability Direction

If a provider markets a publish plan as durable rather than best-effort, it should also publish a replication target.

The recommended durable baseline is:

- metadata replicated to at least 3 independent discovery or index paths
- full content replicated to at least 2 retained-provider paths

These are service commitments made by the provider offering the plan, not universal guarantees made by the entire network.

## Content Temperature Model

The network should expect different storage behavior for different demand levels:

- hot content:
  recently active or frequently retrieved objects that should be cached broadly
- warm content:
  less active objects that remain available from several host paths
- cold content:
  older retained objects that may be slower to recover but should still remain discoverable according to provider retention commitments

## Old-Content Recovery Example

```text
client has old message_id
  ->
query index provider A and provider B
  ->
receive metadata record with content_address
  ->
receive host hints:
- host C
- host F
- host H
  ->
try host C: miss
  ->
try host F: offline
  ->
try host H: hit
  ->
fetch content
  ->
verify by content address
  ->
cache locally and refresh local host map
```

This example describes recovery behavior, not a mandatory transport sequence. Concrete endpoint usage is defined in the API document.

## Ranking Model

- Ranking behavior consumes the metadata and retrieval model defined in this document.
- Local-first ranking, remote ranking fallback, and private preference handling are specified in the attention and client-flow documents.

## Interface Questions

- What exact metadata is globally visible?
- How are index chunks produced, addressed, and verified?
- What retention guarantees exist for content versus metadata?
- What happens when a content address resolves to missing or illegal content?

## Privacy and Policy Questions

- Remote AI services are allowed, but local processing is the default model.
- What metadata is available to third-party crawlers?
- What user controls exist over ranking and filtering inputs?
- What content access patterns leak user interests?

## Open Decisions

- Whether the metadata index is purely operational or has any stronger interoperability role
- Whether retained-provider commitments should be standardized further into multiple retention classes after launch

## Related Documents

- `11-attention-and-ranking-model.md`
- `12-ranking-profile-and-model-interface.md`
- `14-protocol-metadata-requirements.md`
- `15-reference-client-feed-flow.md`
- `17-index-provider-and-candidate-chunk-api.md`
