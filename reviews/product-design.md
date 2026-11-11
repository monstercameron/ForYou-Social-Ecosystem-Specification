# Product roles and app-experience design

SUPERSEDED: The user rejected social-app scope. Current normative docs retain only paid public-message storage and client-derived comments; the design below is historical and is not a launch requirement.

Date: 2026-11-11. Nonnormative design record; requirements belong to the seven owning documents and schemas.

## Decisions

Added seven product roles to the overview and concrete journeys for each in the client specification. Defined Home, Explore, Create, Activity, Profile, Saved and Services/privacy screen contracts, mobile/desktop navigation, publication states, accessibility and offline/failure behavior.

Selected chronological Following/Favorites, ordered 16-reference carousels, nested/collapsible discussions, private bookmarks/collections, custom author/topic feeds, bounded search and local activity. The client specification links primary Meta/Reddit sources for the inspiration and distinguishes historical announcements from current third-party capabilities. ForYou's limits and protocol semantics are independent design choices.

Ordinary Follow, Favorite, Save, Watch, Mute and Block are private local actions. Public recommendations, follows, replies, quotes and withdrawals remain explicitly approved paid protocol actions. Topic/provider views do not create global groups, moderators or membership authority. No hidden creator rewards, mutable signatures, private posting audience, remote spending or automatic media consent was added.

## Supporting contracts

- Added bounded topic/search/thread/related-message queries and direct public message retrieval, sharing the existing paginated discovery size/privacy/failure model.
- Added DiscoveryQuery, DiscoveryPage and PublicTransportMessage schemas; pages reject private state and clients validate scope and signed evidence.
- Extended Preferences with optional client_experience for favorites, topics, watched threads, feeds, collections and local activity settings. Defined legacy import behavior, stable local IDs, membership invariants and a 512 KiB plaintext budget.
- Kept CDN configuration/upload outside the protocol. Kept unsigned local drafts distinct from paid prepared-admission archives. Defined explicit limits for future private groups, DMs, events, commerce, polls, ads and payout systems.
- Added client journey evidence to governance, updated the ownership index and supplied synthetic preferences plus six contract tests.

## Verification and compatibility

50 Python tests, independent Node/OpenSSL signature-vector verification and Git whitespace checks pass. Tests cover schemas, reference predicates and cryptographic contracts, not a running UI or search service. The design still requires actual usability/accessibility, source-query isolation, consent, staff access and interoperability testing before deployment.

This is an unfrozen pre-release revision. Existing preference archives without client_experience remain structurally importable with explicit missing-setting disclosure. Older clients that reject this optional field need upgrading; do not silently discard it. Index implementations need the new bounded read routes before claiming the revised profile. Frozen-release changes would require the versioning process in governance. No new adversarial review is claimed for these product-design additions.
