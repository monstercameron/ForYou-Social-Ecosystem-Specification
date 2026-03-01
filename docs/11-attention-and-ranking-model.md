# Attention and Ranking Model

## Objective

Define who controls feed ranking, how ranking is performed, and how local and third-party AI systems interact with the protocol.

## Status

This document defines normative requirements for attention ownership and ranking behavior.

The keywords `MUST`, `SHOULD`, and `MAY` are to be interpreted as normative requirements.

## Core Principle

The user owns the algorithm for their attention.

ForYou separates publishing from ranking:

- the protocol distributes posts and metadata
- the protocol does not impose a mandatory global feed algorithm
- ranking is local by default
- users may choose local or third-party ranking systems

Local-first does not mean "every phone runs a multi-gigabyte model over the global firehose."

For launch, local-first primarily means:

- the user's preference state, filters, trust lists, and objectives are controlled by the user
- the user can swap clients and models without losing their attention policy
- ranking execution may be local, remote, or hybrid depending on device constraints, but must remain user-controlled and replaceable

## Scope

This document covers:

- attention ownership
- ranking defaults
- local model usage
- third-party ranking services
- portability of models and preferences
- low-power device fallbacks

## Normative Requirements

### Ranking Ownership

- A conforming client `MUST NOT` require a single network-wide ranking algorithm in order to read protocol content.
- A conforming client `MUST` allow users to consume unranked or minimally processed protocol content if ranking is unavailable.
- The protocol `MUST NOT` treat a ranking service as a source of truth for message validity.

### Default Ranking Behavior

- Clients `MUST` treat local ranking as the default mode when the device can support it.
- Clients `SHOULD` perform ranking on-device when local compute, memory, bandwidth, and power constraints allow it.
- Clients `MAY` disable local ranking when the user explicitly opts out.

Local ranking does not require every client to ingest a full global firehose or run a heavyweight model over the entire network state.

At launch, local ranking should usually mean:

- fetch candidate sets from one or more providers
- combine those sets with local preferences and history
- run local reranking or local filtering on that candidate pool

This keeps attention ownership local without assuming unrealistic mobile compute or bandwidth budgets.

### User-Controlled Preferences

- Clients `MUST` allow user-controlled ranking preferences to influence feed generation.
- Clients `MUST` keep private ranking context local unless the user explicitly chooses to share it with an external service.
- Clients `SHOULD` expose clear controls for ranking objectives, filters, and weighting behavior.
- Clients `SHOULD` preserve private ranking context across the user's own devices through export, import, or encrypted portable state.

### Third-Party Ranking

- Clients `MAY` integrate third-party ranking services.
- Third-party ranking `MUST` be opt-in.
- Clients `MUST` make it clear when ranking is performed remotely.
- Third-party ranking services `MUST NOT` be required for protocol participation.

### Model Portability

- Users `SHOULD` be able to change ranking models without changing the underlying protocol.
- Clients `SHOULD` support export or transfer of ranking preferences in a portable format.
- The ecosystem `SHOULD` define a stable interface between candidate-content retrieval and ranking execution.

### Low-Power Devices

- Clients on low-power devices `MAY` use smaller local models.
- Clients on low-power devices `MAY` delegate ranking to a user-chosen remote service.
- Clients `MUST` preserve local user preference state even when ranking is performed remotely.
- Clients on constrained devices `SHOULD` prefer hybrid ranking or lightweight local reranking over attempting full-device global feed inference.

## Supported Ranking Modes

- Local model runner:
  users may run local models through desktop or device-local tooling such as LM Studio or similar runtimes
- Hosted model provider:
  users may use remote state-of-the-art models hosted by third-party services when they choose
- Specialized ranking service:
  users may opt into domain-specific ranking services, such as a blog or topic curation service
- Hybrid mode:
  clients may combine local preference storage with remote ranking execution

## Private Context

Clients may use private local metadata for ranking, including:

- reading history
- hidden or muted topics
- explicit positive and negative preferences
- local embeddings or summaries
- personal trust lists
- device-local behavioral signals

This private context does not need to be published to the network.

Some private context should still be portable across the user's own devices. Protocol-standard encrypted private-state sync is preferable to forcing each client vendor to invent a proprietary cloud sync layer.

## Design Constraints

- Ranking logic must remain separable from publishing and storage.
- Clients should make ranking provenance clear to users.
- Third-party ranking should be opt-in.
- The protocol should expose enough metadata for ranking without forcing disclosure of private user state.
- The protocol should not assume that a mobile client can or should process the entire global network state locally.

## Related Documents

- `06-storage-indexing-and-ai-processing.md`
- `09-client-facing-products.md`
- `12-ranking-profile-and-model-interface.md`
- `13-network-ascii-architecture.md`
- `14-protocol-metadata-requirements.md`
- `15-reference-client-feed-flow.md`

## Open Decisions

- How should clients disclose ranking provenance in a consistent way?
