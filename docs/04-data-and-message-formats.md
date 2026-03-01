# Data and Message Formats

## Objective

Define the canonical protocol message envelope and typed payload schemas used by the network.

## Status

This document is a draft schema specification with a provisional launch baseline.

The keywords `MUST`, `SHOULD`, and `MAY` are to be interpreted as normative requirements for the launch baseline sections of this document. Other sections remain explanatory unless they are explicitly tied to launch behavior.

## Scope

This document covers:

- common message fields
- typed message variants
- serialization and signing concerns
- schema versioning rules

## Message Model

Every protocol message consists of:

- a base envelope
- a typed payload
- zero or more external references
- a signature over a canonical serialization

## Base Envelope

### Launch-Critical Envelope Fields

The following envelope fields are launch-critical and `MUST` be implemented for interoperable clients and nodes:

- `message_id`
- `author_id`
- `timestamp`
- `message_type`
- `version`
- `signature`

The following fields are launch-critical when applicable:

- `payment` for direct-payment fallback messages
- `submission_receipt` for immediately metered plan-funded portable public messages
- `submission_token` for asynchronously admitted lightweight public interactions
- `content_address` for externally stored primary content

### Required Fields

- `message_id`
  stable message identifier
- `author_id`
  canonical author identity reference
- `timestamp`
  message creation timestamp
- `message_type`
  declared type of payload
- `version`
  schema version identifier
- `signature`
  signature over the canonical message representation

### Conditionally Required Fields

- `payment`
  required for any direct-payment fallback message
- `submission_receipt`
  required for any portable public message that uses immediate per-message metering
- `submission_token`
  permitted for Tier 2 lightweight public interactions that use token-based asynchronous admission
- `content_address`
  required for any message whose primary content is stored externally

### Optional Fields

- `thread_id`
- `language`
- `keywords`
- `topic_tags`
- `media_kinds`
- `is_ad`
- `content_warning_flags`

### Validation Rules

- `message_id` `MUST` be unique.
- `author_id` `MUST` use the canonical identity format defined by the identity specification.
- `timestamp` `MUST` be a valid RFC 3339 UTC timestamp.
- `message_type` `MUST` be recognized by the receiving implementation or rejected as unsupported.
- `version` `MUST` be a positive integer.
- `signature` `MUST` verify against the canonical serialization and author identity.

## Payment Object

### Required Fields

- `chain`
- `transaction_id`
- `amount`

### Optional Fields

- `block_reference`
- `confirmation_status`
- `payment_class`
- `verified_by`

### Validation Rules

- Direct-payment fallback messages `MUST` include a `payment` object.
- Tier 1 plan-funded portable public messages `MUST` include a `submission_receipt`.
- Tier 2 plan-funded portable public messages `MUST` include either a `submission_receipt` or a `submission_token`.
- Messages that are neither direct-payment fallback messages nor plan-funded portable public messages `MAY` omit both.
- `chain` `MUST` be a supported payment network identifier.
- `transaction_id` `MUST` be parseable by the relevant bridge or payment verifier.

### Launch-Critical Payment Fields

The launch-critical payment fields are:

- `chain`
- `transaction_id`
- `amount`

`confirmation_status` and `verified_by` are strongly recommended at launch even if they are produced after initial client submission.

## Submission Receipt Object

This object is used when a portable public message is admitted against a pre-funded provider plan or allowance instead of a direct L1 payment reference.

### Required Fields

- `provider_id`
- `plan_id`
- `receipt_id`
- `message_id`
- `units_charged`
- `provider_signature`

### Optional Fields

- `period_start`
- `period_end`
- `tier`
- `remaining_units_hint`

### Validation Rules

- `provider_id` `MUST` use the canonical host or service identity format.
- `message_id` `MUST` match the enclosing message.
- `units_charged` `MUST` be a positive integer or decimal value according to provider plan rules.
- `provider_signature` `MUST` verify against `provider_id`.
- `receipt_id` `MUST NOT` be reused across distinct accepted messages.

### Launch-Critical Submission-Receipt Fields

