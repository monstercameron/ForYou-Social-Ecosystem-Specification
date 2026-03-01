# Governance and Dispute Resolution

## Objective

Define how the network changes over time, how collective decisions are made, and how disputes are handled.

## Scope

This document covers:

- governance bodies and roles
- proposal and voting processes
- scope of governance authority
- dispute handling mechanisms

## Governance Functions

- protocol upgrades
- fee parameter changes
- role certification or recognition
- policy publication
- ecosystem coordination

## Launch Governance Baseline

At launch, governance should be narrow.

The baseline governance role is:

- coordinate protocol revisions
- publish reference policies and operational guidance
- document fee parameter decisions
- coordinate ecosystem discussion when hosts or clients need interoperability changes

Governance should not be treated as:

- a mandatory source of feed ranking
- a universal moderation authority
- a mechanism for controlling what every compliant client must show readers

## Launch Governance Process

For launch, governance should use a simple published-process model:

- protocol changes are proposed in public
- decisions are recorded off-chain in versioned specification updates
- implementers choose whether to adopt those versioned updates
- interoperability depends on shared adoption, not on coercive central control

This keeps governance real enough to coordinate the network without pretending there is already a mature constitutional system in place.

## Versioning and Proposal Lifecycle

For launch, governance should use a simple versioned editorial process:

- every proposal receives a public identifier
- every proposal moves through `draft`, `review`, `accepted`, `active`, or `deprecated`
- accepted changes are published in a versioned specification release
- breaking interoperability changes should require a new major protocol version
- backward-compatible additions should use a minor version update

The launch publication authority is the maintainers of the public versioned specification set.

That authority is limited to publishing the current reference version and change history. It does not make a change effective by decree; implementations make a change effective by adopting it.

## Adoption Rule

A launch governance decision should be treated as operationally active when:

- it has been published in a versioned specification update
- at least one publicly available implementation has adopted it
- independent operators or clients can choose to adopt or reject it explicitly

Compatibility statements should be tied to published version numbers rather than to vague claims of being "current."

## Required Decisions

- Membership rule:
  launch governance should be open to operator, developer, and ecosystem review, with final publication handled by the maintainers of the versioned spec process
- Voting rule:
  launch does not require token voting or on-chain voting; consensus should be demonstrated through public review and implementation adoption
- Authority rule:
  governance may define reference protocol versions, fee-schedule guidance, and interoperability guidance, but it must not dictate reader-level ranking or visibility policy
- Enforcement rule:
  governance outputs become effective only when they are implemented by clients, hosts, or published reference software

## Dispute Scope

For launch:

- a protocol dispute is a disagreement about message validity, interoperability rules, version meaning, or required network behavior
- an operator dispute is a disagreement about local hosting, relay, pricing, retention, or policy choices that do not redefine protocol validity for everyone else
- emergency guidance may be published quickly during attacks or legal emergencies, but it remains advisory until implementations adopt it

## Launch Dispute Baseline

For launch:

- protocol disputes should be resolved through published clarifications or versioned spec updates
- operator disputes should remain local unless they affect interoperability
- emergency guidance may be published quickly, but it is advisory until adopted by implementations

## Open Decisions

- Whether governance should remain a lightweight editorial-operator process after launch or evolve into a broader membership system
