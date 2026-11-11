# Core scope correction and comments

SUPERSEDED: This historical record predates the post-only versioning decision. Current documents define updates with `supersedes` and no author-delete message.

Date: 2026-11-11. Nonnormative change record; this supersedes the social-app product design. The user specified paid message storage with public download, not a protocol-owned social network experience.

## Resulting scope

- Public TransportMessage supports post and withdraw. Posts store text and up to 16 external media references. A comment is a post with signed reply_to; nested parent references are reconstructed by apps without a thread object, social graph, counter or preference state.
- Any downloader can use public direct-message and paginated listing routes without an account, reader purchase or signing proof, subject to disclosed rate/retention/legal limits. Publication purchases fund positive public-delivery budgets.
- Likes/recommendations, favorites, follows, subscriptions, profiles, ranking, topic/search/thread query APIs, app screens and private preference synchronization were removed from the core schemas/contracts. Apps can implement their own derived services.
- Retained necessary payment/receipt/retry, storage, delegation revocation, withdrawal and provider rights obligations. Minimal-state does not mean removing anti-double-charge or security state.
- Owner-only confidential prepared submissions still export as encrypted ArchiveRecord artifacts, never public transport. The encryption profile no longer implies a sync endpoint. Public exports require no app preference snapshot.

## Comments

Each comment pays for its own post, binds its parent ID into its message ID/signature/receipt and can itself receive replies. A parent is resolved through approved providers, not an arbitrary fetch URL. Missing/withdrawn parents stay placeholders; child records are independently valid. Parent-author attribution requires verified parent evidence. Apps may maintain advisory child indexes, deduplicate and bound traversal; no provider is presumed to know all cross-provider comments.

## Validation and compatibility

45 Python tests, independent Node/OpenSSL signature checks and Git whitespace checks pass. These changes have not received a new adversarial-agent review and no production security claim follows.

This is a breaking correction to an unfrozen pre-release specification. Previous social-action messages/private-state records are legacy artifacts, not silently rewritten into accepted core records. Old signatures must remain original evidence. Comment imports require explicit republishing under the new shape if they used the removed reply type; do not convert their IDs or charge automatically. The working tree remains uncommitted.
