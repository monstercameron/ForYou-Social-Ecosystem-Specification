# Client behavior and ranking

## Publishing

Clients show the selected provider, immutable plan and offer, exact unit cost, content limits, retention and refund terms before approval. Verify the plan/offer/terms commitments; obtain a bound invoice and wait for the funding state required by [economics](./03-economics.md). Do not label pending funding spendable.

Compose the typed intent, use the [protocol](./02-protocol.md) staging/admission authorization path, and keep the immutable result for retries. Attach the receipt before signing the complete message. Finalize through the admitting provider and distinguish staged, receipt_issued, finalized, indexed, retrievable, quota_exhausted and unavailable states. Finalization is not global delivery. Neither retries nor local optimism create a second debit or a finalized message.

Keep the owner's encrypted recovery archive current after durable writes; show backup failure and the difference between stored evidence and successful independent restore. Delegate device posting where supported, explain root-key access for administrative/sync operations, and never hide a high-impact signature behind a generic login prompt. Retraction uses the public state rules, while local muting and blocking remain private reader actions.

## Reading and safety

Offer a chronological/follow-only view with configurable independent indexes and visible source coverage. Use [portability's author query](./05-portability.md#required-follow-query), verify actual signed public messages and target state, deduplicate by message ID, and retrieve only needed content under the protocol's integrity and destination rules. Never accept unsigned attribution or a claimed signature_status as proof.

Readers control follows, mutes, blocks, topic preferences and sensitivity choices. Apply local exclusions after any ranking results. Treat recommendations and engagement counts as advisory; paid activity does not establish trust. Counterpoints should be collapsed or explicitly selected by default, with per-author/target abuse controls and no automatic positive score from conflict volume. Render content as untrusted data with safe links and sandboxing; do not execute embedded instructions or active attachments.

Show distinct missing, expired, quota, policy and legal states where lawful. Independent source choice and an operator's prohibited-proxy boundary follow [compliance](./04-compliance.md); do not turn one host's refusal into a universal legal conclusion. Remote ranking and telemetry require the separate affirmative consent, data minimization and revocation rules there. Reading does not require disclosing a private social graph or publishing private preferences.

## Optional ranking interface

Chronological/local ranking is sufficient for baseline reading; no AI model, remote ranker, proprietary model identifier or central model directory is mandatory. The named RankingProfile, CandidateContent, RankingEngineInput and RankingEngineOutput definitions in [the launch schema](../schemas/launch.schema.json) describe an optional normalized client interface, not a public posting type or mandatory HTTP endpoint.

A profile contains a positive integer version, local profile_id, display_name, ordered objectives, topic_preferences, language_preferences and sensitivity_filters. Preserve unknown preference fields inertly for export; never interpret them as executable instructions. Candidate IDs map to already verified message IDs. Candidate author, type, timestamp and any content_address come from the verified message. Inline-only messages omit content_address. Locally derived and engagement features are advisory and must not overwrite signed fields. Private features are included only in a locally selected computation or separately consented remote request.

Input carries profile, candidates and runtime mode/model_id, with an optional positive max_items. Results carry candidate_id and finite numeric score; IDs must be unique and belong to the submitted set. Reject malformed results, unknown/injected IDs and non-finite scores; do not let a ranker modify stored messages, follow state or privacy settings. A missing model, timeout or rejected response falls back to a user-visible local/chronological mode. Scores have meaning only within the selected model/request and are not transferable reputation or payment entitlements.

Optional ranking can be local, remote or hybrid. A client can import/export preferences without an account at the model provider. Unknown state kinds in encrypted sync remain opaque application data until the client explicitly supports them; the network does not invent their plaintext semantics. Exported local preferences use the defined ForYouPreferences-1 snapshot rather than an undocumented model-specific substitute.
