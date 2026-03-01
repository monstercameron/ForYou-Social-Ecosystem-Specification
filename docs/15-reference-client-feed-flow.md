# Reference Client Feed Flow

## Objective

Describe a reference client flow for fetching content, ranking it, and rendering a personalized feed.

## Status

This document is a draft behavioral reference for client implementers.

## User-Facing Summary

From the user's perspective:

- a publisher funds a plan and posts to the network
- a reader decides locally what to read

The client should preserve that simplicity even though the underlying system includes signing, payment verification, indexing, storage retrieval, and local ranking.

## Publishing Overview

A reference client should support a clean publishing flow:

1. write the post
2. show the required allowance impact for the action
3. approve one publish action
4. submit to the network
5. show `pending` or `published`

Readers do not need to share the publisher's client, preferences, or ranking model to discover the post.

## Overview

A reference client separates feed generation into five stages:

1. fetch candidate metadata
2. enrich with local context
3. rank candidates
4. retrieve full content selectively
5. render and iterate

## Publishing Flow

### Stage P1: Compose

The client:

- lets the user draft the content
- validates required fields before submission
- prepares the canonical message envelope and payload

### Stage P2: Quote Fee and Sign

The client:

- shows the plan impact and remaining allowance required for the action
- asks the user to approve a single publish action
- handles signing and receipt attachment as part of that publish action

### Stage P3: Submit and Track

The client:

- submits the signed message and the applicable submission receipt or submission token
- tracks acceptance state from `pending` to `published`
- explains failures in user language rather than protocol jargon

### Publishing Reference Sequence

```text
1. user -> client: write post
2. client -> user: show fee and publish action
3. user -> client: approve publish action
4. client -> network path: submit signed message + submission receipt
5. provider/flow path -> client: pending or published status
6. network path -> client: published status
```

## Canonical Publish-State Example

Example state progression:

```text
Draft -> Pending -> Published
```

Example user copy:

```text
Pending: Your publish request was sent.
Published: Your post is fully accepted.
```

## Stage 1: Fetch Candidate Metadata

The client:

- connects to one or more index providers or full nodes
- requests candidate chunks relevant to the user's scopes of interest
- validates message integrity and basic metadata shape
- discards invalid or unsupported items

The client should not assume it can or should download the full global network state. Candidate retrieval is supposed to narrow the ranking problem to a practical working set.

The client should rely on the provider and discovery surfaces defined by the index-provider API document rather than inventing a private retrieval flow.

## Stage 2: Enrich With Local Context

The client:

- attaches private local preference signals
- loads any synced encrypted private curation state available to the user's device set
- computes or loads local trust, mute, and history features
- prepares a normalized candidate set for ranking
- keeps this enrichment local unless the user has opted into remote ranking

## Stage 3: Rank Candidates

Default path:

- the client invokes a local ranking engine
- the engine scores and orders the candidate set
- the client records ranking provenance as local

Fallback path:

- if the device cannot support useful local ranking, the client may use a smaller local model
- if that is still insufficient and the user opts in, the client may call a remote ranking service
- the client records ranking provenance as remote or hybrid

At launch, local ranking should usually act as reranking over provider-fetched candidate sets rather than as full-network inference on-device.

## Stage 4: Retrieve Full Content Selectively

The client:

- selects the highest-value candidates based on ranking score and UI needs
- resolves content addresses through the canonical retrieval path
- verifies content integrity
- loads additional content lazily as the user scrolls or expands threads

If a host path fails, the client should fall back through alternate providers or host hints as defined by the storage and discovery documents.

For launch, the interoperable retrieval baseline is the provider or host content endpoint defined by `GET /v1/content/{content_address}`.

## Stage 5: Render and Iterate

The client:

- renders the personalized feed
- surfaces ranking provenance to the user
- accepts public actions such as `reply`, `quote`, `counterpoint`, `recommend`, `follow_source`, `follow_topic`, and `subscribe_thread`
- accepts private curation actions such as `mute`, `hide`, `trust_source`, `boost`, `downrank`, `bookmark`, and `private_note`
- feeds those actions back into local preference state for future ranking

Public interaction actions should generate portable signed events when the client supports them.

Tier 2 public lightweight interactions should be treated as weak social context by default. A conforming client should not let raw recommendation or follow totals dominate ranking without additional local trust, graph, or history weighting.

Tier 2 public lightweight interactions should support optimistic local UI with background reconciliation where possible.

If a Tier 2 interaction is still awaiting reconciliation, the client should show that it is queued or still local to this client rather than pretending it is already durable public state.

If reconciliation fails, the client should retain accurate local state while making clear that the interaction was not promoted to portable public state.

Private curation actions should be stored in encrypted portable state when the client supports cross-device sync.

Only transient unsynced actions should remain device-local by default.

## Reference Sequence

```text
1. client -> index provider: fetch candidate metadata
2. index provider -> client: candidate batch
3. client -> local state: attach preferences and history
4. client -> ranking engine: score candidates
5. ranking engine -> client: ranked results
6. client -> storage layer: fetch top content objects
7. storage layer -> client: full content
8. client -> user: render personal feed
```

## Normative Guidance

- A conforming client `SHOULD` fetch metadata before full content whenever feasible.
- A conforming client `MUST` preserve user preference state locally by default.
- A conforming client `SHOULD` preserve portable private curation state across the user's own devices when the user enables sync.
- A conforming client `MUST` disclose when remote ranking is used.
- A conforming client `SHOULD` support graceful degradation to smaller local models on constrained devices.
- A conforming client `MUST NOT` require a remote ranking provider in order to read protocol content.

## Failure Handling

- If ranking fails:
  render unranked or lightly sorted content
- If storage retrieval fails:
  retain candidate shells, retry lazily, and consult alternate provider or host paths when available
- If remote ranking fails:
  fall back to local ranking or non-ranked display
- If index providers disagree:
  prefer valid, verifiable metadata and log the conflict
- If Tier 2 reconciliation fails:
  keep the local UI honest by marking the interaction as still local to this client, queued, or failed rather than silently fabricating portable state
- If a target message is withdrawn or unavailable:
  render a tombstone or unavailable target state instead of leaving a broken empty reference

## Related Documents

- `09-client-facing-products.md`
- `11-attention-and-ranking-model.md`
- `12-ranking-profile-and-model-interface.md`
- `13-network-ascii-architecture.md`
- `14-protocol-metadata-requirements.md`
- `17-index-provider-and-candidate-chunk-api.md`
