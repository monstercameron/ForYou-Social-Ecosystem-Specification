# Date retrieval and pagination adversarial review

Date: 2026-11-11. Nonnormative record; current requirements belong to the protocol, portability and schemas.

## Scope and decisions

Three adversarial reviewers examined UTC single-date and half-open date-range filters on public listing routes, snapshot consistency, cursor safety, privacy and cost accounting. Date filtering uses the signed message timestamp. A UTC day is date=YYYY-MM-DD; explicit from is inclusive and until exclusive. Local calendar days require converting local midnight boundaries to UTC.

## Findings fixed

- Cursor tokens are exactly 32 unpredictable bytes stored as ownerless public continuation handles, canonically base64url encoded; decoded malformed tokens and malformed raw queries have explicit distinct errors.
- Cursors bind provider/route, normalized date bounds, author, effective page limit, fixed snapshot and keyset position. Tied timestamps order by message ID; late arrivals require a new snapshot.
- Empty nonterminal pages may occur after current restriction/expiry filtering. Servers enforce real advancement; clients cannot prove opaque-cursor progress and instead reject repeated tokens and enforce finite budgets.
- Current disclosure restrictions override snapshot bytes. Suppression/restriction/expiry events persist across the snapshot even if lifted before first scan, or invalidate that snapshot; no hidden identifiers are leaked by cursor metadata. Independently public signed references can contain known IDs; prohibited references require withholding the whole signed record.
- Retries charge no new publication debit or reader fee, but actual delivery consumes the purchased delivery budget. Quota failures cannot be treated as deletions or silently skipped.
- Clients check snapshot timestamps/expiry, per-page bounds, filters, ordering and uniqueness. Expired/lost snapshots require explicit rescan/deduplication, never a false completeness claim.

All three reviewers confirmed their targeted pagination findings closed. Reference cases cover day/range boundaries, leap years, malformed calendars and encodings, local-day UTC intervals of 23/25 hours, cross-provider/route/filter cursors, equal timestamps, late arrivals, suppress/restore events, quota and retries, large-message byte deferral and expiry. The reference model is not a deployed public index or proof of completeness against a malicious provider. Implementations still need concurrency, storage, abuse and interoperability testing.
