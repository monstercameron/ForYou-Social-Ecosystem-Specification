# Text-only and external-media adversarial review

Date: 2026-11-11. Nonnormative review record for the text-only revision; the owning docs and schemas define the requirements.

## Scope

Three adversarial reviewers examined the uncommitted revision across security, contracts/economics, and compliance/privacy/decentralization. ForYou retains text and structured protocol records. Users/apps configure external media hosting. Posts, replies, quotes and counterpoints accept at most 16 image/video URL references combined. Media availability and CDN services are outside ForYou's service contracts.

## Findings and fixes

- Browser/native media loading could bypass server-style fetch controls. Every embedded path now requires isolated credential-free networking, checked destinations and redirects; clients disable rendering where enforcement is unavailable. Nested resources, playlists, decoding and resource budgets are covered explicitly.
- Lazy loading could expose reading activity before consent. Media, avatars and prefetch now require a reader gesture or revocable exact-origin approval; new origins require approval before contact. Text-only reading remains available.
- Avatar rendering conflicted with the attachment-only rule. A single profile avatar is now an explicit separate exception with the same URL and privacy controls.
- URL shape checks left parser ambiguity. The protocol now defines offline restricted HTTPS semantics for authority, ports, IDNA A-labels, escapes and exact signed bytes, with actual-network-parser comparison and independent fetch-time destination checks.
- Non-post payloads could smuggle media fields past the 16-reference constraint. Remaining public payloads are closed; only the four text-bearing message types accept attachments. The limit counts signed top-level references, while every secondary fetch remains bounded and protected.
- Finalization retries lost their explicit single-worker rule. Restored one worker per message ID with aggregate work limits, durable retry progress and no additional debit.
- Paid but unfinalized text had no valid export representation. Added encrypted, owner-only prepared_admission evidence with original admission request and receipt bindings, restored strictly as unpublished text.
- The new encrypted draft format exposed a size conflict. A complete prepared-admission archive file has a bounded 2 MiB allowance, retaining original request/receipt/plaintext bounds. Public and private-sync transports keep their 1 MiB limits.
- The prior media-signature test used a signing domain absent from the actual protocol flow. Replaced it with real admission authorization, intent-ID, receipt and final-message mutation checks.

## Verification and recheck

All three reviewers confirmed closure of their respective findings and the follow-up export-size conflict. They reported no further material defect in their targeted rechecks. The contract reviewer independently ran the maximal prepared-export test.

44 Python tests pass, including restricted URL cases, non-post field rejection, actual media-reference proof binding, prepared-record ownership and an exact 1 MiB finalizable message encrypted/decrypted within the 2 MiB archive limit. Independent Node/OpenSSL signature-vector verification and Git whitespace checks pass.

These are specification, schema, cryptographic and reference-model checks. Browser isolation, DNS rebinding/redirect defenses, consent UI, decoder limits, durable concurrent services, delegated-admission integration and complete archive assembly still require implementation-level testing. Review is not a guarantee that implementations have no exploits.

## Compatibility

This is a pre-release profile revision. It replaces content_summary with inline text, removes media object/CID contracts and their offer/export fields, closes public payload extensions, and replaces attachment CID strings with typed external URL references. Updated fixtures are incompatible with the previous pre-release data shape; applications must retain old evidence as legacy data rather than rewriting signatures. Any newly published replacement follows the current admission path. The release/versioning gates in [governance](../docs/06-governance.md) still apply.
