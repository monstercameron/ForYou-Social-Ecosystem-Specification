# Protocol Metadata Requirements

## Objective

Define the minimum protocol-visible metadata required to support strong local ranking, filtering, and retrieval without exposing private user state.

## Status

This document is a draft requirements specification with a provisional launch baseline.

The keywords `MUST`, `SHOULD`, and `MAY` are to be interpreted as normative requirements for the launch baseline sections of this document. Other sections remain explanatory unless they are explicitly tied to launch behavior.

## Design Principle

The protocol should expose enough public metadata to make local ranking viable while keeping private user context outside protocol state.

## Minimum Metadata Set

Each rankable content item `MUST` expose or reference the following public metadata:

- `message_id`
  stable identifier for the message
- `author_id`
  stable author identity reference
- `timestamp`
  creation timestamp
- `content_type`
  base type such as post, reply, ad, poll, or alias update
- `content_address`
  reference to retrievable full content
- `language`
  primary language when known
- `is_ad`
  explicit advertisement indicator

## Strongly Recommended Metadata

The protocol `SHOULD` expose:

- `thread_id`
- `reply_to`
- `target_message_id`
- `target_author_id`
- `target_topic`
- `keywords`
- `topic_tags`
- `media_kinds`
- `payment_class`
- `content_size`
- `signature_status`

## Optional Metadata

The protocol `MAY` expose:

- `reply_count`
- `quote_count`
- `counterpoint_count`
- `recommend_count`
- `weighted_recommend_score`
- `thread_subscriber_count`
- `topic_follower_count`
- `message_status`
- `target_status`
- `link_domains`
- `geo_scope`
- `content_warning_flags`
- `reshare_of`
- `edit_of`
- `retention_policy`

## Validation Requirements

- `message_id` `MUST` be unique.
- `timestamp` `MUST` be parseable and comparable.
- `author_id` `MUST` be stable enough for trust, mute, and follow decisions.
- `is_ad` `MUST NOT` be omitted for paid promotional content.
- `content_address` `MUST` resolve to retrievable content or a verifiable retrieval failure state.
- if a provider exposes `message_status` or `target_status`, the values `SHOULD` distinguish at least `active`, `withdrawn`, `unavailable`, and `blocked` where applicable.

## Privacy Boundaries

The protocol `MUST NOT` require publication of:

- local reading history
- user embeddings
- user trust scores
- user preference weights
- device-local behavioral signals
- local moderation decisions
- encrypted private-state contents
- private-state sync references in public candidate metadata

## Why These Fields Matter

- Identity fields:
  support source trust, blocking, and preference learning
- Time fields:
  support freshness and recency ranking
- Thread fields:
  support conversation-aware ranking
- Target fields:
  support interaction-aware ranking and graph reconstruction
- Target-status fields:
  support resilient rendering when a referenced message is withdrawn, unavailable, or locally blocked
- Content references:
  support selective retrieval of full content after lightweight ranking
- Ad markers:
  support transparent paid-content handling

## Candidate Metadata Example

```json
{
  "message_id": "msg-123",
  "author_id": "did:key:z6MkrJVnaZkeuWiRiwXQDq6rYmQXW1Lg31xHn3pV3hokW2Pp",
  "timestamp": "2026-03-01T14:00:00Z",
  "content_type": "post",
  "content_address": "ipfs://bafyexample",
  "language": "en",
  "is_ad": false,
  "thread_id": "thread-88",
  "message_status": "active",
  "target_status": null,
  "reply_count": 3,
  "recommend_count": 2,
  "keywords": ["distributed-systems", "indexing"],
  "media_kinds": ["text"]
}
```

## Relationship To Ranking

- This metadata is public candidate input.
- Private ranking context remains local to the user or to a user-selected remote ranking service.
- Clients `SHOULD` combine protocol metadata with private local features before ranking.
- Raw lightweight-interaction counts such as `recommend_count`, `thread_subscriber_count`, or `topic_follower_count` `MUST NOT` be treated as high-trust ranking truth without local or provider-specific weighting.
- If providers expose derived weighting fields such as `weighted_recommend_score`, those fields `SHOULD` be treated as advisory inputs rather than canonical truth.
- Private portable state such as bookmarks, mutes, blocks, trust lists, or notes should be handled outside public candidate metadata surfaces.

## Related Documents

- `04-data-and-message-formats.md`
- `06-storage-indexing-and-ai-processing.md`
- `11-attention-and-ranking-model.md`
- `12-ranking-profile-and-model-interface.md`
- `16-identity-and-source-references.md`
- `17-index-provider-and-candidate-chunk-api.md`

## Open Decisions

- Which metadata fields are required for all content types versus only some types?
- Should topic tags be protocol-native or client-derived?
- Which derived social counts should be standardized across providers at launch?