The launch-critical submission-receipt fields are:

- `provider_id`
- `plan_id`
- `receipt_id`
- `message_id`
- `units_charged`
- `provider_signature`

## Submission Token Object

This object is used when a provider grants short-window or session-scoped admission for lightweight public interactions without requiring a new provider signature on every interaction.

### Required Fields

- `provider_id`
- `plan_id`
- `token_id`
- `author_id`
- `tier_scope`
- `units_limit`
- `valid_from`
- `valid_until`
- `provider_signature`

### Optional Fields

- `remaining_units_hint`
- `redeemer_scope`
- `device_group_id`

### Validation Rules

- `provider_id` `MUST` use the canonical host or service identity format.
- `author_id` `MUST` match the acting identity or an authorized delegated device group.
- `tier_scope` `MUST` identify the permitted interaction class.
- `tier_scope` `MUST NOT` be narrowed to one specific `target_message_id`, `target_author_id`, `target_topic`, or `target_thread_id`.
- `valid_until` `MUST` be later than `valid_from`.
- `provider_signature` `MUST` verify against `provider_id`.
- `token_id` `MUST NOT` be reused as if it were a per-message receipt identifier.

### Launch-Critical Submission-Token Fields

- `provider_id`
- `plan_id`
- `token_id`
- `author_id`
- `tier_scope`
- `units_limit`
- `valid_from`
- `valid_until`
- `provider_signature`

## Host Hint Object

This object is used in discovery flows, provider responses, and local availability maps.

### Required Fields

- `host_id`
- `endpoint`
- `last_seen`

### Optional Fields

- `jurisdiction`
- `policy_hint`
- `transport_capabilities`
- `confidence`

### Validation Rules

- `host_id` `MUST` identify one host instance or host service identity using the canonical host identity format.
- `endpoint` `MUST` be a parseable HTTPS base URL at launch.
- `last_seen` `MUST` be a valid RFC 3339 UTC timestamp.
- `confidence`, if present, `MUST` be a numeric advisory value and `MUST NOT` be treated as protocol truth.

### Launch-Critical Host-Hint Fields

The launch-critical host-hint fields are:

- `host_id`
- `endpoint`
- `last_seen`

Launch should use a single canonical endpoint string rather than a list of transports.

## Canonical Message Types

- `post`
- `reply`
- `quote`
- `counterpoint`
- `recommend`
- `follow_source`
- `follow_topic`
- `subscribe_thread`
- `withdraw`
- `private_state_update`
- `advertisement`
- `alias_registration`
- `poll`

Implementations `MAY` support additional message types, but unknown types `MUST NOT` be treated as valid known types.

## Launch Message-Type Decision

For launch:

- `reply` remains a first-class message type
- replies `MUST` include `reply_to`
- replies `SHOULD` include `thread_id` when a thread context exists
- `quote`, `counterpoint`, `recommend`, `follow_source`, `follow_topic`, and `subscribe_thread` should be treated as portable public interaction types
- `withdraw` should be treated as a tombstone-producing target-state update rather than a cascading deletion primitive
- `private_state_update` should be treated as encrypted portable user-state sync rather than public social context
- `advertisement` remains a defined extension message type, but it `MUST NOT` be required for launch interoperability
- private curation interactions such as mute, hide, block, bookmark, trust source, boost, downrank, private tags, and private notes may be carried through `private_state_update` without becoming public discovery metadata

Content-type-specific target references such as `reply_to`, `target_message_id`, `target_author_id`, `target_topic`, and `target_thread_id` should live in the typed payload rather than the generic message envelope.

## Interaction State Classes

At launch, canonical message types fall into these state classes:

- public portable content and interaction messages:
  `post`, `reply`, `quote`, `counterpoint`, and `withdraw`
- lightweight public interaction messages:
  `recommend`, `follow_source`, `follow_topic`, and `subscribe_thread`
- private portable sync messages:
  `private_state_update`
- device-local-only actions:
  non-canonical transient client-local behavior outside protocol message requirements
- Extension types:
  `advertisement`, `alias_registration`, and `poll` may be supported, but they are not required for launch interoperability

