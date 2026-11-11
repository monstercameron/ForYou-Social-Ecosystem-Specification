# Governance, consistency and pilot gates

## Release authority and versioning

The document ownership map in [the documentation index](./README.md) defines one specification set. Each topic has one owning document; cross-references add detail, not override precedence. The JSON Schemas define structural constraints and the owning prose defines semantic predicates. Both must be satisfied. Examples and reviews are nonnormative. A contradiction blocks a conformance claim until corrected; do not select whichever requirement is convenient.

Before any public deployment, publish a frozen release digest of these documents and both schema libraries. Existing pre-release fixtures are not a compatibility promise. After freezing, incompatible field/signing changes require a major version and migration plan; do not redefine version1 in place. Every accepted edit updates affected schemas, fixtures, cross-references and migration notes together. No automated production activation from changes on the main branch.

## Governance and license

Proposals have public IDs, motivation, threat analysis, economic/privacy impact, interoperability tests and review history. Normal review lasts at least 30 days; acceptance requires two independent implementation reviews and public maintainer rationale. Maintainers disclose conflicts and recuse from decisions on their own commercial exceptions. Record dissent, alternatives and compatibility consequences. Maintainer succession uses a published nomination/review process, with multiple independently controlled release-signing keys and documented key revocation. Decisions coordinate reference releases; operators retain adoption choice and may fork under the applicable license.

Emergency security advisories identify affected versions and mitigations and expire or receive public review within seven days. They cannot remotely impose a network-wide content ban, move funds, seize accounts or change ranking. Maintainers publish signed advisories; clients/operators explicitly choose deployment policy. Security reporting has a private contact, acknowledgment target of three business days, coordinated disclosure, severity triage and a transparently funded maintenance budget. Budget promises require actual funding.

The repository currently lacks an established license grant. Release is blocked until actual rights holders approve and publish licenses covering the specification, code/tests and contributions, with contribution provenance and a license-compatible fork/implementation policy. Do not fabricate ownership, silently assign contributors' rights or label unlicensed work open source. This is a human authorization gate, not a protocol design omission that an editor can resolve by assertion. No governance token or compulsory fee is needed to fund maintenance; disclose voluntary sponsorship and conflicts.

## Bounded pilot

Start in explicitly selected markets with named accountable operators, completed 04 assessments and scoped audiences/features. No claim of worldwide compliance. Before taking money, execute the purchased terms, privacy notices, service-offer and refund paths, assess payment/consumer obligations, and test failure recovery. A legal reviewer must evaluate actual deployment; a schema checkbox is insufficient. Do not launch paid services while material role/funding classification is unresolved.

The minimum pilot has two independently controlled funded providers, two independent client implementations, separately controlled discovery sources, and demonstrated replica independence. These are requirements for the project's public pilot claim, not barriers to anyone privately implementing the protocol. Test users can decline telemetry; publish aggregate methodology and confidence, not private identities or social graphs.

| Gate | Required evidence |
| --- | --- |
| Protocol | Cross-client publish/read/interactions; actual signatures and content verified; malformed-input and adversarial concurrency tests; two implementations, not just two crypto libraries |
| Exit | Successful restore and new publication with old provider and preferred directory offline; no original-provider approval, lost follows or secret-key export |
| Recovery | Root backup restore, delegate revocation and lost-device drills; no claim of compromise recovery under unchanged did:key |
| Storage | Independent replica acknowledgments and random complete restores; expired/legally removed objects handled without forbidden repair |
| Economics | Measured costs/revenue by role, reserve reconciliation, stress scenarios and refund/closure exercise; distinguish subsidized pilot from [the economics specification's](./03-economics.md) self-sustaining gate |
| Compliance | Role/market legal assessment, exercised notices/appeals/deletion/holds/age processes and incident response; no universal certification |
| User value | Pre-registered audience/use case, onboarding completion, D7/D30 retention, paid conversion, churn, willingness to pay, harassment response and accessibility observations |
| Independence | Provider/directory/index outage exercise, default replacement, ownership concentration disclosure, no mandatory project service |
| Release rights | Approved licenses and contributor provenance, reproducible builds, versioned conformance results and signed release |

Define product success thresholds before recruitment with an honest sample-size plan; do not select them after observing results or count bots/sponsored users as organic paid conversion. Stop expansion if unit economics, safety response or recovery fail. Publish the failure and remediation before increasing exposure. Audit concrete implementations and future financial contracts independently; completing this document does not establish a secure or profitable operating network.
