# Security, Moderation, and Compliance

## Objective

Define the network's trust model, validation rules, abuse resistance, and legal-policy boundaries.

## Scope

This document covers:

- message and payment verification
- network integrity and peer trust
- abuse and Sybil resistance
- moderation boundaries
- jurisdictional compliance

## Security Areas

- Identity and signatures:
  verify authorship and protect message integrity
- Payment linkage:
  prevent false or reused funding references and submission receipts
- Peer trust:
  define how nodes authenticate and evaluate each other
- Data integrity:
  verify retrieved content and index data
- Abuse resistance:
  reduce spam, replay, and resource exhaustion attacks

## Moderation Areas

- protocol-level rejection rules
- node-operator hosting and relay policies
- client-side filtering and ranking policies
- retention policy exceptions

## Baseline Moderation Model

ForYou does not rely on a single global feed or a single centralized moderation authority.

The baseline model is:

- the network accepts valid posts according to protocol and operator rules
- readers decide what they see through their own clients
- filtering and ranking happen primarily on the reader side
- node operators may still apply local hosting, relay, and legal-compliance policies

Network publication and reader visibility are separate concerns.

## Locality Principle

Network validity and local hosting legality are different things.

- a post can be valid in the network
- that same post may be unavailable from specific hosts or regions
- local removal does not imply global deletion
- the protocol `MUST NOT` require every host to store, relay, or serve every post

## Censorship-Resistance Boundary

ForYou should be designed for resistance to chokepoints, not for magical immunity.

The network becomes harder to suppress when it avoids dependence on:

- one provider
- one host
- one API surface
- one payment intermediary
- one client
- one transport path

The network may still experience local blocking, regional outages, or legal pressure. The goal is that other hosts, transports, caches, and providers can continue serving valid content where legally and technically possible.

## Compliance Areas

- local legal obligations for operators
- cross-jurisdiction behavior differences
- retention versus takedown conflicts
- operator disclosure and transparency expectations

## Required Clarifications

- Which threats are explicitly in scope?
- What content can a node refuse to store, relay, or index?
- What part of the moderation model is mandatory versus optional?
- How is illegal content handled when references are already replicated?

## Severe-Illegal Content Baseline

Launch should not assume that generic providers blindly propagate all metadata references.

For severe illegal content classes under applicable law, such as child sexual abuse material or similarly prohibited material:

- accepting providers `MUST` refuse publication when they have credible reason to believe the content is severe-illegal material under applicable law
- index providers `MUST` refuse to index or return metadata pointers for known severe-illegal material under applicable law
- hosts `MUST` refuse storage, relay, caching, or serving for known severe-illegal material under applicable law
- providers `MUST` support ingestion of shared deny-lists or hash lists where legally available and technically feasible to reduce repeated re-distribution

The protocol should distinguish between reader-side filtering for ordinary content and provider-side refusal to handle severe illegal material.

Launch note:

- This is a strict-liability risk area. Treating severe-illegal handling as optional creates operator liability.
- The protocol cannot guarantee detection of unknown illegal material, but it can require refusal behavior for known or credibly reported material.

## Takedown and Erasure Reality

The protocol is designed so that local removal does not imply global deletion. That property improves censorship resistance, but it creates legal friction in some jurisdictions.

Launch should therefore be explicit:

- `withdraw` is a protocol-visible tombstone and target-state update, not a guarantee of global deletion
- operators in some jurisdictions may be legally required to purge stored content and stored metadata earlier than their advertised retention floors
- operators should treat legally valid takedown or erasure requests as local obligations that can override service commitments

The spec should not claim a universal right-to-erasure guarantee across all hosts. It should instead specify best-effort local compliance behavior and make jurisdictional participation constraints explicit.

## Reader-Side Filtering

- Clients `SHOULD` treat filtering, muting, trust decisions, and feed shaping as reader-controlled behavior.
- The protocol `MUST NOT` require a single global ranking or filtering policy.
- Clients `MAY` use local AI or user-selected remote services to filter and rank content.
- Reader-side filtering `MUST NOT` be confused with protocol-level message validity.

## Lightweight-Interaction Abuse Model

Public lightweight interactions such as recommendations, topic follows, source follows, and thread subscriptions are useful social context, but they are easier to spam than paid public content writes.

For launch:

- providers accepting lightweight public interactions `MUST` apply admission controls such as funded allowance debits, rate limits, quotas, or equivalent abuse controls
- portable public interactions without funded allowance consumption or equivalent paid admission `SHOULD` be treated as low-trust or provider-local only
- clients and providers `MUST NOT` treat raw lightweight-interaction volume as high-trust ranking truth
- trust weighting, account age, graph quality, and reader-local context `SHOULD` matter more than raw totals
- abusive interaction floods `MAY` be deprioritized, rejected, or discounted without changing the validity rules for paid public content writes

This keeps the protocol expressive while limiting the value of bot-swarm inflation.

## Counterpoint Harassment Risk

`counterpoint` is a useful response primitive, but it is also an easy harassment primitive because it attaches conflict to a target without the target's consent.

Launch mitigations:

- clients `SHOULD` make `counterpoint` rendering a reader-controlled choice:
  collapsed by default, trust-weighted, or hidden unless explicitly expanded
- clients `SHOULD` support per-source and per-thread controls that can hide or downrank counterpoints without affecting network validity
- providers accepting `counterpoint` writes `SHOULD` apply per-target and per-author rate limits to reduce dogpiling and targeted harassment
- index providers `SHOULD` allow clients to request counterpoints as a separate optional stream rather than forcing them into the default reply stream
- clients and providers `MUST NOT` treat counterpoint volume as a positive engagement signal by default

## Operator Compliance Boundaries

- Node operators `MAY` refuse to host, relay, or index content based on local law or explicit operator policy.
- Operator policy does not define what every reader must see.
- Clients `SHOULD` make clear that a post can be validly published yet still be hidden, deprioritized, or unavailable in some environments.

Hosts are local legal actors:

- each host complies with the laws of the jurisdiction where it operates
- each host may choose whether it can store full content, relay metadata, or serve local access
- jurisdiction-specific restrictions apply at the host layer, not as a universal network rule

Providers should not be required to expose or relay metadata pointers for material they are legally prohibited from handling.

## Operator Policy Metadata

Launch baseline:

- operator policy metadata is optional at launch
- operator policy metadata is not exposed by default at launch
- if exposed, it `SHOULD` be treated as advisory rather than authoritative protocol truth
- clients `MAY` surface it to help explain availability differences across providers
- the protocol `MUST NOT` require operator policy metadata in order to publish or read content

## Client Fallback Model

- Clients `SHOULD` be able to query alternate hosts when content is unavailable from a specific provider.
- Clients `MAY` retrieve metadata from one host and full content from another.
- Clients `SHOULD` verify retrieved content by content address rather than trusting host identity alone.

Fallback and multi-source retrieval are central resilience features, not just convenience features.

## Open Decisions

- Whether the protocol should define any global content rejection rules
- Whether retained content may need special deletion handling in some jurisdictions