Validation and operator behavior should reflect these different risk profiles.

- Tier 1 messages `MUST` satisfy the submission-funding rules for their action class.
- Tier 1 portable public messages `MUST` include either a valid `submission_receipt` or a valid direct-payment `payment` object.
- Tier 2 portable public messages `MUST` include one of:
  a valid `submission_receipt`, a valid `submission_token`, or a valid direct-payment `payment` object.
- Tier 2 messages `MUST` be signed and portable, but they `MUST NOT` require their own base-layer BTC or ETH payment reference in the normal launch path.
- Tier 2 messages `SHOULD` support optimistic local acceptance and delayed provider reconciliation rather than blocking the user on a synchronous provider round trip for each tap.
- Providers accepting Tier 2 messages `MUST` apply at least one abuse-control mechanism such as funded allowance debits, rate limiting, bounded quota windows, or equivalent submission controls.
- `private_state_update` messages `MUST` be encrypted, `MUST NOT` be exposed through public candidate metadata, and `MUST NOT` be treated as shared social context.
- `private_state_update` messages `MUST NOT` require a `submission_receipt` or direct-payment `payment` object in the normal launch path.
- device-local-only actions `MUST NOT` be treated as canonical network messages at launch.

This keeps reply validation explicit and avoids overloading generic post semantics during initial implementation.

## Payload Schemas

### Post

Required payload fields:

- `content_format`
- `content_summary`

Optional payload fields:

- `links`
- `attachments`
- `metadata`

Expected envelope support:

- `content_address` `SHOULD` be present when the full body is stored externally
- `is_ad` `MUST` be false or omitted

Launch-critical post support:

- `content_format`
- `content_summary`

### Reply

Required payload fields:

- all required post fields
- `reply_to`

Expected envelope support:

- `thread_id` `SHOULD` be present

Launch-critical reply support:

- all launch-critical post fields
- `reply_to`

### Advertisement

Required payload fields:

- all required post fields
- `sponsor_reference`

Optional payload fields:

- `campaign`
- `targeting_scope`
- `payout_rules`

Expected envelope support:

- `is_ad` `MUST` be true
- either `payment` or `submission_receipt` `MUST` be present

Launch-critical advertisement support:

- all launch-critical post fields
- `sponsor_reference`
- `is_ad`
- submission funding evidence as defined by the applicable advertisement rules

Launch note:

- `advertisement` is an extension type and is not part of the minimum interoperable launch surface.

### Quote

Required payload fields:

- all required post fields
- `target_message_id`

Expected envelope support:

- `thread_id` `SHOULD` be present when the quote participates in a thread

Launch-critical quote support:

- all launch-critical post fields
- `target_message_id`

### Counterpoint

Required payload fields:

- all required post fields
- `target_message_id`

Expected envelope support:

- `thread_id` `SHOULD` be present when the counterpoint participates in a thread

Launch-critical counterpoint support:

- all launch-critical post fields
- `target_message_id`

### Recommend

Required payload fields:

- `target_message_id`

Optional payload fields:

- `context`

Expected envelope support:

- `content_address` `MAY` be omitted when the recommendation is fully inline

Launch-critical recommend support:

- `target_message_id`

Validation notes:

- `recommend` is a lightweight public interaction.
- A `recommend` message `MUST` be signed by the acting identity.
- A `recommend` message `MUST NOT` be treated as high-trust ranking truth solely because many such messages exist.

### Follow Source

Required payload fields:

- `target_author_id`

Expected envelope support:

- `content_address` `MAY` be omitted

Launch-critical follow-source support:

- `target_author_id`

Validation notes:

- `follow_source` is a lightweight public interaction.
- A `follow_source` message `MUST` be signed by the acting identity.

### Follow Topic

Required payload fields:

- `target_topic`

Expected envelope support:

- `content_address` `MAY` be omitted

Launch-critical follow-topic support:

- `target_topic`

Validation notes:

- `follow_topic` is a lightweight public interaction.
- A `follow_topic` message `MUST` be signed by the acting identity.

