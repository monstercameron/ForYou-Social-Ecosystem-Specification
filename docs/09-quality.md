# Provider quality evidence

## Scope and trust

A monitor is any independently chosen party that measures a provider's public service and signs a QualityReport. Anyone can monitor.

Two trust choices are separate:

- Clients choose which monitors and criteria to trust. They may use their own measurements, and can decline a provider's receipts under their local policy.
- The release-approved DistributionPolicy names the committee monitors whose reports feed the quarterly [distribution](./03-economics.md#distribution).

There is no mandatory ranking and no payment based on raw requests.

A valid report signature identifies the monitor's assertion. It does not prove that the monitor was honest, independent, well funded or able to observe every provider, reader or message.

Reports can compare only their explicitly stated provider, endpoint, period, sample, method, clocks, location and limits. Retrieval success is not proof of indefinite retention, replica independence, solvency or legal compliance. A monitor cannot prove any of the following merely by signing a result:

- a network partition;
- an outage;
- a missing record;
- the completeness of a provider's inventory;
- a globally correct timestamp.

A provider can choose what it serves or withholds; sample and source coverage remain visible. New reports and independent checks can change a client's local assessment without changing old message signatures.

## Signed report and evidence

QualityReport is the closed operations-schema object with `report_id,monitor_id,provider_id,period_start,period_end,created_at,methodology_digest,observations_digest,sample_seed,sample_seed_commitment,sample_frame_digest,sample_coverage,availability_attempts,availability_successes,retrieval_attempts,retrieval_passes,restore_attempts,restore_passes,latency_p50_ms,latency_p95_ms,latency_p99_ms,replica_operators,independent_controllers,sponsors,conflicts,monitor_signature`. Its field bounds are structural. The semantic checks below are mandatory for an interoperable report.

Use the common canonical UTF-8 JCS, `did:key`, strict Ed25519 and P rules from [protocol](./02-protocol.md#bytes-keys-and-signatures):

- Compute `report_id` as `fyqr2:` plus lowercase SHA256 hex of P("quality-report-id", the exact report excluding report_id and monitor_signature).
- Sign P("quality-report", the report excluding monitor_signature) with monitor_id.

A monitor MUST NOT sign for a provider key it does not control or imply its own signature is the provider's signature.

Period timestamps use the protocol's canonical UTC format and satisfy `period_start < period_end <= created_at`. The maximum period is 31 days. A report describes exactly one provider and period.

Monitors publish the exact methodology and raw observations alongside the report whenever lawful. Their SHA256 digests bind the exact bytes. The methodology is non-executable UTF-8 text, at most 1 MiB. It identifies:

- the endpoint and pinned provider key;
- the probe rate and observation locations. The exact probe times are committed by digest in advance and revealed with the observations, so a provider cannot serve well only when probed;
- the selection procedure and candidate-frame source;
- rate limits, timeout and retry treatment;
- clock uncertainty;
- failure classifications and exclusions;
- restore-test scope;
- ownership assessment;
- funding and conflicts.

Never put credentials, reader history, IP addresses or legally restricted case details into public evidence. The report describes sponsors and conflicts; a blank disclosure is not proof none exist.

QualityObservationSet is the closed operations-schema object `{provider_id,monitor_id,period_start,period_end,observations}`. Its exact UTF-8 JCS bytes are at most 4 MiB and contain at most 10,000 observations. Each observation identifies:

- kind;
- message_id, when applicable;
- started_at;
- duration_ms;
- outcome;
- `http_status` (null when no HTTP response);
- `within_limits` (the monitor's assertion).

Hash these exact bytes with SHA256 to obtain `observations_digest`.

A retrieval pass requires a non-null message ID; a concealed ID cannot independently establish a cryptographic pass. Provider, monitor and period MUST match the report. Every probe start lies in the half-open period, and duration is bounded by the schema.

Records, hashes and counts describe only legally publishable observations. Apply current disclosure controls before every publication and correction. If a restriction prevents publishing a truthful raw set, use unknown/incomplete coverage or withhold the report as necessary, rather than inventing observations or revealing restricted identifiers. Cached copies outside the monitor's control cannot be recalled.

`sample_coverage` describes only whether the stated bounded sampling plan was executed: complete, incomplete or unknown. Complete is the monitor's assertion about that plan. It is never proof of complete provider inventory or global network coverage.

Sampling works as follows:

- Verify canonical random `sample_seed` as 32 unpadded base64url bytes. Its commitment is lowercase SHA256 hex of P("quality-sample-seed", `{sample_seed}`).
- For reproducible tests the candidate frame MUST be a JCS array of at most 10,000 unique canonical message IDs sorted by ASCII byte order. Hash those exact JCS bytes with SHA256 as `sample_frame_digest`.
- The methodology MUST disclose the planned sample size n, where 0 <= n <= frame length, and exclusions.
- Compute each rank as the SHA256 bytes of P("quality-sample-rank", `{sample_seed,message_id}`).
- Select the first n IDs ordered by rank bytes, breaking ties by message ID ASCII byte order. Sampling is without replacement.

Publish the frame digest, selection method and seed commitment before observing outcomes where lawful. Provide the frame when lawful for recomputation. This fixed algorithm requires no execution of monitor-supplied code.

The seed and its timing have these limits:

- Independently unpredictable future randomness can reduce seed grinding if its source and timing are disclosed. Otherwise acknowledge that seed selection may be biased.
- Prefer an independently timestamped commitment or randomness source, but disclose its trust and failure limits.
- The publication and its timing are monitor assertions unless independently witnessed or timestamped. Even an authenticated timestamp does not prove unbiased frame selection or prevent advance seed grinding.
- Publishing both seed and commitment after sampling alone cannot prove the seed was not chosen after seeing results.

Source, missing coverage and selection bias remain visible. No compulsory global beacon or monitor registry is introduced.

## Retrieval and availability probes

Use only the provider's approved public GET routes.

A candidate frame used for a report that feeds distribution MUST be drawn from the settled messages whose receipt names the provider and has a `retain_until` that has not passed. Those messages are taken as held by the Lifetime Vault or, when the vault cannot be reached, as mirrored by the monitor from providers' `GET /v1/changes`. The frame spans the whole retained age range. The vault only holds finalized messages, so an unfinished admission cannot enter the frame, and the provider cannot choose the list.

For such a record:

- a 404, or a 410 `retention_expired`, is a failed retrieval;
- a 403 restriction is excluded from the denominators for at most 2% of the sample;
- restricted outcomes beyond that count as failed retrievals.

The report MUST state the restricted share.

A monitor may choose a bounded frame of public, lawfully testable message IDs, commit its method, choose a reproducible random subset and request `GET /v1/messages/{message_id}`. For a retrieval pass:

- receive the complete bounded canonical response;
- verify the returned ID equals the selected ID;
- recompute its intent ID;
- validate strict author/delegate signatures and receipt bindings;
- record the outcome.

Provider admission trust is a separate local policy. A provider signature alone does not establish payment, truth or completeness. A mismatch, invalid proof, timeout or unavailable response cannot be labeled a pass.

The monitor MUST make sufficient lawful response evidence available to reproduce successful cryptographic checks. Signed observations alone attest to results; they do not establish that a response was actually received. Do not fetch external media, hidden records, previews or private account data as part of this measurement.

Availability probes test the disclosed public listing route with valid requests inside published rate and work limits. Record every scheduled attempt and the actual bounded result.

- An in-limit 429 or 503 is a failed availability probe; do not silently discard it.
- A 429 caused by a probe that exceeded disclosed limits is reported separately as rate-limited, with the exclusion and reason visible.
- A lawful restriction, nondisclosing 404 or unknown authorization state is not proof of an outage, absent record or false report. Classify and disclose it separately where lawful, or do not publish the affected observation when disclosure is prohibited.

A monitor MUST NOT claim that excluding a legally inaccessible target increases proven global availability.

Use independent bounded retries and a documented deadline. Count each planned probe exactly once under that method. Record durations to complete the response using a monotonic local timer, not a remote timestamp. The recorded UTC time and duration are monitor assertions.

Latency percentiles are computed only over successful availability probes. Use nearest-rank indices `ceil(p*n)` for p=0.50, 0.95 and 0.99 on ascending integer milliseconds. When there are no eligible successful samples, all latency percentiles are null, never zero. Otherwise require p50 <= p95 <= p99.

Counting rules apply to each kind:

- Eligible observations are those with `within_limits` true and outcome `pass`, `fail`, `rate_limited` or `unavailable`.
- Attempts equal their count. Successes/passes equal the count with outcome `pass`.
- Restore attempts and passes follow the same rule.
- Outcomes `restricted` and `unknown`, and any out-of-limit observations, are excluded from these denominators and disclosed separately.

Outcomes are classified as follows:

- An HTTP 429 MUST be `rate_limited`.
- An HTTP 503 MUST be `unavailable`.
- A timeout has null status and MUST be `unavailable`.
- An HTTP 403 subject to legal restriction MUST be `restricted`.
- An ambiguous 404 MUST be `unknown`, except for a record in a distribution frame, where a 404 or a 410 is `fail`.
- Other unsuccessful HTTP statuses MUST NOT be `pass`.
- For availability and retrieval, `pass` requires HTTP 200 and the complete route-specific response to validate. Retrieval also requires all ID and signature checks above.
- A local restore can have null HTTP status, but `pass` requires verified scoped restore evidence.

Never classify an unchecked response as a pass. Verify all aggregates and percentiles against the complete available observation set. Reject a report whose recomputed values differ. If raw evidence cannot lawfully be shared, label aggregates unverified rather than externally recomputable. Keep separately classified restrictions, out-of-limit requests and unknown observations visible in the raw set and methodology.

A report's consumer needs the probe failure and timeout counts together with the percentiles. Percentiles are particularly unstable for p95 with fewer than 20 successes or p99 with fewer than 100 successes. No count of downloads or raw traffic creates a fee or payout entitlement.

Restore attempts measure the monitor's explicitly scoped recovery drill, not a new public endpoint. Explain whether the test used a locally held archive, a consenting operator, or an independent replica. Verify restored exact bytes, IDs and signatures where lawful. A signature or report by itself does not independently establish that a remote operator actually restored data.

`replica_operators` and `independent_controllers` are disclosed, evidence-backed claims about the scope observed:

- Both MUST be null when their values are unknown.
- Otherwise both are nonnegative integers, and the latter cannot exceed the former.
- Zero is a substantiated count, not unknown.

Different keys or URLs alone do not prove independent ownership or failure domains; the methodology explains the evidence and uncertainty.

## Interpretation and optional reference score

An application MAY display a simple reference score for comparison within a single explicitly comparable methodology.

The score is **unknown**, not zero or perfect, if any of these holds:

- sample_coverage is not complete;
- either availability_attempts or retrieval_attempts is below 20, or either denominator is zero.

Otherwise compute, using exact integers:

- `A = floor(10000 * availability_successes / availability_attempts)`;
- `R = floor(10000 * retrieval_passes / retrieval_attempts)`;
- `score = min(A, R)` basis points.

Because the score takes the minimum, a provider that answers listings but cannot return records scores low. The formula does not include latency, restore or replica diversity: display those raw metrics and the methodology separately. Users may choose different criteria or reject the score entirely. The score is not a measurement of worldwide availability.

The same formula gives the reference scores used for `quality_bp` in distribution, where a report with an unknown score gives a monitor no coverage. Report uncertainty, small samples, freshness and conflicting monitors rather than presenting a single number as a guarantee.

Default provider or monitor lists disclose their curators, sponsorship, ownership relationships, selection and update criteria. Clients MUST:

- make defaults visible and replaceable;
- support manually selected providers and monitors;
- avoid silently replacing user trust choices.

A monitor or provider cannot gain authority over message validity, content moderation or fees by publishing a score.

Self-monitoring and paid monitoring are allowed only with clear disclosure. Independent corroboration is advisable because collusion, shared infrastructure and Sybil identities can distort reports. Committee monitors are paid from fees by the rule in the release-approved [distribution policy](./03-economics.md#distribution). Other monitors fund their own work or disclose voluntary support. The protocol imposes no monitoring fee on readers or authors.

A monitor named in a DistributionPolicy MUST disclose any ownership or funding relationship with a provider it reports on. It MUST NOT report on a provider it controls.
