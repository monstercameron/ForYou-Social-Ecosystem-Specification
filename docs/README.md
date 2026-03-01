# Documentation Map

## Purpose

This repository is being reorganized from a single concept document into a set of focused specification documents. The goal is to make each major area easier to reason about, discuss, and revise independently.

## How to Use This Folder

- Start with the root repository `README.md` for project context.
- Use the documents in this folder as the working specification set.
- Treat each document as the source of truth for one major area.
- Record unresolved decisions directly in the relevant document instead of burying them in a general summary.

## Document Index

- [01-vision-and-product-model.md](./01-vision-and-product-model.md)
- [02-core-protocol-architecture.md](./02-core-protocol-architecture.md)
- [03-network-roles-and-infrastructure.md](./03-network-roles-and-infrastructure.md)
- [04-data-and-message-formats.md](./04-data-and-message-formats.md)
- [05-payments-and-economic-model.md](./05-payments-and-economic-model.md)
- [06-storage-indexing-and-ai-processing.md](./06-storage-indexing-and-ai-processing.md)
- [07-security-moderation-and-compliance.md](./07-security-moderation-and-compliance.md)
- [08-governance-and-dispute-resolution.md](./08-governance-and-dispute-resolution.md)
- [09-client-facing-products.md](./09-client-facing-products.md)
- [10-operations-and-roadmap.md](./10-operations-and-roadmap.md)
- [11-attention-and-ranking-model.md](./11-attention-and-ranking-model.md)
- [12-ranking-profile-and-model-interface.md](./12-ranking-profile-and-model-interface.md)
- [13-network-ascii-architecture.md](./13-network-ascii-architecture.md)
- [14-protocol-metadata-requirements.md](./14-protocol-metadata-requirements.md)
- [15-reference-client-feed-flow.md](./15-reference-client-feed-flow.md)
- [16-identity-and-source-references.md](./16-identity-and-source-references.md)
- [17-index-provider-and-candidate-chunk-api.md](./17-index-provider-and-candidate-chunk-api.md)
- [18-poster-experience.md](./18-poster-experience.md)
- [19-reader-experience.md](./19-reader-experience.md)
- [20-third-party-reader-experience.md](./20-third-party-reader-experience.md)
- [21-host-operator-experience.md](./21-host-operator-experience.md)

## Recommended Editing Flow

1. Clarify the product and protocol goals in `01`.
2. Define the core protocol and node responsibilities in `02` and `03`.
3. Lock down message formats and payment rules in `04` and `05`.
4. Resolve storage, indexing, and AI boundaries in `06`.
5. Define the enforcement and policy model in `07` and `08`.
6. Translate protocol behavior into user-facing requirements in `09`.
7. Define attention ownership and ranking interfaces in `11`.
8. Define portable ranking profiles and model interfaces in `12`.
9. Define the minimum metadata needed for strong local ranking in `14`.
10. Use `13` for plain-text architecture communication and reviews.
11. Use `15` as the reference client behavior document.
12. Define canonical source identity and trust references in `16`.
13. Define candidate-chunk retrieval APIs in `17`.
14. Define the poster, reader, third-party reader, and host experiences in `18` through `21`.
15. Capture launch requirements and future work in `10`.

## Current Status

The repository is still in draft form. Several documents now define provisional launch baselines, but the spec set is not yet fully frozen. The document split is intended to make remaining gaps visible and easier to resolve.
