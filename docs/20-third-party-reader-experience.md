# Third-Party Reader Experience

## Objective

Define the experience and expectations for a third-party reader client or service built on the ForYou protocol.

## Scope

This document covers:

- third-party client mental model
- interoperability expectations
- discovery and ranking expectations
- service-provider UX obligations

## Core Mental Model

A third-party reader is not a privileged platform layer.

It is:

- another compatible client or reading service
- a consumer of protocol metadata and content
- a presenter of reader-controlled ranking and filtering
- an implementation that competes on experience, not ownership of the network

## Third-Party Reader Goals

- connect to the network without special permission
- fetch metadata through standard provider paths
- rank or display content without becoming protocol authority
- explain its own ranking or filtering choices clearly
- remain replaceable by the user

## Baseline Third-Party Reader Journey

1. discover one or more providers
2. fetch candidate metadata through the standard API
3. satisfy any applicable reader-service terms or subscription requirements
4. apply local or service-side ranking according to user choice
5. retrieve full content by `content_address`
6. display a reader-controlled feed
7. expose public source controls such as follow separately from private curation controls such as mute and trust

## UX and Interoperability Requirements

- A third-party reader `MUST` use the baseline interoperable API surface at launch.
- A third-party reader `MUST NOT` imply exclusive control over protocol content.
- A third-party reader `MUST` disclose when ranking is remote or service-side.
- A third-party reader `SHOULD` preserve user portability of source lists and ranking intent where practical.
- A third-party reader `MUST NOT` redefine protocol validity through its own ranking outputs.

## Reader-Service Responsibilities

- respect canonical identity references
- use standard content and metadata fields
- handle unavailable content gracefully
- make service terms or paid access requirements explicit when they exist
- make local versus remote processing clear
- avoid hiding interoperability behind proprietary transport assumptions

## Failure Cases

- provider disagreement
- unsupported optional fields
- stale host hints
- partial content availability
- remote model or service degradation

Third-party readers should degrade gracefully rather than presenting protocol breakage when only one provider path fails.

## Trust Expectations

- users should be able to leave a third-party reader without losing protocol access
- third-party readers should compete on ranking quality, design, and features
- protocol compatibility should matter more than product branding

## Related Documents

- `09-client-facing-products.md`
- `12-ranking-profile-and-model-interface.md`
- `17-index-provider-and-candidate-chunk-api.md`

## Open Decisions

- How much ranking-profile portability should be mandatory across third-party readers at launch?
