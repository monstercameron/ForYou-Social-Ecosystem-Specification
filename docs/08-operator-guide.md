# Operator guide (nonnormative)

This guide describes operational choices. It defines no message type or route and never overrides the normative documents listed in the [index](./README.md). Operators remain responsible for applicable law, user commitments, security and their actual funding model.

## Payment research

The protocol fee is about US$0.0001 per started KiB at the release reference prices. The exact native-unit amounts are in the release-approved [fee schedule](./03-economics.md#denominations-and-versioned-fee-schedule). Fixed native amounts fluctuate against the dollar, and network transaction costs are additional.

A single fee is smaller than one satoshi and far below any practical on-chain output. For that reason:

- authors prepay a provider-local balance;
- the provider funds a prepaid settlement account at the Foundation with occasional on-chain deposits;
- the provider draws that account down with signed claims.

Ethereum gas is separate and variable.

The provider is a collection agent. Every fee it debits is owed in full to the Foundation under [settlement](./03-economics.md#settlement). Its income from the protocol is the later [distribution](./03-economics.md#distribution).

Keep the prepaid settlement account funded ahead of each claim. Deposits are at least 10,000 satoshis or 10^15 wei and are not refundable.

A provider-local balance is an operator liability and a custodial relationship, not a portable network token. A settlement proof (witnesses from a quorum of more than two-thirds of the committee monitors) shows that a receipt is included in a claim covered by deposits. It does not prove provider solvency.

## Operation and financing

Operators need funded capacity for at least the retention period they declare. That capacity covers retained text, public reads, vault delivery, recovery and lawful handling.

The part of its settled fees a provider gets back grows with measured quality and proven retention. A longer `RetentionDeclaration` is therefore a commitment to fund. A record keeps the retention of the declaration its claim named.

Use settlement periods of at most 24 hours and publish each claim promptly, so receipts settle well inside the 7-day pending limit. Deliver each finalized message to the Lifetime Vault within 7 days after its receipt is settled. The vault, operated by the Foundation, keeps it after the provider's own period ends. Neither the provider's copy nor the vault is a guarantee of perpetual availability.

Users or applications choose and fund external image and video hosts separately.

Providers may enter voluntary private agreements for replication or indexing. Such agreements do not change the protocol fee, the settlement duty or the distribution formula.

When several versions of a record exist, the default selection among known leaves is the three-step rule in [clients](./07-clients.md#version-chains). An index that reports a "latest version" follows the same rule and stays advisory.
