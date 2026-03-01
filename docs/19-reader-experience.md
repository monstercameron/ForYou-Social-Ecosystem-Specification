# Reader Experience

## Objective

Define the user experience for a person reading content from the ForYou network.

## Scope

This document covers:

- the reader's mental model
- feed and discovery behavior
- filtering and ranking controls
- reader-facing failure handling

## Core Mental Model

From the reader's perspective:

- choose a compatible client
- fetch candidate content from the network
- rank locally by default
- shape the feed with personal filters and preferences
- read what is useful without controlling what everyone else sees

## Reader Goals

- get a useful feed without surrendering attention control
- understand why content appears or does not appear
- keep preferences and private context local by default
- preserve important private curation across the user's own devices without making it public
- use filters, trust, mute, and follow tools without confusing local preferences with protocol validity
- fall back gracefully when content is missing from one host

## Baseline Reader Journey

1. open a compatible client
2. choose local ranking by default or opt into remote ranking
3. set preferences, follows, mutes, and trust rules
4. browse ranked content
5. open posts or threads as needed
6. let the client fetch full content lazily
7. adjust local preferences over time and sync private curation when enabled

## UX Requirements

- The client `MUST` make clear that reading and ranking are reader-controlled.
- The client `SHOULD` make local ranking the default when feasible.
- The client `MUST` disclose remote ranking when used.
- The client `SHOULD` explain when content is unavailable from one provider but may exist elsewhere.
- The client `MUST NOT` treat ranking or filtering as protocol truth.
- The client `SHOULD` support encrypted sync or export for private curation state.
- The client `SHOULD` display aliases and profiles when available, while showing a short fingerprint of `author_id` to reduce impersonation.

## Reader Controls

Public controls:

- reply
- quote
- counterpoint
- recommend
- follow source
- follow topic
- subscribe to thread

Private curation controls:

- mute
- trust source
- hide
- bookmark
- boost
- downrank
- sensitivity preferences
- local ranking mode choice

Public interactions shape shared social context.

Private curation interactions such as mute, trust, hide, bookmark, boost, downrank, and notes shape only the reader's experience even when they are synchronized across the reader's own devices.

Clients should treat public lightweight interactions such as recommend, follow source, follow topic, and subscribe to thread as weak shared context rather than as authoritative popularity truth.

Clients should allow lightweight public interactions to feel immediate and reconcile them with the network path in the background where possible.

## Reader Failure Cases

- provider unavailable
- content missing from one host
- remote ranking unavailable
- stale host hints
- invalid metadata from a provider

Clients should recover through alternate providers, local fallback, or unranked display where possible.

## Reader Trust Expectations

- the reader should be able to verify content by content address
- the reader should be able to switch clients without losing the core network
- the reader should understand that local filtering does not delete content from the network

## Related Documents

- `06-storage-indexing-and-ai-processing.md`
- `11-attention-and-ranking-model.md`
- `15-reference-client-feed-flow.md`

## Open Decisions

- How much explanation should launch clients provide for why a specific item was ranked highly?
