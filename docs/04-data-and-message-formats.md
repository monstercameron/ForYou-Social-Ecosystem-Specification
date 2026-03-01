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
- `signer_id`
- `delegation`
- `timestamp`
- `message_type`
- `version`
- `signature`

The following fields are launch-critical when applicable:

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

- `submission_receipt`
  required for any portable public message that uses immediate per-message metering
- `submission_token`
  permitted for Tier 2 lightweight public interactions that use token-based asynchronous admission
- `signer_id`
  required when the signing key is not the same as `author_id`
- `delegation`
  required when `signer_id` is present and differs from `author_id`
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
- `version.major` `MUST` be a positive integer.
- `version.minor` `MUST` be a non-negative integer.
- `signature` `MUST` verify against the canonical serialization and the declared signing identity:
  `signer_id` if present, otherwise `author_id`.
- If `signer_id` is present and differs from `author_id`, `delegation` `MUST` be present and `MUST` verify as an authorization from `author_id` to `signer_id`.
- If `content_address` is present, it `MUST` use the launch content-address scheme:
  `ipfs://<cidv1>` with CIDv1 base32 encoding.

## Payment Object

### Required Fields

- `chain`
- `funding_reference`
- `amount`

### Optional Fields

- `block_reference`
- `payment_class`
- `acceptance_state`
- `verifier_id`

### Validation Rules

- The interoperable launch baseline does not require per-message direct BTC/ETH payment references.
- Tier 1 plan-funded portable public messages `MUST` include a `submission_receipt`.
- Tier 2 plan-funded portable public messages `MUST` include either a `submission_receipt` or a `submission_token`.
- Messages that are not Tier 1 or Tier 2 portable public messages `MAY` omit payment-related objects unless a later extension standardizes them.
- `chain` `MUST` be a supported payment network identifier.
- `funding_reference` `MUST` be parseable by the relevant verifier for the declared chain.
- `acceptance_state`, if present, `MUST` be one of:
  `provisional`, `verified`, or `rejected`.
- `verifier_id`, if present, `MUST` be a canonical host or service identity reference.

### Launch-Critical Payment Fields

The launch-critical payment fields are:

- `chain`
- `funding_reference`
- `amount`

`acceptance_state` and `verifier_id` are strongly recommended at launch even if they are produced after initial client submission.

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
- `audit_log_root`
- `audit_proof_ref`

### Validation Rules

- `provider_id` `MUST` use the canonical host or service identity format.
- `message_id` `MUST` match the enclosing message.
- `units_charged` `MUST` be a positive integer or decimal value according to provider plan rules.
- `provider_signature` `MUST` verify against `provider_id`.
- `receipt_id` `MUST NOT` be reused across distinct accepted messages.
- `audit_log_root`, if present, `SHOULD` be a stable provider-published log root hash for receipt auditability.
- `audit_proof_ref`, if present, `SHOULD` be a URL or content address that can be used to fetch an inclusion proof for `receipt_id`.

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
- `audit_log_root`
- `audit_proof_ref`

### Validation Rules

- `provider_id` `MUST` use the canonical host or service identity format.
- `author_id` `MUST` match the acting identity or an authorized delegated device group.
- `tier_scope` `MUST` identify the permitted interaction class.
- `tier_scope` `MUST NOT` be narrowed to one specific `target_message_id`, `target_author_id`, `target_topic`, or `target_thread_id`.
- `valid_until` `MUST` be later than `valid_from`.
- `provider_signature` `MUST` verify against `provider_id`.
- `token_id` `MUST NOT` be reused as if it were a per-message receipt identifier.
- `audit_log_root`, if present, `SHOULD` be a stable provider-published log root hash for token auditability.
- `audit_proof_ref`, if present, `SHOULD` be a URL or content address that can be used to fetch an inclusion proof for `token_id`.

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

## Delegation Object

This object is used when a message is signed by a `signer_id` that is different from the stable `author_id`.

### Required Fields

- `author_id`
- `signer_id`
- `delegation_id`
- `valid_from`
- `valid_until`
- `delegation_signature`

### Optional Fields

- `scope`

### Validation Rules

- `author_id` and `signer_id` `MUST` use canonical identity references.
- `valid_until` `MUST` be later than `valid_from`.
- `delegation_signature` `MUST` verify against `author_id`.
- If `scope` is present, the receiving implementation `MUST` enforce it.
- Delegations `SHOULD` be short-lived.

### Launch-Critical Delegation Fields

- `author_id`
- `signer_id`
- `delegation_id`
- `valid_from`
- `valid_until`
- `delegation_signature`

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
- replies `MUST` include `thread_id`
- `quote`, `counterpoint`, `recommend`, `follow_source`, `follow_topic`, and `subscribe_thread` should be treated as portable public interaction types
- `withdraw` should be treated as a tombstone-producing target-state update rather than a cascading deletion primitive
- `private_state_update` should be treated as encrypted portable user-state sync rather than public social context
- `alias_registration` should be treated as a baseline profile and handle message so users can identify each other without comparing raw key strings
- `advertisement` remains a defined extension message type, but it `MUST NOT` be required for launch interoperability
- private curation interactions such as mute, hide, block, bookmark, trust source, boost, downrank, private tags, and private notes may be carried through `private_state_update` without becoming public discovery metadata

