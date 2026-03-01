# Network Roles and Infrastructure

## Objective

Define the node roles and operational responsibilities in the ForYou ecosystem.

## Scope

This document covers:

- named ecosystem layers
- node categories
- role responsibilities
- role interactions

## Ecosystem Layers

- ForYou Network:
  the protocol layer responsible for content exchange and discovery data
- ForYou Federation:
  the governance layer responsible for policy and protocol evolution

## Node Roles

- Flow Node:
  propagates new messages and may maintain regional or local caches
- Bridge Node:
  verifies external payment events and produces normalized payment status for the network

## Role Responsibilities

- Flow Node responsibilities:
  relay messages, maintain availability, support fast retrieval, participate in retention, and help distribute cached content
- Bridge Node responsibilities:
  verify BTC and ETH funding or direct-payment fallback references, expose confirmation status, and reduce payment interpretation ambiguity

## Revenue-Relevant Role Classes

For launch, the economic model should recognize that different roles perform different work.

Relevant launch service classes are:

- ingress:
  accepts funded writes and issues submission receipts
- discovery:
  serves candidate metadata and discovery responses
- retrieval:
  serves full content and cache hits
- retention:
  honors retained-provider commitments over time
- verification:
  verifies BTC or ETH funding and related receipt chains

One implementation may perform several classes at once, but accounting should still distinguish the work categories.

## Host Lifecycle

Baseline host lifecycle:

1. install host software
2. generate host identity and configuration
3. connect to known bootstrap peers
4. sync recent metadata and network state needed for participation
5. begin relaying accepted metadata
6. begin serving content and caches according to local capacity, policy, and jurisdiction

Simple model:

```text
New host -> bootstrap peers -> sync metadata -> join relay -> serve what it can
```

## Bootstrap-Peer Discovery

For launch, hosts discover the network through a simple bootstrap model:

- the operator configures one or more known bootstrap peers
- the host connects to those peers
- the host learns additional peers through normal network participation
- the host refreshes peer knowledge over time as peers appear or disappear

Simple model:

```text
configured bootstrap peers -> initial connections -> peer learning -> normal participation
```

Launch should prefer a bootstrap-peer list over a more complex discovery system.

## Host Responsibilities Under Locality

- A host may accept and relay metadata without serving every full content object.
- A host may store full content selectively based on locality, demand, and policy.
- A host may refuse storage, relay, or serving for some content under local law or explicit operator policy.
- A host should still preserve protocol correctness for the content it does handle.

## Cache and Swarm Expectations

Hosts should not be treated only as fixed origin servers.

At scale, a host may act as:

- metadata relay
- cache for hot content
- retention node for colder content
- discovery source for alternate host paths

The network becomes more resilient when popular or important content is available from many hosts rather than one origin.

## Host Graph

For launch, hosts should contribute to a refreshable host graph.

The host graph is not a perfect global map. It is a partial, overlapping view of:

- peer hosts
- likely content locations
- last-seen availability hints

Each host should be able to expose:

- peer references:
  other hosts it knows about
- content availability hints:
  hosts it believes may still have a given content object
- freshness data:
  when the peer or content hint was last seen to be usable

At launch, a host hint should minimally include:

- `host_id`
- `endpoint`
- `last_seen`

`host_id` should use the canonical host identity format defined by the identity specification.

Hosts may include optional locality or policy hints, but those are advisory.

For launch, `endpoint` should be a single canonical base URL for the host's primary retrieval or discovery surface. Multi-transport advertisement can be added later, but launch should prefer one clear endpoint per hint.

The host graph should improve over time through successful connections, successful fetches, and normal peer exchange.

## Minimal Persistent Host State

At launch, a host should persist at least:

- host identity and configuration
- known peer list or bootstrap configuration
- accepted metadata index needed for participation
- cached or retained content chosen by the operator
- local policy and jurisdiction settings
- peer references and recently learned content-location hints

## Interface Expectations

- Each role should have a defined set of APIs or protocol endpoints.
- Each role should define what state it stores and what state it can reconstruct.
- Each role should define whether its outputs are authoritative, advisory, or cacheable.

## Transport Diversity Direction

Launch may start with one baseline HTTPS endpoint model, but host design should leave room for multiple transports over time.

Future transports may include:

- alternate HTTPS front doors
- long-lived streaming connections
- peer-to-peer transport layers
- local or regional peer discovery paths

The object and verification model should survive transport change.

## Bridge Node Baseline Interface

A bridge node `SHOULD` expose:

- payment or plan-funding verification by declared chain and transaction identifier
- normalized payment status output
- clear failure reasons for malformed or insufficient funding references

Bridge output is authoritative for payment interpretation within the node's operating policy, but it does not replace message-signature verification or schema validation performed elsewhere.

## Bridge Proof Shape

A bridge proof should minimally include:

- `chain`
- `transaction_id`
- `verification_status`
- `confirmation_state`
- `observed_amount`
- `bridge_id`

This proof is the normalized payment-verification artifact consumed by flow nodes and related services.

## Launch-Critical Roles

For launch, the minimum viable network likely requires:

- flow nodes for message propagation and basic acceptance
- bridge nodes for payment verification
- at least one index-provider-capable node path for candidate discovery

Retention exists at launch, but it is part of the baseline posting service rather than a separate user-facing service.

## Open Decisions

- Can one implementation combine Flow and Bridge roles?
- How should role-level service guarantees be measured at launch?

## Related Documents

- `17-index-provider-and-candidate-chunk-api.md`
