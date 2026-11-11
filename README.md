# ForYou Social Ecosystem Specification

ForYou is a proposed paid publishing network with portable signed identity and reader-controlled feeds. Independent providers admit funded messages, hosts retain bounded copies, indexes provide discovery, and readers choose clients, filters and ranking. Payment does not guarantee audience reach, universal acceptance or permanent storage.

This repository is a **pre-release specification**, schema library and regression-test collection. It does not contain a deployed social network or executable financial smart contracts. Legal review, license authorization, independently tested implementations and measured operating economics remain release requirements.

Start with the [documentation index](./docs/README.md). The seven documents form one current specification set; there are no historical override documents to combine with it.

| Area | Current document |
| --- | --- |
| Principles and architecture | [Overview](./docs/01-overview.md) |
| Messages, identity, authorization, sync and retrieval | [Protocol](./docs/02-protocol.md) |
| Funding, admission services, renewals and sustainability | [Economics](./docs/03-economics.md) |
| Operator obligations, privacy, moderation and regional assessment | [Compliance](./docs/04-compliance.md) |
| Discovery, provider exit, exports and recovery limits | [Portability](./docs/05-portability.md) |
| Versioning, governance and pilot requirements | [Governance](./docs/06-governance.md) |
| Publishing/reading experience and optional ranking interface | [Clients](./docs/07-clients.md) |

Machine-readable contracts are in [launch.schema.json](./schemas/launch.schema.json) and [operations.schema.json](./schemas/operations.schema.json). Structural validation alone does not establish valid signatures, authorized actions, funded obligations or legal compliance.

See [test instructions](./tests/README.md) and the [consolidation review](./reviews/consolidation-review.md). Economic examples are synthetic planning scenarios, not operating results. Future extensions require explicit versioning; reusable admission tokens, advertisements, polls, transferable balances and automatic traffic-based rewards are not part of this baseline.
