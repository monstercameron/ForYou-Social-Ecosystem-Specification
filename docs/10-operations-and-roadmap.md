# Operations and Roadmap

## Objective

Define the practical operating requirements for network participants and identify the major work remaining before broader deployment.

## Scope

This document covers:

- node operating expectations
- health and reliability metrics
- resilience planning
- launch dependencies
- post-launch roadmap items

## Operations Areas

- hardware expectations
- uptime and performance targets
- health reporting
- automated recovery
- partition and censorship resilience

## Launch Operating Priorities

For launch, operations should focus on the minimum behaviors needed to keep the network usable:

- reliable publish acceptance
- redundant metadata propagation
- sufficient bridge availability for BTC and ETH verification
- enough retained storage to keep recent and important content retrievable
- multiple provider paths for discovery and old-content recovery
- clear operator visibility into peer health, backlog, and payment-verification failures
- no single public operator becoming a practical dependency for normal network use

## Shared-Service Accounting Support

If operators participate in network service buckets, they should be able to expose enough evidence for bucket accounting during each window.

Launch-support expectations should include:

- ingress providers can report accepted paid submissions
- discovery providers can report valid candidate responses served
- retrieval providers can report successful content responses served
- retained providers can report committed retention classes and auditable availability
- bridge or verification providers can report valid funding verifications and receipt issuance volume

These reports should be auditable and should avoid rewarding obvious self-generated loops.

## Minimum Launch Operator Capabilities

An operator participating in the launch network should be able to:

- persist host identity and configuration across restarts
- maintain bootstrap peers and refresh peer knowledge over time
- relay accepted metadata to at least one additional peer path
- either perform bridge verification or consume normalized bridge results reliably
- serve the metadata, content, or discovery role it advertises
- surface explicit miss or failure states instead of silent timeouts where practical

## Reference Service Targets

For public launch operators, the following targets should be treated as strong guidance:

- public publish paths should target at least 99% monthly availability
- public metadata and discovery endpoints should target at least 95% monthly availability
- accepted metadata should normally propagate into at least one additional peer or index path within 60 seconds under non-degraded conditions
- operators should publish supported chains, fee classes, and known maintenance windows clearly
- public operators should prefer caching and re-serving high-demand content rather than acting only as thin pass-throughs

## Measurement Baseline

At launch, public operator targets should be measured in a simple, inspectable way:

- availability should be measured over a rolling 30-day window
- publish-path availability means the operator accepts a valid submission request and returns an explicit success or explicit failure state
- metadata or discovery availability means the advertised API responds with a parseable success or explicit miss state rather than timing out
- the 60-second propagation target should be interpreted as a best-effort launch SLO for at least 95% of accepted messages under non-degraded conditions

Operators should not advertise a target they do not actively measure.

If operators claim shared-bucket rewards, they should also measure and publish enough evidence to support those claims for the relevant accounting window.

## Retention Capability Disclosure

If a public operator claims retained-provider behavior, it should publish:

- whether it is a baseline provider or retained provider
- its stated metadata-retention floor
- its stated full-content-retention floor
- any major locality or policy limitations on retention

Clients and other operators should treat these disclosures as real service commitments rather than vague aspirations.

## Operational Questions

- How should health claims be verified across operators?
- What additional role-specific objectives are needed beyond the baseline launch targets?

## Roadmap Areas

- stronger scalability model
- more efficient payment architecture
- improved discovery and ranking systems
- better resilience and observability
- possible expansion to additional networks or services

## Resilience Roadmap

The most important long-term resilience upgrades are:

- stronger peer exchange and host-graph propagation
- more swarm-compatible retrieval for full content
- wider cache participation across hosts and clients
- transport diversity beyond one baseline HTTPS path
- better degraded-mode behavior under censorship, blocking, or provider outages

## Launch Planning Questions

- Which unresolved decisions block interoperability?
- Which features can remain experimental after launch?

## Open Decisions

- Whether operational requirements are part of the protocol or only reference guidance
- Whether node certification is needed for public launch operators
