# Host Operator Experience

## Objective

Define the experience and operational expectations for a host operator participating in the ForYou network.

## Scope

This document covers:

- host operator mental model
- host lifecycle and daily operation
- locality and compliance experience
- operator-facing failure handling

## Core Mental Model

From the host operator's perspective:

- run a compatible host
- join through bootstrap peers
- relay accepted metadata
- serve the roles the host advertises
- comply with local law
- earn publish-related revenue if acting as an accepting provider

## Host Goals

- join the network without central permission
- stay interoperable with other hosts and clients
- serve content or metadata reliably within local capacity
- make locality and policy boundaries explicit
- recover from peer failures, stale hints, and degraded dependencies

## Baseline Host Journey

1. install host software
2. generate host identity and configuration
3. configure bootstrap peers
4. join the network and sync metadata
5. decide which functions to serve
6. publish fee schedules if acting as an accepting provider
7. publish any retention capability commitments if acting as a retained provider
8. maintain peer knowledge, retained content, and service health
9. update implementation as protocol revisions are adopted

## Host UX Requirements

- The host `MUST` preserve identity and configuration across restarts.
- The host `SHOULD` expose clear failure states rather than silent degradation.
- The host `MUST` make advertised roles match actual behavior.
- The host `SHOULD` expose advisory host hints and discovery data in a consistent way.
- The host `MUST NOT` imply that local policy decisions represent universal protocol truth.

## Host Locality Model

- a host may relay metadata without serving every full content object
- a host may refuse some storage or serving actions under local law or operator policy
- a host may still participate in the network even with selective availability
- local removal does not imply global deletion

## Host Revenue Model

If the host is an accepting provider:

- it may receive plan funding directly
- it may publish supported chains, plan classes, fee classes, and recipient references
- it may share revenue operationally with verification, index, or storage partners
- it may contribute a network service share into shared service buckets

If the host advertises retained-provider behavior:

- it should publish its retention floor clearly
- it should treat that published floor as a real service commitment

If the host is not an accepting provider:

- it may still contribute relay, storage, or discovery capacity as part of the broader network
- it may earn from shared service buckets if it performs auditable work in those classes

## Shared-Bucket Expectations

If the host participates in shared-bucket rewards:

- it should know which service classes it is claiming
- it should expose auditable evidence for work done during the relevant accounting window
- it should not expect self-generated traffic or fake demand to count as rewarded work

## Operator Failure Cases

- peer loss
- funding verification outage
- stale host hints
- storage miss
- local legal restriction
- version drift from other hosts

Operators should be able to identify which failures are local, upstream, or protocol-level.

## Trust Expectations

- operators should know what parts of their output are authoritative and what parts are advisory
- operators should be able to remain compatible without adopting every optional feature
- operators should understand that reader visibility is not controlled at the host layer

## Related Documents

- `03-network-roles-and-infrastructure.md`
- `07-security-moderation-and-compliance.md`
- `10-operations-and-roadmap.md`

## Open Decisions

- Whether public launch hosts should publish a standard operator status page or machine-readable health document
