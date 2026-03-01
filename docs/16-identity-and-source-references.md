# Identity and Source References

## Objective

Define the canonical identity format for authors, sources, trust lists, and source references used across the protocol and ranking system.

## Status

This document is a draft identity specification with a provisional launch baseline.

The keywords `MUST`, `SHOULD`, and `MAY` are to be interpreted as normative requirements for the launch baseline sections of this document. Other sections remain explanatory unless they are explicitly tied to launch behavior.

## Design Goals

- stable author references for posting and ranking
- portable source identity across clients
- compatible trust, mute, and preference lists
- minimal coupling between identity and any single client implementation

## Canonical Identity Reference

For launch, the baseline canonical identity format is still:

- `did:key:<identifier>`

However, `did:key` by itself is not a safe long-term account model unless the protocol supports key rotation and recovery.

Launch should therefore distinguish between:

- account identity:
  a stable long-lived `author_id` that represents the user's account reference
- signing identity:
  a possibly-rotated `signer_id` that produces message signatures under delegated authority from `author_id`

Both use `did:key` formatting at launch.

## Identity Requirements

- Every authored message `MUST` include an `author_id`.
- `author_id` `MUST` be stable enough to support trust, mute, block, and follow behavior over years.
- Clients `MUST` compare source references by canonical identifier, not by display name.
- Display names `MUST NOT` be treated as unique identifiers.

## Host and Service Identity

At launch, host and service identifiers should use the same canonical `did:key` form unless a later protocol revision standardizes an additional host-identity method.

- `host_id` should identify one host or service instance used in discovery and availability hints
- host aliases or brand names must not replace canonical host identifiers in protocol data

## Source Reference Uses

Source references are used for:

- authorship
- trust lists
- mute lists
- follow lists
- ranking preferences
- moderation and filtering

## Alias and Profile Layers

- An alias is a user-facing label associated with an identity.
- A profile is descriptive metadata associated with an identity.
- Alias and profile data `MUST NOT` replace the canonical identity reference in protocol messages.
- Clients `SHOULD` display aliases while retaining canonical identifiers internally.

### Alias Namespace Rule

Global unique usernames are not realistically enforceable without a centralized registry.

For launch, aliases should be treated as namespaced handles:

- `@alias@namespace`

Where `namespace` is one of:

- a provider identity (`did:key:...`)
- a user identity (`did:key:...`)
- a future standardized namespace method

Clients `SHOULD` display a short fingerprint of `author_id` alongside aliases so users can distinguish look-alike display names.

## Source List Formats

Lists such as `trusted_sources`, `muted_sources`, and `followed_sources` `SHOULD` store canonical identity references.

Example:

```json
{
  "trusted_sources": [
    "did:key:z6MkrJVnaZkeuWiRiwXQDq6rYmQXW1Lg31xHn3pV3hokW2Pp",
    "did:key:z6Mkf8x8P5gL6N8sYZZs1xP7vC18JNpDutLCRa14Qdqgttxy"
  ],
  "muted_sources": [
    "did:key:z6MkpTHR8V4QjzvY4xXHzkwmo7aX6ixkmKuuNHYsYkdivgLP"
  ]
}
```

## Validation Rules

- An identity reference `MUST` be parseable by the receiving implementation.
- Unsupported identity methods `MAY` be preserved as opaque references but `MUST NOT` be silently normalized to a different identity.
- A client `MUST NOT` collapse two identities merely because they share the same alias or display name.

## Launch Signing and Delegation Baseline

For launch:

- `author_id` identifies the stable account identity for trust and follow semantics
- `signature` verifies against either:
  `author_id` directly, or an explicitly declared `signer_id`
- if `signer_id` is used, the message `MUST` include a delegation proof signed by `author_id`

This enables key rotation and recovery without forcing users to lose their entire account history when a device key is lost.

### Delegation Proof Requirements

A delegation proof should bind at least:

- `author_id`
- `signer_id`
- a validity window (`valid_from`, `valid_until`)
- an optional scope (which message types the signer may produce)
- a delegation identifier for audit
- a signature by `author_id`

Clients and hosts `SHOULD` prefer short-lived delegations so a compromised signing key can be rotated out quickly.

### Key Rotation and Recovery

Launch should treat the recovery-capable key as `author_id` and allow normal posting with delegated signing keys.

Recovery flows are client UX, but protocol data must support:

- rotating to a new `signer_id` without changing `author_id`
- revoking or expiring old delegations
- keeping follow and trust relationships stable across signer rotation

## Future Identity-Stability Rule

Any future key-rotation or delegation design should preserve auditability.

At minimum, a future standard should make it possible to verify:

- which identity was replaced or delegated
- who authorized the change
- when the change took effect
- whether clients may continue trust relationships across the change

## Ranking Implications

- Ranking profiles `SHOULD` reference sources by canonical identity.
- Local trust scores `MUST` attach to canonical identity references.
- Source reputation or trust features `MUST NOT` alter the underlying identity identifier.

## Related Documents

- `04-data-and-message-formats.md`
- `11-attention-and-ranking-model.md`
- `12-ranking-profile-and-model-interface.md`
- `14-protocol-metadata-requirements.md`

## Open Decisions

- Whether delegation proof should be carried per-message or via a separately indexed delegation record
- Whether additional DID methods are worth standardizing after the `did:key` baseline is proven
