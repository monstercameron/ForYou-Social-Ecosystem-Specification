# Security refinement review

This is a historical non-normative review record, not a certification or audit of a running implementation. Some findings predate the post-only versioning decision; current requirements are in the numbered documents and schemas.

Read-only adversarial reviewers identified and rechecked these areas:

- Public listing availability, explicit incomplete quota skips, cursor branch state, restriction handling and operator-controlled caches. Earlier control-record budgets were superseded by post-only versioning.
- Bounded delegation revocation, epoch freezing and rotation, signed-state freshness, anti-rollback recovery and the limits of provider attestations.
- Bounded service-auth challenges, one-use consumption and crash/recovery fencing.
- Renewal authorization, exact retries, retained evidence, purge fencing and export job staging limits.
- Notice and rights intake, anonymous recovery credentials, receipt verification, disclosure controls, historical form definitions and recovery checkpoints.
- Bilateral provider compensation, evidence exchange, dispute windows, accepted liabilities, settlement binding and bounded reserves.

The Python checks are synthetic schema, signature and reference-model tests; the Node check independently exercises selected cryptographic vectors. They do not prove concurrency, production security, worldwide legal compliance, solvency, censorship resistance or absence of exploits. A deployable system still requires interoperable implementations, integration and failure testing, independent security review, actual operating-cost evidence and deployment-specific legal assessment.