### Subscribe Thread

Required payload fields:

- `target_thread_id`

Expected envelope support:

- `content_address` `MAY` be omitted

Launch-critical subscribe-thread support:

- `target_thread_id`

Validation notes:

- `subscribe_thread` is a lightweight public interaction.
- A `subscribe_thread` message `MUST` be signed by the acting identity.

### Withdraw

Required payload fields:

- `target_message_id`

Optional payload fields:

- `reason_code`
- `replacement_reference`

Expected envelope support:

- `content_address` `MAY` be omitted

Launch-critical withdraw support:

- `target_message_id`

Validation notes:

- `withdraw` is a public target-state update for the author's own prior message.
- A `withdraw` message `MUST` be signed by the same identity that authored the target message or by an authorized successor identity under the identity rules.
- A `withdraw` message `MUST NOT` imply cascading deletion of replies, quotes, counterpoints, or recommendations that reference the withdrawn target.
- Clients and providers `SHOULD` resolve the target to a tombstone or unavailable state rather than a broken null reference.

### Private State Update

Required payload fields:

- `state_kind`
- `encrypted_state`
- `encryption_scope`
- `state_sequence`

Optional payload fields:

- `device_group_id`
- `supersedes`
- `state_summary`
- `compaction_kind`

Expected envelope support:

- `content_address` `MAY` be omitted when the encrypted state is inline

Launch-critical private-state-update support:

- `state_kind`
- `encrypted_state`
- `encryption_scope`
- `state_sequence`

Validation notes:

- `private_state_update` is encrypted portable user state, not public social content.
- A `private_state_update` message `MUST` be signed by the acting identity.
- A `private_state_update` message `MUST` be encrypted for the user's own devices, delegates, or chosen sync service.
- A `private_state_update` message `MUST NOT` appear in public candidate discovery surfaces.
- Providers `MAY` store or relay the encrypted object without interpreting the private contents.
- `private_state_update` `SHOULD` carry compact snapshots or bounded deltas rather than one network object per trivial UI toggle.
- `supersedes` and `state_sequence` should be used to compact old private state rather than create unbounded event logs.
- Providers `MAY` garbage-collect superseded private-state objects after the user's sync policy or retention policy permits it.

### Alias Registration

Required payload fields:

- `alias`

Optional payload fields:

- `display_name`
- `bio`
- `avatar_reference`
- `profile_links`

Expected envelope support:

- `content_address` `MAY` be omitted when the full profile is inline

Launch-critical alias-registration support:

- `alias`

### Poll

Required payload fields:

- `prompt`
- `options`

Optional payload fields:

- `duration_seconds`
- `closing_time`

Validation rules:

- `options` `MUST` contain at least two entries

Launch-critical poll support:

- `prompt`
- `options`

## Canonical Serialization

- Senders `MUST` sign a deterministic serialization of the message envelope and payload.
- Implementations `MUST` use canonical JSON encoding for launch.
- Signature verification `MUST` exclude transport-specific wrapper data.

## Launch Canonical JSON Rules

For launch, canonical JSON serialization uses these rules:

- the signed object `MUST` include the envelope and payload fields required for message validation
- the `signature` field itself `MUST NOT` be included in the signed byte sequence
- object keys `MUST` be serialized in lexicographic order
- UTF-8 `MUST` be used as the byte encoding
- insignificant whitespace `MUST NOT` be included
- numbers `SHOULD` be serialized in a stable minimal JSON form
- arrays `MUST` preserve application-defined order
- `null` fields `SHOULD` be omitted unless semantically required by the schema

## Signed Object Shape

The launch signed object is:

- the full message envelope except `signature`
- the typed payload object

Transport wrappers, HTTP metadata, provider chunk metadata, and local ranking features `MUST NOT` be part of the signed object.

## Signature Process

The baseline signature process is:

1. construct the envelope without `signature`
2. attach the typed payload
3. serialize the combined object using canonical JSON rules
4. sign the resulting UTF-8 byte sequence with the author's key material
5. encode the resulting signature in the `signature` field

