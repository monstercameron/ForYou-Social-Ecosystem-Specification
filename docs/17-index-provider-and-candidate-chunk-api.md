# Index Provider and Candidate Chunk API

## Objective

Define how clients fetch candidate metadata from index providers or full nodes for local ranking and selective retrieval.

## Status

This document is a draft transport and API specification with a provisional launch baseline.

The keywords `MUST`, `SHOULD`, and `MAY` are to be interpreted as normative requirements for the launch baseline sections of this document. Other sections remain explanatory unless they are explicitly tied to launch behavior.

## Design Goals

- allow lightweight retrieval of rankable metadata
- keep full-content retrieval separate from candidate discovery
- support local-first ranking workflows
- allow multiple index providers to coexist
- keep private portable user-state out of public discovery surfaces

## Candidate Gatekeeping Reality

Clients can only rank what they receive as candidates. That means candidate selection is an upstream power layer.

Launch mitigations:

- clients `SHOULD` query multiple independent providers and merge candidate sets
- providers `SHOULD` offer at least one "broad" candidate mode (recent, random sample, or unfiltered-by-topic) so new users are not trapped in a zero-candidate cold start
- clients `SHOULD` treat provider candidate sets as advisory inputs rather than as the authoritative universe of content

This document defines the canonical launch endpoint surface. Higher-level retrieval invariants belong in the architecture document, and availability/retention behavior belongs in the storage document.

## Roles

- Index provider:
  serves candidate metadata chunks
- Client:
  requests, validates, ranks, and selectively expands candidate sets
- Storage provider:
  serves full content referenced by candidate metadata

Read and discovery infrastructure should be treated as real services with real operating cost, not as an unbounded free side effect of publishing.

## Bootstrap and Provider Discovery

For launch, clients and hosts may discover index providers through:

- configured provider lists
- client-bundled defaults
- known peer or host recommendations

Launch should prefer simple configured discovery over a more complex decentralized provider-discovery system.

## Provider Service Terms

At launch, a provider may publish service terms for discovery and retrieval, including:

- public access limits
- authenticated or subscribed access tiers
- bundled access for users of the same operator's publish plans
- maintenance windows
- locality or policy restrictions

The protocol should not assume that every serious provider offers unlimited anonymous reads for free.

### Optional Service-Access Evidence

To avoid a pure free-rider model on the read path, providers `MAY` require service-access evidence for higher-volume discovery or retrieval.

Launch direction:

- a provider `MAY` accept a provider-signed token as service-access evidence
- the token may be derived from the user's funded plan (bundled access), a reader plan, or an operator subscription
- requests without evidence may still be served under a limited public tier

This document does not standardize one mandatory token transport at launch. Providers should keep access terms explicit and simple.

## Host and Content Hints

For launch, providers and hosts may also expose advisory discovery hints.

Useful hint types:

- peer host references
- likely content-host references for a content address
- `last_seen` timestamps for those hints

These hints help clients and hosts build a partial map of the network without relying on a central directory.

At launch, a host hint `SHOULD` minimally include:

- `host_id`
- `endpoint`
- `last_seen`

`host_id` should use the canonical host identity format defined by the identity specification.

For launch, `endpoint` should be one canonical HTTPS base URL. Providers may describe richer transport capability later, but clients should not have to resolve a transport list to try a hinted host.

Optional fields may include:

- jurisdiction hint
- advisory policy hint
- transport capabilities
- confidence score

## Candidate Chunk Model

A candidate chunk is a collection of metadata records intended for ranking or filtering.

Each candidate chunk `MUST` include:

- `chunk_id`
- `generated_at`
- `items`

Each item `MUST` include the minimum metadata required by the metadata requirements document.

## Request Parameters

Clients `MAY` request chunks using filters such as:

- time window
- topic filter
- language filter
- author filter
- content type filter
- pagination cursor
- maximum item count

Topic note:

- `target_topic` keys are lexical identifiers, not a universal global ontology.
- providers `MAY` publish recommended topic taxonomies, alias maps, or suggested keys, but clients should not assume cross-provider semantic equivalence unless explicitly declared.

## Response Shape

Example:

```json
{
  "chunk_id": "chunk-20260301-001",
  "generated_at": "2026-03-01T14:30:00Z",
  "items": [
    {
      "message_id": "msg-123",
      "author_id": "did:key:z6MkrJVnaZkeuWiRiwXQDq6rYmQXW1Lg31xHn3pV3hokW2Pp",
      "timestamp": "2026-03-01T14:00:00Z",
      "content_type": "post",
      "content_address": "ipfs://bafyexample",
      "language": "en",
      "is_ad": false
    }
  ],
  "next_cursor": "cursor-002"
}
```

An implementation may also expose discovery hints alongside content metadata.

Example:

```json
{
  "content_address": "ipfs://bafyexample",
  "host_hints": [
    {
      "host_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
      "endpoint": "https://host-c.example.net",
      "last_seen": "2026-03-01T13:00:00Z"
    },
    {
      "host_id": "did:key:z6Mkp8M4Q8T7qvR2nXwQ2X4c7u9aBRx9M3q7wYf9QnL5zJ6b",
      "endpoint": "https://host-f.example.net",
      "last_seen": "2026-02-28T20:00:00Z"
    }
  ]
}
```

## Client Requirements