Content-type-specific target references such as `reply_to`, `target_message_id`, `target_author_id`, `target_topic`, and `target_thread_id` should live in the typed payload rather than the generic message envelope.

## Interaction State Classes

At launch, canonical message types fall into these state classes:

- public portable content and interaction messages:
  `post`, `reply`, `quote`, `counterpoint`, and `withdraw`
- lightweight public interaction messages:
  `recommend`, `follow_source`, `follow_topic`, and `subscribe_thread`
- public profile and handle messages:
  `alias_registration`
- private portable sync messages:
  `private_state_update`
- device-local-only actions:
  non-canonical transient client-local behavior outside protocol message requirements
- Extension types:
  `advertisement` and `poll` may be supported, but they are not required for launch interoperability

Validation and operator behavior should reflect these different risk profiles.

- Tier 1 messages `MUST` satisfy the submission-funding rules for their action class.
- Tier 1 portable public messages `MUST` include a valid `submission_receipt`.
- Tier 2 portable public messages `MUST` include a valid `submission_receipt` or a valid `submission_token`.
- Tier 2 messages `MUST` be signed and portable, but they `MUST NOT` require their own base-layer BTC or ETH payment reference in the launch baseline.
- Tier 2 messages `SHOULD` support optimistic local acceptance and delayed provider reconciliation rather than blocking the user on a synchronous provider round trip for each tap.
- Providers accepting Tier 2 messages `MUST` apply at least one abuse-control mechanism such as funded allowance debits, rate limiting, bounded quota windows, or equivalent submission controls.
- `alias_registration` messages `MUST` be signed and `MUST` include Tier 2 admission evidence (`submission_receipt` or `submission_token`).
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

- `thread_id` `MUST` be present and should equal the root message identifier for the thread

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
- `target_topic` `MUST` be a canonical topic key:
  lowercase ASCII, digits, and hyphens only, with no spaces.
- Topic keys are lexical identifiers, not a guaranteed universal ontology.
- Clients and providers `SHOULD` treat topic follows as discovery and routing hints rather than as global semantic truth.

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
- `target_thread_id` should be the `thread_id` value used by replies in the same thread.

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
- `encryption_scheme`
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
- `encryption_scheme`
- `encryption_scope`
- `state_sequence`

Validation notes:

- `private_state_update` is encrypted portable user state, not public social content.
- A `private_state_update` message `MUST` be signed by the acting identity.
- A `private_state_update` message `MUST` be encrypted for the user's own devices, delegates, or chosen sync service.
- `encryption_scheme` `MUST` be one of the launch-supported schemes declared by the client.
- Launch interoperability `MUST` support:
  `x25519-xchacha20poly1305`.
- A `private_state_update` message `MUST NOT` appear in public candidate discovery surfaces.
- Providers `MAY` store or relay the encrypted object without interpreting the private contents.
- `private_state_update` `SHOULD` carry compact snapshots or bounded deltas rather than one network object per trivial UI toggle.
- `supersedes` and `state_sequence` should be used to compact old private state rather than create unbounded event logs.
- Providers `MAY` garbage-collect superseded private-state objects after the user's sync policy or retention policy permits it.

#### Launch Baseline Private-State Encryption

For launch, `private_state_update` defines encrypted portable state that can sync across the user's own devices without publishing their private preferences or moderation choices as public metadata.

Launch baseline values:

- `encryption_scope` `MUST` be `device_group`.
- `device_group_id` `MUST` be present when `encryption_scope` is `device_group`.
- `device_group_id` `SHOULD` be a random base64url identifier generated by the client when the user enables sync.

Launch baseline `encrypted_state` shape:

- `encrypted_state` `MUST` be a JSON object with:
  `v`, `nonce`, `ciphertext`, and `recipients`
- `recipients` `MUST` be a non-empty list of recipient entries

Recipient entry shape:

- `kid`
  key identifier (client-defined)
- `recipient_pubkey`
  base64url X25519 public key (32 bytes)
- `epk`
  base64url ephemeral X25519 public key (32 bytes)
- `wrap_nonce`
  base64url XChaCha20-Poly1305 nonce (24 bytes)
- `wrapped_key`
  base64url ciphertext of the 32-byte content key

Launch baseline encryption scheme `x25519-xchacha20poly1305`:

1. The plaintext is UTF-8 JSON bytes representing the private state snapshot or bounded delta.
2. Generate a random 32-byte `content_key` and a random 24-byte `nonce`.
3. Encrypt the plaintext using XChaCha20-Poly1305 with `content_key` and `nonce`.
4. For each recipient public key:
   - generate an ephemeral X25519 keypair
   - compute the X25519 shared secret
   - derive a 32-byte wrapping key using HKDF-SHA256 with:
     `info = "foryou-private-state-wrap-v1"`
   - encrypt the 32-byte `content_key` using XChaCha20-Poly1305 under the wrapping key
