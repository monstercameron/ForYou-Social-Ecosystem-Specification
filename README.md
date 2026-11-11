# ForYou Core Message Storage Specification

ForYou defines publicly downloadable signed text messages. Each record pays a specification-set admission fee. The fee is an anti-spam hurdle, not a purchase of audience reach.

**Posts, comments and edits.** Each post may include up to 16 external image/video slots. The user or app chooses and configures media hosting; it is outside the storage protocol. A comment is another paid post with `reply_to` pointing to its parent. An edit is another signed post with `supersedes` pointing to the prior version. It pays the full fee calculated for its own canonical intent. The protocol has no author-delete message; legal restrictions and removals remain provider-local.

**Retention.** Each provider declares its retention period, with a minimum of one year. The ForYou Foundation funds and owns a Lifetime Vault that retains every delivered record with no scheduled expiry. This is an obligation of the Foundation, not a guarantee that any operator survives or can lawfully serve every record forever.

**Reading.** Anyone can download retained public records without a reader account, wallet signature or reader purchase. Explicit availability, rate and legal limits apply. Apps verify the records and build their own threads, feeds or other experiences. Likes, favorites, follows, profiles, ranking and private preference sync are not core protocol state. An optional [display names profile](./docs/12-display-names-profile.md) lets an author sign a non-unique name for their key; follows stay in the client.

**Paying for a post.** Publishers fund a balance with their chosen provider in Bitcoin or Ethereum. They then authorize a separate debit for each post. The balance is an accounting claim on that provider, not a transferable protocol token or a portable network balance. A provider's failure or insolvency may put the balance at risk. Funding and withdrawal network fees are separate.

**The fee and where it goes.** Fee schedule 1 charges 136 millisatoshis or 48,900,000,000 wei per started KiB of the canonical intent. That is about US$0.0001 at the release reference prices. Providers collect the fee and settle all of it to the Foundation. Settlement uses prepaid on-chain deposits and signed claims that anyone can audit. Each quarter the Foundation returns to each provider a part of the fees that provider settled:

- the part is larger for better measured quality and longer proven retention;
- it is never more than the policy's keep share (half under policy 1).

The Foundation keeps the rest for the vault and the monitor committee. There is no protocol token.

**Status.** This repository is the text of specification release 1.0: documents, a schema library and a regression-test collection. It is not a deployed network or an executable financial contract. The release is frozen, and a network can exist, only when the [release checklist](./docs/06-governance.md#release-checklist) is complete and the genesis manifest is signed. Independent implementations, security review, legal review and measured operating capacity are part of that checklist.

| Area | Document |
| --- | --- |
| Core scope and actors | [Overview](./docs/01-overview.md) |
| Signed messages, updates, admission and comments | [Protocol](./docs/02-protocol.md) |
| Fees, settlement, distribution and retention | [Economics](./docs/03-economics.md) |
| Provider accountability and rights | [Compliance](./docs/04-compliance.md) |
| Public download, incremental sync and provider exit | [Portability](./docs/05-portability.md) |
| Foundation, versioning and release calendar | [Governance](./docs/06-governance.md) |
| Minimal publisher/downloader integration | [Clients](./docs/07-clients.md) |
| Nonnormative provider implementation examples | [Operator guide](./docs/08-operator-guide.md) |
| Provider quality evidence | [Quality](./docs/09-quality.md) |
| Optional owner export profile | [Owner export](./docs/10-owner-export-profile.md) |
| Nonnormative operator compliance guidance | [Compliance guide](./docs/11-operator-compliance-guide.md) |
| Optional signed display names | [Display names](./docs/12-display-names-profile.md) |
| Route and error index | [API catalog](./docs/API-catalog.md) |

The [documentation index](./docs/README.md) defines ownership. [Launch schemas](./schemas/launch.schema.json) and [operations schemas](./schemas/operations.schema.json) define structural contracts; semantic checks and signatures remain mandatory. See [test instructions](./tests/README.md). Review records describe historical snapshots and never override current normative documents.
