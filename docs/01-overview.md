# Principles and architecture

## Purpose

ForYou separates publication, storage, discovery and presentation. Authors fund bounded publishing services with BTC or ETH, produce portable signed messages, and retain their identity when changing providers. Readers choose which sources to query and how to filter and rank what those sources offer.

## Core principles

- Identity and signed history belong to the user; provider exit does not require the former provider's permission.
- No compulsory network token, shared treasury, exclusive registry, global moderation authority or universal recommendation algorithm.
- Operators independently choose service terms, legal policies, peers and trusted admission providers. Compatibility is not an obligation to host every object.
- Reader controls and private preferences remain local unless explicitly shared under the consent rules.
- Fees purchase disclosed service commitments; popularity, permanent availability and audience reach are not included guarantees.
- Local legal restrictions do not rewrite cryptographic identity or automatically dictate every other operator's behavior.

## Actors and trust

An author signs messages. An admission provider verifies ownership, funded allowance and message intent, then issues a receipt while committing contracted resources. Storage operators retain verified objects for funded periods. Index providers expose the public messages they can lawfully and technically return. Clients verify evidence and apply reader choices. A remote ranking service, when selected, returns advisory scores and receives only specifically authorized data.

One operator can perform several roles, but that does not make its endpoints independent. Provider signatures attest admission; they do not prove solvency, lawful processing or unbiased discovery. Trust defaults must be visible and replaceable. A reader's ranking cannot surface content absent from every queried index.

## Publication and reading

```text
author -> verify plan/offer -> fund service -> prepare signed intent
       -> stage committed content -> provider reserves resources and issues receipt
       -> author signs complete message -> provider finalizes replica metadata
       -> independent indexes and hosts, subject to their policies
       -> reader verifies messages/content -> applies chosen filters and ranking
```

The same signed identity can use another provider. Raw BTC/ETH transactions settle funding; social content and private preferences are not written to a blockchain. Admission accounting is consistent within the chosen provider, not a global consensus ledger. There is no global feed order or proof that every node has seen a message.

## Included and excluded capabilities

The public baseline supports posts, replies, quotes, counterpoints, withdrawals, recommendations, source/topic follows, thread subscriptions and self-namespaced profiles. Public messages require bound receipts. Private state uses a separate encrypted, authenticated sync path and never enters public discovery.

Reusable admission tokens, polls, advertisements, network-wide reward pools, exchange/transferable balances, account takeover by support staff and same-identity recovery after root compromise are excluded. Ordinary hosting, subscriptions, sponsorship and bilateral service contracts can fund the network within the economics and compliance requirements.

## Limits

Withdrawal changes visible state but cannot guarantee deletion by unknown independent parties. Expired retention can end availability. Root-key compromise requires a new identity. Provider accounting and timestamps remain trust assumptions. Censorship resistance means avoiding compulsory chokepoints, not immunity from law, outages or refusal to serve. These limits must be reflected in client claims and operating contracts.