## Example Envelope

```json
{
  "message_id": "msg-123",
  "author_id": "did:key:z6MkrJVnaZkeuWiRiwXQDq6rYmQXW1Lg31xHn3pV3hokW2Pp",
  "timestamp": "2026-03-01T14:00:00Z",
  "message_type": "post",
  "version": 1,
  "content_address": "ipfs://bafyexample",
  "language": "en",
  "keywords": ["distributed-systems", "indexing"],
  "signature": "base64-signature"
}
```

## Example Post Payload

```json
{
  "content_format": "markdown",
  "content_summary": "Short preview or summary text.",
  "links": ["https://example.com"],
  "attachments": [],
  "metadata": {
    "topic_tags": ["distributed-systems"],
    "media_kinds": ["text"]
  }
}
```

## End-to-End Publish Example

Example launch message envelope:

```json
{
  "message_id": "msg-123",
  "author_id": "did:key:z6MkrJVnaZkeuWiRiwXQDq6rYmQXW1Lg31xHn3pV3hokW2Pp",
  "timestamp": "2026-03-01T14:00:00Z",
  "message_type": "post",
  "version": 1,
  "content_address": "ipfs://bafyexample",
  "language": "en",
  "keywords": ["distributed-systems", "indexing"],
  "payment": {
    "chain": "bitcoin",
    "transaction_id": "tx-123",
    "amount": "0.0001",
    "payment_class": "standard_post"
  },
  "signature": "base64-signature"
}
```

Direct-payment fallback note:

- this example shows the fallback path
- the normal launch path should prefer `submission_receipt` on top of a previously funded plan

Example launch payload:

```json
{
  "content_format": "markdown",
  "content_summary": "Short preview or summary text.",
  "links": ["https://example.com"],
  "attachments": [],
  "metadata": {
    "topic_tags": ["distributed-systems"],
    "media_kinds": ["text"]
  }
}
```

Example signed object:

```json
{
  "author_id": "did:key:z6MkrJVnaZkeuWiRiwXQDq6rYmQXW1Lg31xHn3pV3hokW2Pp",
  "content_address": "ipfs://bafyexample",
  "keywords": ["distributed-systems", "indexing"],
  "language": "en",
  "message_id": "msg-123",
  "message_type": "post",
  "payment": {
    "amount": "0.0001",
    "chain": "bitcoin",
    "payment_class": "standard_post",
    "transaction_id": "tx-123"
  },
  "payload": {
    "attachments": [],
    "content_format": "markdown",
    "content_summary": "Short preview or summary text.",
    "links": ["https://example.com"],
    "metadata": {
      "media_kinds": ["text"],
      "topic_tags": ["distributed-systems"]
    }
  },
  "timestamp": "2026-03-01T14:00:00Z",
  "version": 1
}
```

## Launch Interaction Examples

### Reply Example

Envelope:

```json
{
  "message_id": "msg-reply-001",
  "author_id": "did:key:z6Mkf8x8P5gL6N8sYZZs1xP7vC18JNpDutLCRa14Qdqgttxy",
  "timestamp": "2026-03-01T14:05:00Z",
  "message_type": "reply",
  "version": 1,
  "content_address": "ipfs://bafyreplyexample",
  "submission_receipt": {
    "provider_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
    "plan_id": "annual-heavy-2026",
    "receipt_id": "receipt-reply-001",
    "message_id": "msg-reply-001",
    "units_charged": 1,
    "provider_signature": "base64-provider-signature"
  },
  "thread_id": "thread-88",
  "signature": "base64-signature"
}
```

Payload:

```json
{
  "content_format": "markdown",
  "content_summary": "A direct reply.",
  "reply_to": "msg-123"
}
```

### Quote Example

Envelope:

