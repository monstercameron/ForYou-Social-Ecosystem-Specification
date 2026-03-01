# Core Protocol Architecture

## Objective

Define the core technical model for publishing, propagating, storing, and discovering content.

## Scope

This document covers:

- write path and read path
- content identification
- separation between metadata and full content
- network-level propagation assumptions

## Architectural Model

The current design assumes a layered system:

- Message layer:
  users create signed protocol messages
- Submission-funding layer:
  messages reference valid funding evidence through submission receipts or direct-payment fallback
- Metadata layer:
  searchable metadata is distributed across the network
- Content storage layer:
  full content is stored outside the metadata path and referenced by address
- Discovery layer:
  clients and AI services use metadata to locate relevant content

## Resilience Principles

ForYou should aim for multi-source resilience in content availability without pretending that any network can be literally unstoppable.

The core resilience rules are:

- no single mandatory host
- no single mandatory index provider
- no single mandatory client
- no single mandatory transport
- many cached copies of useful content
- content verification by signed message and content address after retrieval

The network should degrade gracefully under blocking, censorship, outages, or regional failures rather than failing as a whole.

## Required Architectural Decisions

- Canonical record:
  define what constitutes the authoritative existence of a post
- Acceptance rule:
  define the conditions under which the network accepts a message
- Ordering model:
  define whether content ordering is strictly global, partially ordered, or client-defined
- Retrieval model:
  define how a client resolves from a message reference to full content

## Baseline Write Path

The baseline write path is:

1. client constructs a canonical message envelope and typed payload
2. client signs the message using the author's identity key
3. client attaches either a provider submission receipt or a direct-payment fallback reference for any portable public message
4. bridge infrastructure verifies any referenced direct funding or direct-payment fallback transaction
5. flow nodes validate message shape, identity, signature, and submission funding status
6. accepted metadata is propagated to index providers and flow peers
7. referenced full content is stored or pinned by storage-capable participants
8. storage-capable participants retain accepted content and metadata according to network policy and local capacity

## Acceptance Rule

A message is considered accepted into the baseline network path when all of the following are true:

- the message schema is valid
- the signature verifies against `author_id`
- the message type is supported
- required submission funding has been satisfied through either a valid submission receipt or a valid direct-payment fallback
- referenced content address is present when required by the message type

Indexing and ranking do not determine validity. They happen after acceptance.

For launch, `valid enough for provisional acceptance` means the direct funding or direct-payment fallback meets the launch confirmation policy, or the submission receipt chains back to a sufficiently funded plan under provider policy.

## Canonical Record

The canonical record of message existence is the accepted signed message envelope plus its typed payload and any required verified submission funding evidence.

BTC or ETH settlement proves plan funding or fallback fee settlement. It is not the canonical store of social content metadata.

For launch, the protocol should not require application metadata to be written on-chain.

When an author later withdraws a message, the canonical record should transition to a tombstone-style target state rather than disappearing as if the message never existed.

## Locality and Availability

- Message validity is a network concern.
- Content availability is a host-level concern.
- The protocol `MUST NOT` assume that every valid post will be served by every host.
- Hosts `MAY` relay metadata broadly while serving full content selectively.
- Clients `SHOULD` be able to resolve content through alternate hosts where legally and technically available.

Detailed host-hint behavior, retention targets, and old-content recovery flows are defined in the storage and discovery documents rather than repeated here.

Simple locality model:

```text
valid in network != available from every host
```

## Retrieval Model

For launch, retrieval should satisfy these invariants:

- clients resolve from `message_id` to metadata and then to `content_address`
- clients may try multiple providers or hinted hosts
- successful retrieval is verified by `content_address`
- no single host or provider is required for a valid object to remain reachable

At a high level, retrieval behaves like this:

```text
message_id
  ->
metadata
  ->
content_address
  ->
candidate hosts
  ->
fetch from any working path
  ->
verify
```

Detailed host-hint behavior belongs in the storage document. Canonical endpoint definitions belong in the API document.

## Ordering Model

- Payment settlement ordering and message creation ordering are distinct concerns.
- The protocol `MUST NOT` require a single global feed order for all clients.
- Index providers `MAY` expose deterministic sort orders for retrieval, such as timestamp descending.
- Final presentation order remains a client-side or ranking-layer decision.

## Duplicate and Replay Handling

- Nodes `MUST` reject duplicate `message_id` values already accepted in the same validity domain.
- Nodes `MUST` reject messages whose signatures do not match their canonical serialization.
- Nodes `SHOULD` reject replayed submission receipts or replayed direct-payment fallback references when they are intended for one-time settlement.

## Target-State Rule

- Referencing messages such as replies, quotes, counterpoints, and recommendations remain valid historical messages even if the target later becomes withdrawn, unavailable, or locally blocked.
- The protocol `MUST NOT` require cascading deletion of dependent interaction messages when a target is withdrawn.
- Providers and clients `SHOULD` expose an explicit target state rather than leaving a dangling unresolved reference.

## System Boundaries

- Protocol responsibilities:
  message validity, identity, references, submission-funding linkage, and baseline interoperability requirements
- Storage responsibilities:
  availability of content payloads and retention
- Client responsibilities:
  ranking, presentation, personalization, and local policy enforcement where applicable

## Anti-Chokepoint Rule

The protocol should avoid requiring any single chokepoint for normal operation.

This includes:

- one domain
- one API provider
- one publish provider
- one discovery path
- one transport family

## Open Decisions

- What transport assumptions are mandatory for interoperable hosts?
- How should conflicting writes be handled if future protocol revisions allow edits or replacements?
