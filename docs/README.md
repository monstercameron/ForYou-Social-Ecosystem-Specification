# Specification index

## Scope and authority

ForYou specification release 1.0 covers:

- public post bytes and signatures;
- admission receipts;
- protocol fees and their settlement to the ForYou Foundation;
- retention;
- public download and verification.

Requirement language is defined [below](#normative-language). A role-specific requirement applies to an implementation that performs or advertises that role. A reader client need not operate a provider.

| Status | Documents |
| --- | --- |
| Normative core | The repository [README](../README.md), documents 01 through 07, document 09, the [API catalog](./API-catalog.md) and the [schemas](../schemas/launch.schema.json) |
| Optional profile | [Owner export profile](./10-owner-export-profile.md); normative only for an implementation that claims it |
| Nonnormative | [Operator guide](./08-operator-guide.md), [operator compliance guide](./11-operator-compliance-guide.md), reviews, examples and tests |

Each topic has one owning document. A cross-reference incorporates the owner's rule and never overrides it. Schema structure and prose semantics MUST both hold. A contradiction is a defect that blocks a conformance claim on the affected point. Nonnormative documents never override the normative core.

| Document | Owns |
| --- | --- |
| [01 Overview](./01-overview.md) | Scope, actors, architecture and limits |
| [02 Protocol](./02-protocol.md) | Byte formats, identifiers, signatures, record semantics, admission and verification |
| [03 Economics](./03-economics.md) | Fee schedule, provider balances, settlement to the Foundation, distribution and retention |
| [04 Compliance](./04-compliance.md) | Core restriction semantics, public status codes, operator disclosure |
| [05 Portability](./05-portability.md) | Public download, listing, incremental sync and the Lifetime Vault |
| [06 Governance](./06-governance.md) | Foundation, versioning and the release calendar |
| [07 Clients](./07-clients.md) | Protocol-visible client obligations |
| [08 Operator guide](./08-operator-guide.md) | Nonnormative operating notes for providers |
| [09 Quality](./09-quality.md) | Quality evidence: observations, signed reports and their limits |
| [10 Owner export profile](./10-owner-export-profile.md) | Optional export archive format, multipart rules and export encryption |
| [11 Operator compliance guide](./11-operator-compliance-guide.md) | Nonnormative intake, case management, per-market checklists, incident handling and funding disputes |
| [API catalog](./API-catalog.md) | Route and status reference; the owning documents define the requirements |

## Machine-readable contracts

- [Launch schema](../schemas/launch.schema.json): the root TransportMessage and the named message, admission, delegation, key-succession and listing definitions.
- [Operations schema](../schemas/operations.schema.json): a library of service definitions. A consumer MUST validate against the intended named definition, never against the library root.
- [Tests](../tests/README.md): executable vectors, schema checks and reference-model regressions. They are not a complete implementation.

## Release status and license

The set is frozen as release 1.0 only when the [release checklist](./06-governance.md#release-checklist) is complete and the release manifest is signed. An implementation MUST NOT advertise conformance to this specification as legal compliance, production security or a guarantee of availability.

The specification is licensed under the MIT License; see [LICENSE](../LICENSE).

## Normative language

MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in RFC 2119 and RFC 8174 when written in uppercase. In a normative document, two further forms are requirements of MUST strength:

- a sentence in the imperative ("reject", "verify", "never");
- a sentence stating what a party does ("the provider returns").

A lowercase "may" states a possibility, not a permission. Nonnormative documents use requirement keywords only inside an optional profile, where they bind an implementation that offers that profile.

Optional profiles: [owner export](./10-owner-export-profile.md), and the [bounded intake and recovery](./11-operator-compliance-guide.md#bounded-intake-and-recovery) section of the operator compliance guide. The rest of that guide is nonnormative advice.