```json
{
  "message_id": "msg-quote-001",
  "author_id": "did:key:z6MkpTHR8V4QjzvY4xXHzkwmo7aX6ixkmKuuNHYsYkdivgLP",
  "timestamp": "2026-03-01T14:07:00Z",
  "message_type": "quote",
  "version": 1,
  "content_address": "ipfs://bafyquoteexample",
  "submission_receipt": {
    "provider_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
    "plan_id": "annual-heavy-2026",
    "receipt_id": "receipt-quote-001",
    "message_id": "msg-quote-001",
    "units_charged": 1,
    "provider_signature": "base64-provider-signature"
  },
  "thread_id": "thread-88",
  "signature": "base64-signature"
}
```

Payload:

```json
{
  "content_format": "markdown",
  "content_summary": "Quoting this because it matters.",
  "target_message_id": "msg-123"
}
```

### Recommend Example

Envelope:

```json
{
  "message_id": "msg-recommend-001",
  "author_id": "did:key:z6MkrJVnaZkeuWiRiwXQDq6rYmQXW1Lg31xHn3pV3hokW2Pp",
  "timestamp": "2026-03-01T14:10:00Z",
  "message_type": "recommend",
  "version": 1,
  "submission_receipt": {
    "provider_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
    "plan_id": "annual-heavy-2026",
    "receipt_id": "receipt-recommend-001",
    "message_id": "msg-recommend-001",
    "units_charged": 0.1,
    "provider_signature": "base64-provider-signature"
  },
  "signature": "base64-signature"
}
```

Payload:

```json
{
  "target_message_id": "msg-123",
  "context": "Useful introduction to the topic."
}
```

### Follow Source Example

Envelope:

```json
{
  "message_id": "msg-follow-source-001",
  "author_id": "did:key:z6MkpTHR8V4QjzvY4xXHzkwmo7aX6ixkmKuuNHYsYkdivgLP",
  "timestamp": "2026-03-01T14:12:00Z",
  "message_type": "follow_source",
  "version": 1,
  "submission_receipt": {
    "provider_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
    "plan_id": "annual-heavy-2026",
    "receipt_id": "receipt-follow-source-001",
    "message_id": "msg-follow-source-001",
    "units_charged": 0.1,
    "provider_signature": "base64-provider-signature"
  },
  "signature": "base64-signature"
}
```

Payload:

```json
{
  "target_author_id": "did:key:z6MkrJVnaZkeuWiRiwXQDq6rYmQXW1Lg31xHn3pV3hokW2Pp"
}
```

### Follow Topic Example

Envelope:

```json
{
  "message_id": "msg-follow-topic-001",
  "author_id": "did:key:z6Mkf8x8P5gL6N8sYZZs1xP7vC18JNpDutLCRa14Qdqgttxy",
  "timestamp": "2026-03-01T14:14:00Z",
  "message_type": "follow_topic",
  "version": 1,
  "submission_receipt": {
    "provider_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
    "plan_id": "annual-heavy-2026",
    "receipt_id": "receipt-follow-topic-001",
    "message_id": "msg-follow-topic-001",
    "units_charged": 0.1,
    "provider_signature": "base64-provider-signature"
  },
  "signature": "base64-signature"
}
```

Payload:

```json
{
  "target_topic": "distributed-systems"
}
```

## Relationship To Ranking Metadata

- The base envelope `SHOULD` expose the minimum fields defined in the metadata requirements document.
- Ranking systems `MUST NOT` treat private local features as part of the canonical message schema.

## Interaction Design Rule

Public interaction events should be signed, portable, and independently verifiable.

Derived counts such as recommendations, replies, quotes, counterpoints, or thread activity should be treated as computed metadata rather than canonical protocol truth.

Tier 2 interaction volume should be treated as low-trust by default unless a client or provider applies stronger local weighting, graph-quality rules, or provider-specific trust controls.

Target references should remain stable even when the referenced object is withdrawn, unavailable, blocked, or locally unserved. Clients and providers should resolve that target state explicitly rather than leaving orphaned references unexplained.

## Related Documents

- `12-ranking-profile-and-model-interface.md`
- `14-protocol-metadata-requirements.md`
- `16-identity-and-source-references.md`
- `17-index-provider-and-candidate-chunk-api.md`

## Open Decisions

- Whether the advertisement extension should be standardized further after the core launch surface is stable
