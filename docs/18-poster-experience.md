# Poster Experience

## Objective

Define the user experience for a person who wants to publish content to the ForYou network.

## Scope

This document covers:

- the poster's mental model
- the poster journey
- required UX behaviors for publishing
- poster-facing failure handling

## Core Mental Model

From the poster's perspective:

- fund a wallet with BTC or ETH
- fund or renew a provider posting plan
- choose any compatible client
- write a post
- approve one publish action
- publish to the network

The poster pays for publication, not for guaranteed audience reach.

## Poster Goals

- publish without asking permission from a central platform
- understand the cost before posting
- complete the publish flow in one clear action
- know whether the post is pending or published
- understand that reader visibility is decided by readers, not by the poster

## Baseline Poster Journey

1. open a compatible client
2. connect or create the posting identity
3. ensure BTC or ETH is available for plan funding or renewal
4. fund or renew the provider plan when needed
5. write a post or reply
6. review the allowance impact or fallback cost
7. approve publish
8. wait for `pending` or `published`
9. optionally withdraw the post later through the chosen client
10. optionally share or monitor engagement through the chosen client

## UX Requirements

- The client `MUST` show plan status, allowance impact, or fallback cost before publish approval.
- The client `SHOULD` make plan-funded publishing feel like one action.
- The client `MUST` distinguish between `pending` and `published`.
- The client `SHOULD` explain that network publication does not guarantee ranking or visibility in every reader feed.
- The client `MUST NOT` imply that the client operator controls global publication rights.
- The client `SHOULD` support a clear withdraw flow for the author's own prior content.

## Poster Status Model

- `pending`
  the publish request has been submitted but is not yet accepted by a network path
- `published`
  the post is fully accepted on the launch baseline

## Poster Failure Cases

- insufficient funds
- expired or exhausted plan
- unsupported chain
- malformed funding or receipt reference
- funding to the wrong recipient
- message validation failure
- provider unavailable

Clients should explain these failures in plain user language.

## Poster Trust Expectations

- the poster should be able to verify that the post was accepted
- the poster should not need to understand node roles to publish
- the poster should understand that some hosts may not serve the content in all jurisdictions

## Related Documents

- `05-payments-and-economic-model.md`
- `09-client-facing-products.md`
- `15-reference-client-feed-flow.md`

## Open Decisions

- How much poster-facing delivery or engagement visibility belongs in launch clients?