5. Additional authenticated data (AAD) `SHOULD` bind the encryption to the message:
   `author_id`, `device_group_id`, `state_kind`, and `state_sequence`.

Device-group management baseline:

- Adding a device is an out-of-band pairing UX.
- When a new device is added, the client `SHOULD` publish a new compact snapshot encrypted to the updated recipient set so the new device can decrypt current state.
- Clients `SHOULD` support an optional offline recovery key as an additional recipient so a user can restore private state even if all devices are lost.

Example `private_state_update` payload:

```json
{
  "state_kind": "curation.v1",
  "encryption_scheme": "x25519-xchacha20poly1305",
  "encryption_scope": "device_group",
  "device_group_id": "dg_Ykz4Y2pQfWQp0b0x3uQ9aA",
  "state_sequence": 42,
  "encrypted_state": {
    "v": 1,
    "nonce": "b64url-24-bytes",
    "ciphertext": "b64url-ciphertext",
    "recipients": [
      {
        "kid": "device-1",
        "recipient_pubkey": "b64url-x25519-pubkey",
        "epk": "b64url-ephemeral-pubkey",
        "wrap_nonce": "b64url-24-bytes",
        "wrapped_key": "b64url-wrapped-key"
      }
    ]
  }
}
```

### Alias Registration

Required payload fields:

- `alias`

Optional payload fields:

- `namespace`
- `display_name`
- `bio`
- `avatar_reference`
- `profile_links`

Expected envelope support:

- `content_address` `MAY` be omitted when the full profile is inline

Launch-critical alias-registration support:

- `alias`

Validation notes:

- `alias_registration` provides a namespaced handle for user-facing UX, not a replacement for `author_id`.
- If `namespace` is omitted, clients should treat the namespace as `author_id` (self-namespaced alias).
- If `namespace` is present, clients should display the handle as `@alias@namespace` and should not assume global uniqueness.

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

For launch, canonical JSON serialization `MUST` follow RFC 8785 (JSON Canonicalization Scheme, JCS).

Launch-specific requirements:

- the signed object `MUST` include the envelope and payload fields required for message validation
- the `signature` field itself `MUST NOT` be included in the signed byte sequence
- implementations `MUST` not introduce optional fields with default values that change signed bytes

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
4. sign the resulting UTF-8 byte sequence with the signing key material:
   `signer_id` if present, otherwise `author_id`
5. encode the resulting signature in the `signature` field

## Example Envelope

```json
{
  "message_id": "msg-123",
  "author_id": "did:key:z6MkrJVnaZkeuWiRiwXQDq6rYmQXW1Lg31xHn3pV3hokW2Pp",
  "timestamp": "2026-03-01T14:00:00Z",
  "message_type": "post",
  "version": {
    "major": 1,
    "minor": 0
  },
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
  "version": {
    "major": 1,
    "minor": 0
  },
  "content_address": "ipfs://bafyexample",
  "language": "en",
  "keywords": ["distributed-systems", "indexing"],
  "submission_receipt": {
    "provider_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
    "plan_id": "annual-heavy-2026",
    "receipt_id": "receipt-post-123",
    "message_id": "msg-123",
    "units_charged": 1,
    "provider_signature": "base64-provider-signature"
  },
  "signature": "base64-signature"
}
```

Launch note:

- this example shows the normal plan-funded path

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
  "submission_receipt": {
    "message_id": "msg-123",
    "plan_id": "annual-heavy-2026",
    "provider_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
    "provider_signature": "base64-provider-signature",
    "receipt_id": "receipt-post-123",
    "units_charged": 1
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
  "version": {
    "major": 1,
    "minor": 0
  }
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
  "version": {
    "major": 1,
    "minor": 0
  },
  "content_address": "ipfs://bafyreplyexample",
  "submission_receipt": {
    "provider_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
    "plan_id": "annual-heavy-2026",
    "receipt_id": "receipt-reply-001",
    "message_id": "msg-reply-001",
    "units_charged": 1,
    "provider_signature": "base64-provider-signature"
  },
  "thread_id": "msg-123",
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
  "version": {
    "major": 1,
    "minor": 0
  },
  "content_address": "ipfs://bafyquoteexample",
  "submission_receipt": {
    "provider_id": "did:key:z6Mkq7Yf6m5hC2NX1LKcKD5Vac7wHxZ34rnKTtwe8QwMmpjD",
    "plan_id": "annual-heavy-2026",
    "receipt_id": "receipt-quote-001",
    "message_id": "msg-quote-001",
    "units_charged": 1,
    "provider_signature": "base64-provider-signature"
  },
  "thread_id": "msg-123",
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
  "version": {
    "major": 1,
    "minor": 0
  },
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
  "version": {
    "major": 1,
    "minor": 0
  },
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
  "version": {
    "major": 1,
    "minor": 0
  },
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
