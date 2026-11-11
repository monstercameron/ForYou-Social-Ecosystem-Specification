# Core protocol checks

Create a disposable virtual environment, install `tests/requirements.txt`, then run:

```text
python -m unittest discover -s tests -p "test_*.py"
node tests/verify-vectors.mjs
node tests/strict-ed25519-reference.mjs
```

`security-vectors.json` uses synthetic fixed test keys/nonces, never production credentials. Regenerate with `python tests/test_security_profile.py --write-vectors`. Python exercises admission/receipt/final-message binding and owner-archive encryption. Node independently checks the published intent ID and Ed25519 signatures; its serializer is fixture-scoped.

Core message tests cover signed post/comment and update IDs, unresolved predecessors, same-author version relationships, deterministic fork display and bounded public pages. Apps' reply indexes and thread presentation are outside the storage service's state.

Other suites cover external URL/reference bounds, slot integrity, signature mutation rejection, archive-only prepared-record confidentiality/size, export paths, retry ordering, administrative binding, schema references and document links. Fee/quote examples use synthetic values and balances; they do not establish an activated payment schedule or verify real settlement. A separate in-memory model exercises finality gating, duplicate deposits, balance isolation, concurrent atomic debit and reorganization freezes, but does not implement a wallet, database or chain verifier. Removed social/preferences/ranking/sync contracts are checked as absent.

There is no deployed provider, payment verifier, index or client here. These are schema/cryptographic/reference-model tests, not proofs of production concurrency, legal compliance, absence of exploits or complete cross-provider threads. Anonymous public-download integration, owner-only export, network isolation and operational limits require real implementation tests before release.

Date retrieval tests exercise canonical UTC filters, cursor binding/expiry, immutable snapshot keyset behavior, restrictions and byte/count bounds. Multipart tests exercise 10,001+ entries, byte-aware part packing, signed manifest integrity, transformed prepared evidence, owner scope and interrupted chunk access. Delegation/epoch signature checks are synthetic; the suite does not establish correct concurrency, durable recovery, legal enforcement or availability in an implementation.

`strict-ed25519-vectors.json` is shared by independent Python and JavaScript arithmetic references and includes valid, malformed, small-order, mixed-order and cofactored-only cases. Both references are deliberately slow and non-constant-time, for public test data only; they are not production cryptographic libraries.

`test_economics_v1.py` and its model `economics_model.py` cover fee schedule 1, release-key schedule approval, the settlement sum tree and audit paths, committee witnessing and handover, receipt settlement states, quarterly distribution, declared retention and key succession. `test_payload_core.py` checks that presentation fields are not part of the signed payload. These are reference models with synthetic keys, not payment or custody implementations.

`test_settlement_search.py` is a randomized adversarial search over committee changes. An adversary controls the provider and up to one-third-minus-one of every committee, publishes several valid claims at one sequence, hides witnesses and leaves, and replaces monitors within the handover bounds several times, while honest monitors run the reference model. It checks that at most one claim at a sequence is ever settled, and includes sanity checks showing that it does find a double settlement when the quorum is weakened or holds are switched off. It is a bounded search with fixed seeds, not a proof.
