# Specification index

## Scope and authority

The current pre-release set consists only of documents 01–07 below plus the two schema libraries. Wire/security profile 1.0 and operations-1.0 are complementary requirements. MUST, MUST NOT, SHOULD and MAY express mandatory requirements, prohibitions, recommendations and permitted choices respectively. Service-role requirements apply to implementations claiming that role; a reader client need not operate a payment provider.

Each topic has one owner. Cross-references incorporate that owner's details, not a later override. Both schema structure and prose semantics must hold. A contradiction is a specification defect requiring resolution before claiming conformance. Reviews, synthetic examples and tests are supporting evidence, not alternative requirements or security certification.

| Document | Owns |
| --- | --- |
| [01 Overview](./01-overview.md) | Core principles, actors, architecture and limits |
| [02 Protocol](./02-protocol.md) | Byte formats, signatures, message semantics, authorization, staging, private sync and safe retrieval |
| [03 Economics](./03-economics.md) | Plans/invoices, fund accounting, service limits, storage/finalization obligations, renewal and reserve rules |
| [04 Compliance](./04-compliance.md) | Regional assessment, operator disclosure, notices/appeals, privacy/consent, legal restrictions and incident response |
| [05 Portability](./05-portability.md) | Provider choice, follow discovery, export/import, backup/recovery and replication independence |
| [06 Governance](./06-governance.md) | Release process, license authorization, versioning, independent review and pilot gates |
| [07 Clients](./07-clients.md) | User-facing publishing/reading flows and optional model interface |

## Machine-readable contracts

- [Launch schema](../schemas/launch.schema.json): root TransportMessage plus named admission, funding, retrieval and optional ranking definitions.
- [Operations schema](../schemas/operations.schema.json): named service-offer, renewal, manifest, export and administrative-request definitions. It is a library: consumers MUST reference the intended definition rather than accepting arbitrary objects against the library root.
- [Tests](../tests/README.md): executable vectors, schema checks and reference-model regressions. These are not complete service implementations.

## Release status

This set is not yet frozen or deployed. Do not advertise worldwide legal compliance, financial sustainability, production security, guaranteed account recovery or an open-source license that has not been granted. The concrete evidence gates are in [governance](./06-governance.md). The [review record](../reviews/consolidation-review.md) describes consolidation and final review without adding protocol rules.