- Clients `SHOULD` fetch metadata before fetching full content.
- Clients `MUST` validate chunk shape and item shape before ranking.
- Clients `MAY` query multiple providers and merge candidate sets locally.
- Clients `SHOULD` treat provider disagreement as a recoverable condition rather than a protocol failure.
- Clients `SHOULD NOT` depend on a single host for old-content discovery when alternate sources are available.
- Clients `MAY` walk peer and content hints to build a partial local map of the network.
- Clients `SHOULD` request or consult multiple hint sources before concluding that old content is unavailable.

## Provider Requirements

- Providers `MUST` return parseable candidate metadata.
- Providers `SHOULD` support pagination or chunk cursors.
- Providers `SHOULD` expose predictable filtering semantics.
- Providers `MUST NOT` require a ranking service in order to access candidate metadata.
- Providers `MUST NOT` expose encrypted private-state sync records through public candidate endpoints.
- Providers `MAY` expose peer and content-location hints as advisory discovery data.
- Providers `SHOULD NOT` expose peer or content-location hints by default unless the client asks for them or the provider bundles them as part of a documented discovery mode.
- Providers `SHOULD` expire or downgrade stale host hints rather than returning them indefinitely as fresh guidance.
- Providers `SHOULD` expose explicit `message_status` or `target_status` metadata when a referenced object is withdrawn, unavailable, or blocked.

If a provider supports encrypted private-state sync, it should expose that through a separate authenticated surface rather than mixing it into public discovery responses.

## Launch REST Baseline

For launch, providers should expose a simple HTTPS REST surface.

The baseline discovery endpoints should be:

- `GET /v1/candidates`
- `GET /v1/content-hints/{content_address}`
- `GET /v1/hosts/{host_id}`
- `GET /v1/content/{content_address}`

The baseline retrieval query for `GET /v1/candidates` should support:

- `limit`
- `cursor`
- `author_id`
- `content_type`
- `language`
- `since`

The baseline retrieval path for `GET /v1/content/{content_address}` should return either:

- the canonical content object for that address
- a verifiable miss or unavailable response

Content retrieval should be interoperable across accepting providers, storage providers, and hinted hosts that advertise a canonical launch endpoint.

GraphQL may be added later, but launch interoperability should not depend on it.

## Launch Endpoint Examples

Candidate request example:

```text
GET /v1/candidates?limit=50&content_type=post&language=en&since=2026-03-01T00:00:00Z
```

Content-hint request example:

```text
GET /v1/content-hints/ipfs%3A%2F%2Fbafyexample
```

Host request example:

```text
GET /v1/hosts/did%3Akey%3Az6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD
```

## Verification

- Clients `SHOULD` verify item signatures or signature status before promoting content into high-trust flows.
- Providers `MAY` include integrity or proof metadata for chunks.
- Chunk-level integrity data, if present, `SHOULD` be verifiable independently of transport.
- Clients `MUST` verify retrieved full content against the requested `content_address` before treating it as a successful fetch.

## Transport Options

- HTTPS REST `MUST` be supported at launch for interoperable providers.
- GraphQL `MAY` be supported as an alternative query surface.
- Push or subscription mechanisms `MAY` be added for near-real-time updates.

## Error Handling

- If a provider returns malformed metadata, clients `MUST` reject the malformed items.
- If a provider is unavailable, clients `SHOULD` fall back to alternate providers or cached chunks.
- If filtering parameters are unsupported, providers `SHOULD` respond explicitly rather than silently changing semantics.
- If host hints are stale or missing, clients `SHOULD` continue with alternate providers, cached hints, or direct host retries.

For `GET /v1/content/{content_address}`, providers should return explicit miss or unavailable responses rather than silently hanging when content is absent or locally blocked.

## Hint Freshness

For launch, clients and providers should treat host hints older than 7 days as stale by default.

Stale hints may still be retried opportunistically, but they should not be treated as high-confidence discovery guidance.

## Availability Graph Principle

The network should maintain a refreshable host graph where hosts can point to:

- other hosts
- likely content locations

This graph is partial, redundant, and expected to change over time. It does not need to be globally complete in order to be useful.

## Old-Post Recovery Example

```text
old message_id
  ->
provider A returns content_address + host hints
  ->
provider B returns the same content_address + different host hints
  ->
client merges hints
  ->
host 1 miss
  ->
host 2 timeout
  ->
host 3 hit
  ->
fetch
  ->
verify by content address
  ->
cache result and keep successful host path
```

## Canonical Content Retrieval Example

Request:

```text
GET /v1/content/ipfs%3A%2F%2Fbafyexample
```

Successful response example:

```json
{
  "content_address": "ipfs://bafyexample",
  "message_id": "msg-123",
  "content_format": "markdown",
  "content": "# Example\n\nFull content body.",
  "retrieved_at": "2026-03-01T14:32:00Z"
}
```

Unavailable response example:

```json
{
  "content_address": "ipfs://bafyexample",
  "status": "unavailable",
  "reason": "not_retained_locally"
}
```

## Related Documents

- `03-network-roles-and-infrastructure.md`
- `04-data-and-message-formats.md`
- `06-storage-indexing-and-ai-processing.md`
- `14-protocol-metadata-requirements.md`
- `15-reference-client-feed-flow.md`

## Open Decisions

- Whether provider-signed chunk envelopes are needed in addition to item-level verification
- What optional GraphQL or push surface is worth standardizing after the REST baseline is stable
