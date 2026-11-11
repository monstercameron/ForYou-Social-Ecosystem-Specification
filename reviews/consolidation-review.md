# Consolidation review

Date: 2026-11-11. This is a nonnormative review record, not a second specification.


This record describes the earlier consolidation snapshot. The subsequent text-only/CDN revision and its validation are recorded in [the external-media review](./text-only-media-review.md); counts and retained retrieval contracts below are historical.

## Consolidation

The current specification consists of seven documents listed in [the documentation index](../docs/README.md). The former concept documents, historical override notices, obsolete examples and successive audit reports have been removed from the active repository documentation. A pre-consolidation snapshot was preserved outside the repository before removal; original tracked history also remains in Git.

| Consolidated owner | Material retained |
| --- | --- |
| Overview | Core principles, roles, trust boundaries and architecture |
| Protocol | Audited message, signing, authorization, state, sync and retrieval requirements, including the previously incorporated destination checks |
| Economics | Current funding, immutable plans/offers, service lifecycle, renewal, reserves and sustainability gates |
| Compliance | Current regional assessment, rights, privacy, remote-consent, notices and incident requirements |
| Portability | Current discovery, migration, export, backup, root-key limits and decentralization measures |
| Governance | Release/versioning process, license approval and evidence gates |
| Clients | Consistent publishing/reading flow and optional reader-controlled ranking interface |

Unused legacy schema definitions were removed. The current admission/acceptance, funding, retrieval and operations contracts remain. Optional ranking now permits inline-only candidates, aligning candidate shape with valid inline messages. Examples remain synthetic and tests remain scoped regression evidence; neither is a guarantee of real-world operation.

## Final review

The security, economics/contracts and compliance/decentralization subagents reviewed the consolidated set for dropped requirements, broken dependencies, stale references and contradictions. They compared the retained normative material and checked the remaining schema dependency graph.

Their findings were fixed:

- Removed unspaced references to deleted documents/profiles and corrected the owner of nonexpiring-credit rules.
- Made admitting-provider success depend on completed paid finalization: an already accepted ID cannot bypass incomplete replication on retry. Independent relay acceptance remains host-local.
- Replaced the inferred schema-name signature-domain rule with each artifact's explicitly specified label and exclusions.

All three reviewers confirmed closure in their targeted final rechecks. No unresolved finding remains from those checks; this is not certification that implementations are exploit-free.

## Verification

39 Python tests pass, including new checks for the exact document set, obsolete-reference absence, file links and section anchors, schema reference closure, removal of excluded contracts and inline-only ranking candidates. Independent Node/OpenSSL signature-vector checks and Git whitespace checks pass. Existing admission, encryption, economics and state-regression tests remain intact. These are scoped schema/crypto/reference-model tests, not production integration tests.

## Release limitations

Consolidation does not grant a license, deploy a service, certify legal compliance or establish profitability. Release still requires the explicit evidence and authorization gates in [governance](../docs/06-governance.md). Root compromise, provider trust and partial index/storage coverage remain disclosed limits.
