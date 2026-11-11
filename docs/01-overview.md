# Principles and core architecture

## Purpose

ForYou is a public-message protocol for signed text. An author pays a specification-set per-record admission fee and submits a signed post. The post may carry up to 16 external image/video slots. In return the author receives a verifiable admission receipt.

The fee is an anti-spam hurdle; it does not buy audience reach. Anyone can download retained public messages and verify their authorship, admission and fee settlement. No publishing account, wallet signature or reader purchase is needed. Users and apps choose and configure media hosting separately.

## Design goals

Every rule in this specification serves one of these goals. A change that works against one of them needs a new major release.

| # | Goal | Where it is met |
| --- | --- | --- |
| G1 | The specification sets the fee, through schedules approved by the release keys within a fixed bound. Neither providers nor the Foundation have pricing power. | [Fee schedule](./03-economics.md#denominations-and-versioned-fee-schedule) |
| G2 | The fee is a small hurdle against spam, not a profit source. It scales with message size. | [Fee schedule](./03-economics.md#denominations-and-versioned-fee-schedule) |
| G3 | The hurdle is real for everyone, including a provider that admits its own posts. Only a settled receipt proves payment. Settlement draws on money already deposited. One deposit cannot settle two claim chains. No provider gets back more than it paid. | [Settlement](./03-economics.md#settlement), [distribution](./03-economics.md#distribution) |
| G4 | Fees go to the Foundation, and part is returned later. A provider with better quality and longer proven retention keeps more. | [Distribution](./03-economics.md#distribution), [quality evidence](./09-quality.md) |
| G5 | Providers build their own services on top of public posts. The protocol does not fund them beyond distribution. | [Economics](./03-economics.md#purpose) |
| G6 | Reading is free and needs no account. | [Public download](./05-portability.md#public-download-and-provider-exit) |
| G7 | The protocol never deletes posts. An edit is a new version. | [Posts, comments and versions](./02-protocol.md#posts-comments-and-versions) |
| G8 | Content is plain text or Markdown, with raw HTML inert. Signed media slots and signed references are placed from the text. | [Text payloads](./02-protocol.md#text-payloads-and-external-media-references) |
| G9 | Each provider chooses its retention period. The Foundation's Lifetime Vault keeps everything. | [Retention](./03-economics.md#retention-and-the-lifetime-vault) |
| G10 | Core only. Presentation, ranking, social graphs and other application features stay out. | [Core principles](#core-principles) |
| G11 | No single party can forge, censor or silently unsettle a paid post. The Foundation has no vote in settlement. A quorum of more than two-thirds of an independent committee decides it from public data. The release keys act only by a two-thirds threshold. | [Settlement committee](./03-economics.md#the-settlement-committee), [release keys](./06-governance.md#release-keys) |

## Core principles

- Users control their signing identity. They can change providers without the former provider's permission.
- The specification sets the admission fee through a release-approved schedule for Bitcoin and Ethereum. Providers do not set, keep or discount the fee. They collect it and settle all of it to the ForYou Foundation. The Foundation later returns part of it to each provider according to its quality and proven retention.
- Each provider declares how long it retains records, with a minimum of one year. The Foundation funds and owns a Lifetime Vault that retains every delivered record with no scheduled expiry. Retention and free anonymous reads are subject to lawful restrictions and operational limits.
- Authority is divided and narrow:
  - The release keys approve fee schedules.
  - The Foundation receives fees, distributes them and runs the vault.
  - A settlement committee audits that every fee was paid. Its committee monitors are independent and named by the release keys. The committee has no authority over message validity, identity, moderation or client trust choices.
  - There is no protocol token, global feed, handle registry or moderation authority.
- Messages are immutable signed records. An update is a new, separately signed and paid post. It does not change or erase earlier versions.
- Public download does not mean unlimited bandwidth or exemption from safety and legal limits. Failures and restrictions MUST be explicit.
- Likes, favorites, follows, bookmarks, profiles, feeds, ranking, notifications, private groups and private preference sync are application features outside this core specification. The optional [display names profile](./12-display-names-profile.md) adds only a signed, non-unique name for a key; it creates no registry and no follow state.
- Polls, events, live streams, pinned status and engagement counts are application-level features, not protocol message types.

## Actors and required state

| Actor | Core role |
| --- | --- |
| Publisher | Funds a provider-local balance, authorizes each per-record debit and signs messages, including comments and updates |
| Storage/admission provider | Verifies funding and authorization, maintains the provider-local balance, debits admission fees, issues receipts, settles every fee to the Foundation, retains accepted records for its declared period and delivers them to the vault |
| ForYou Foundation | Receives fees, publishes quarterly distributions to providers, and funds and owns the Lifetime Vault |
| Settlement committee | The committee monitors named in the release-approved policy. Each audits providers' claims against the chain and witnesses them. A quorum of more than two-thirds settles a claim |
| Downloader or app | Downloads public records, verifies proofs and builds its own presentation or indexes |
| Optional independent index, replica or monitor | Helps locate, retain or measure records under disclosed, independently funded terms |

The protocol is minimal-state rather than literally stateless. Providers need:

- separately accounted Bitcoin and Ethereum balances;
- payment and admission results, for idempotency;
- retained messages;
- delegation-revocation records;
- applicable provider-local restriction/removal records.

A balance is a liability of the provider holding it, not a transferable network token. It does not automatically move when the author changes providers. Provider failure, insolvency and custody compromise can impair it. Funding and withdrawal network fees are separate from the per-record fee.

Providers do not maintain social graphs, preferences, feed state or an authoritative version-chain object. One operator can fill several roles; different endpoints are not proof of independent control. [Decentralized operation and trust boundaries](./05-portability.md#decentralized-operation-and-trust-boundaries) define what provider independence does and does not establish.

## Publication and download

```text
fund chosen provider -> wait for confirmed balance -> compose text and media slots
                 -> compute and approve per-record fee -> authorize admission
                 -> provider atomically debits balance and issues receipt
                 -> author signs complete message -> provider finalizes storage
provider        -> settle fees to the Foundation -> deliver messages to the vault
any downloader  -> fetch/list public messages -> verify IDs, signatures and settlement
                 -> optionally reconstruct comments or build an app-specific view
```

Bitcoin and Ethereum are the funding networks. Bitcoin sub-satoshi amounts are accounting units, not independently spendable outputs. Ethereum balances are denominated separately. The fee applies to each canonical intent; the message text is not stored on-chain. Admission and balances are provider-local, not global network consensus.

Public download never reveals the content or message ID of an unfinished submission, private payment records or administrative evidence.

## Messages, updates and comments

The only public message type is post. A post contains text, optional media references and an optional reply_to naming any version of another post. A comment is an ordinary paid post linked to its parent, not a separate social-state object. Nested references form a discussion tree that apps reconstruct. No authoritative thread object, comment counter or global ordering service is required. See [message semantics](./02-protocol.md#posts-comments-and-versions).

An optional `payload.supersedes` identifies the immediately prior version. The update and its target MUST have the same author and the same `reply_to` value, including both absent. A delegate's post scope covers updates. Each update incurs the full size-scaled fee for its own canonical intent.

Every version is a separate immutable record with its own retention period. An update does not replace or erase an earlier record. Clients reconstruct chains from verified records and resolve forks deterministically among records they know. The protocol has no author-delete operation; provider-local legal restriction and removal processes remain separate. Media files, live video, likes/reactions, favorites, recommendation algorithms and app workspaces are outside the storage protocol.

An optional signed `payload.refs` array holds up to 32 structured references to canonical message IDs or author DIDs. Markdown can place them using `fy-ref:<id>`; the display label is not identity evidence. Clients and independent indexes can thus recognize references without a handle registry, notification service or social graph. A bare `@name` or hashtag remains ordinary text. `reply_to` remains the separate signed thread-parent field.

## Limits

Provider receipts attest admission and rely on the provider's honesty. A settlement proof shows that the fee was paid to the Foundation. Neither proves solvency or legality.

Provider retention ends at the declared period. The Lifetime Vault is an obligation of the Foundation, not a guarantee that it never fails or that lawful restrictions never apply. Source coverage can be incomplete, and copies can persist outside the network. No claim of worldwide legality, perpetual availability or absence of exploits follows from this specification.

A lost root key cannot be recovered, and there is no account-recovery authority. An author who still controls a key can name a successor with a [key succession](./02-protocol.md#key-succession). A thief who holds the key can do the same, so a succession is an advisory link. Clients MUST explain this limitation and offer a protected backup path.
