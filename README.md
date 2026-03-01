# ForYou Social Ecosystem Specification

**Domain:** [foryousocial.network](https://foryousocial.network)

## Purpose

This repository contains the working specification for the ForYou social ecosystem. The original monolithic README has been split into focused documents so each major area can be clarified and evolved independently.

The current material describes a paid publishing network with user-controlled reading.

At a high level:

- anyone can publish through any compatible client
- publishing requires funded access through a provider plan
- providers issue admission evidence for each portable public message:
  submission receipts for Tier 1 writes and submission tokens for Tier 2 lightweight interactions
- the network accepts valid posts
- each reader decides what they see through their own client, filters, and ranking

## Why BTC and ETH

ForYou uses BTC and ETH to support censorship resistance, payment independence, reduced intermediary control, and resistance to platform or state pressure through centralized services.

## User Promise

Fund a wallet, fund a provider plan, choose a client, publish posts, and let readers decide locally how to view them.

## Baseline User Flow

1. Get BTC or ETH.
2. Fund a provider plan.
3. Open any compatible client.
4. Write a post.
5. Approve the publish action.
6. Publish to the network.
7. Readers may discover it through their own clients.

## Status

This specification is still a draft. The core model is in place, and some documents now define provisional launch baselines, but unresolved areas remain and should not yet be treated as permanently frozen requirements.

## Document Map

The active specification lives under [`docs/`](./docs/README.md).

Suggested reading order:

- product and user model:
  [Vision and Product Model](./docs/01-vision-and-product-model.md),
  [Client-Facing Products](./docs/09-client-facing-products.md),
  [Reference Client Feed Flow](./docs/15-reference-client-feed-flow.md),
  [Poster Experience](./docs/18-poster-experience.md),
  [Reader Experience](./docs/19-reader-experience.md),
  [Third-Party Reader Experience](./docs/20-third-party-reader-experience.md),
  [Host Operator Experience](./docs/21-host-operator-experience.md)
- protocol and transport:
  [Core Protocol Architecture](./docs/02-core-protocol-architecture.md),
  [Data and Message Formats](./docs/04-data-and-message-formats.md),
  [Index Provider and Candidate Chunk API](./docs/17-index-provider-and-candidate-chunk-api.md)
- payments and identity:
  [Payments and Economic Model](./docs/05-payments-and-economic-model.md),
  [Identity and Source References](./docs/16-identity-and-source-references.md)
- ranking and discovery:
  [Storage, Indexing, and AI Processing](./docs/06-storage-indexing-and-ai-processing.md),
  [Attention and Ranking Model](./docs/11-attention-and-ranking-model.md),
  [Ranking Profile and Model Interface](./docs/12-ranking-profile-and-model-interface.md),
  [Protocol Metadata Requirements](./docs/14-protocol-metadata-requirements.md)
- governance, compliance, and operations:
  [Security, Moderation, and Compliance](./docs/07-security-moderation-and-compliance.md),
  [Governance and Dispute Resolution](./docs/08-governance-and-dispute-resolution.md),
  [Operations and Roadmap](./docs/10-operations-and-roadmap.md)
- supporting reference:
  [Network ASCII Architecture](./docs/13-network-ascii-architecture.md)

## Working Approach

- Use the root `README.md` as the repository entry point.
- Use each document in `docs/` to define one major component of the system.
- Keep unresolved design questions in the relevant component document.
- Prefer making protocol requirements explicit instead of relying on concept language.
- Keep the public-facing story simple even when the protocol underneath it is more complex.

## Immediate Priorities

The most important unresolved areas are:

- keeping the paid publish flow simple while staying honest about BTC/ETH settlement costs and latency
- locking the canonical retrieval and discovery surfaces for interoperable clients and hosts
- keeping the boundary clear between network publication and reader-side visibility
- defining how reader-side filtering interacts with operator compliance obligations
- limiting launch governance to protocol coordination instead of central control
- defining the interface between local ranking models and third-party ranking services

## Next Editing Pass

The next useful step is to turn the remaining draft sections into explicit launch requirements, interfaces, state transitions, and validation rules.
