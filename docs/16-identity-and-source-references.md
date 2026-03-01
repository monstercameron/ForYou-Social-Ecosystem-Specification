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

The baseline canonical identity format is:

- `did:key:<identifier>`

Implementations `MAY` support additional DID methods, but a conforming client `MUST` be able to preserve and compare canonical source references without ambiguity.

For launch, `did:key` is sufficient and should be treated as the required interoperable baseline for authored content and source lists.

## Identity Requirements

- Every authored message `MUST` include an `author_id`.
- `author_id` `MUST` be stable enough to support trust, mute, block, and follow behavior.
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

## Launch Signing Assumption

For launch:

- `author_id` identifies the signing key material used to verify `signature`
- the signer for a message `MUST` correspond directly to `author_id`
- delegated signing and key-rotation flows are deferred until a later protocol revision unless explicitly standardized

If key rotation is needed before a standard exists, the rotated identity should be treated as a new identity rather than silently mutating the old one.

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

- How a future key-rotation mechanism should preserve continuity without weakening trust semantics
- Whether additional DID methods are worth standardizing after the `did:key` baseline is proven
