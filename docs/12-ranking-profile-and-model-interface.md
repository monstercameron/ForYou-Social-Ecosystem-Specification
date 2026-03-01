# Ranking Profile and Model Interface

## Objective

Define a portable representation for ranking preferences and a stable interface between candidate content and ranking engines.

## Status

This document is a draft interface specification intended to support interoperability between clients, local model runners, and optional third-party ranking services.

The keywords `MUST`, `SHOULD`, and `MAY` are to be interpreted as normative requirements.

## Goals

- allow users to move ranking intent between clients
- separate candidate retrieval from ranking execution
- support local and remote model providers
- preserve private preference data under user control

## Concepts

- Candidate set:
  the list of posts or content references available for scoring
- Ranking profile:
  the user-controlled preferences, filters, and weights applied during ranking
- Ranking engine:
  the local or remote system that returns ordered or scored candidates
- Ranking result:
  the scored and ordered output presented to the client

## Baseline Requirements

- Clients `MUST` treat ranking output as advisory presentation state, not protocol state.
- Ranking engines `SHOULD` accept normalized candidate inputs rather than raw network transport messages.
- Clients `SHOULD` represent portable user ranking intent in a structured format.
- Remote ranking providers `MUST NOT` require publication of the user's full private context to the network.

## Ranking Profile Schema

### Required Fields

- `version`
  integer schema version for the ranking profile
- `profile_id`
  stable local identifier for the profile
- `display_name`
  human-readable label
- `objectives`
  ordered list of high-level ranking goals
- `topic_preferences`
  map of topic keys to numeric preference weights
- `language_preferences`
  ordered list of preferred languages
- `sensitivity_filters`
  structured moderation and sensitivity preferences

### Optional Fields

- `blocked_topics`
- `trusted_sources`
- `muted_sources`
- `freshness_weight`
- `thread_depth_preference`
- `media_preferences`
- `ad_tolerance`
- `explanation_level`
- `sync_policy`
- `private_state_reference`

### Validation Rules

- `version` `MUST` be a positive integer.
- `profile_id` `MUST` be unique within the client context.
- `display_name` `MUST` be non-empty.
- `objectives` `MUST` contain at least one value.
- `topic_preferences` values `SHOULD` be normalized between `0.0` and `1.0`.
- `ad_tolerance`, if present, `SHOULD` be normalized between `0.0` and `1.0`.
- Unknown fields `MAY` be preserved by clients for forward compatibility.
- `private_state_reference`, if present, `SHOULD` point to encrypted portable state rather than public metadata.

### Example

```json
{
  "version": 1,
  "profile_id": "default-local-profile",
  "display_name": "Default Feed",
  "objectives": ["relevance", "novelty", "trusted-sources"],
  "topic_preferences": {
    "distributed-systems": 0.9,
    "ai": 0.8,
    "politics": 0.2
  },
  "blocked_topics": ["celebrity-gossip"],
  "trusted_sources": [
    "did:key:z6MkrJVnaZkeuWiRiwXQDq6rYmQXW1Lg31xHn3pV3hokW2Pp",
    "did:key:z6Mkf8x8P5gL6N8sYZZs1xP7vC18JNpDutLCRa14Qdqgttxy"
  ],
  "muted_sources": ["did:key:z6MkpTHR8V4QjzvY4xXHzkwmo7aX6ixkmKuuNHYsYkdivgLP"],
  "language_preferences": ["en"],
  "freshness_weight": 0.7,
  "thread_depth_preference": 0.4,
  "media_preferences": {
    "video": 0.2,
    "image": 0.6,
    "text": 1.0
  },
  "ad_tolerance": 0.1,
  "sync_policy": "encrypted-portable",
  "sensitivity_filters": {
    "nsfw": "hide",
    "violence": "warn"
  }
}
```

## Candidate Content Schema

### Required Fields

- `candidate_id`
- `author_id`
- `timestamp`
- `content_type`
- `content_address`
- `is_ad`

### Optional Fields

- `language`
- `keywords`
- `thread_id`
- `reply_to`
- `payment_class`
- `local_features`
- `engagement_features`
- `retrieval_hints`

### Validation Rules

- `candidate_id` `MUST` uniquely identify the candidate within the ranking batch.
- `timestamp` `MUST` be a valid RFC 3339 UTC timestamp.
- `content_type` `MUST` be a recognized value known to the client or engine.
- `local_features` `MUST NOT` be published back to the network as protocol state.
- Clients `SHOULD` omit optional fields that are unavailable rather than invent placeholders.

### Example

```json
{
  "candidate_id": "post-123",
  "author_id": "did:key:z6MkrJVnaZkeuWiRiwXQDq6rYmQXW1Lg31xHn3pV3hokW2Pp",
  "timestamp": "2026-03-01T14:00:00Z",
  "language": "en",
  "content_type": "post",
  "keywords": ["distributed-systems", "indexing"],
  "thread_id": "thread-88",
  "reply_to": null,
  "content_address": "ipfs://bafyexample",
  "payment_class": "standard",
  "is_ad": false,
  "local_features": {
    "seen_before": false,
    "source_trust_score": 0.93
  }
}
```

## Ranking Engine Input

### Required Fields

- `profile`
- `candidates`
- `runtime.mode`
- `runtime.model_id`

### Optional Fields

- `runtime.max_items`
- `runtime.explanation_level`
- `runtime.device_constraints`
- `runtime.remote_policy`

### Example

```json
{
  "profile": {},
  "candidates": [],
  "runtime": {
    "mode": "local|remote|hybrid",
    "model_id": "string",
    "max_items": 100
  }
}
```

## Ranking Engine Output

### Required Fields

- `model_id`
- `mode`
- `results`

Each result item `MUST` include:

- `candidate_id`
- `score`

### Optional Fields

- `labels`
- `explanation`
- `trace_id`

### Validation Rules

- `results` `SHOULD` be ordered from highest to lowest score unless otherwise declared.
- `candidate_id` values in `results` `MUST` refer to candidates present in the input batch.
- `score` `SHOULD` be normalized to a stable range within a given engine implementation.

### Example

```json
{
  "model_id": "string",
  "mode": "local|remote|hybrid",
  "results": [
    {
      "candidate_id": "post-123",
      "score": 0.982,
      "labels": ["relevant", "trusted-source", "fresh"]
    }
  ]
}
```

## Integration Targets

- Local runners:
  LM Studio, local inference servers, embedded on-device models
- Remote providers:
  hosted APIs, state-of-the-art cloud models, specialized ranking vendors
- Client adapters:
  mapping between protocol candidate retrieval and engine input/output

## Privacy Boundaries

- Private ranking features `SHOULD` remain on-device by default.
- Clients `MUST` disclose when profile or candidate data is sent to a remote service.
- Clients `SHOULD` minimize the data sent to remote ranking providers.
- Remote services `MUST NOT` be treated as protocol authorities.
- When a client syncs private curation across devices, it `SHOULD` use encrypted portable state rather than public interaction metadata.

## Related Documents

- `11-attention-and-ranking-model.md`
- `14-protocol-metadata-requirements.md`
- `15-reference-client-feed-flow.md`

## Open Decisions

- Should the profile schema be part of the base protocol or an ecosystem standard?
- Which candidate fields should be promoted from optional to required?
