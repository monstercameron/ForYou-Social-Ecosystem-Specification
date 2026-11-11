# Security profile checks

Use a disposable virtual environment and install `tests/requirements.txt`, then run:

```text
python tests/test_security_profile.py
python -m unittest discover -s tests -p "test_*.py"
node tests/verify-vectors.mjs
```

`security-vectors.json` contains fixed synthetic test keys/nonces and must never be used for real accounts. Regenerate with `python tests/test_security_profile.py --write-vectors`. Review any fixture changes as protocol changes.

Python validates the schema and exercises direct-author receipt binding, tampering, signature domain separation and encrypted-state authentication. Node independently verifies the published fixture's canonical intent, ID and Ed25519 signatures using OpenSSL. Its serializer is intentionally fixture-scoped. These are not two complete protocol implementations. No live provider, chain node or sync server exists in this repository; concurrency, revocation durability, funding reorganization, network filtering and authenticated sync still require implementation integration tests before deployment.

The operations suite adds offer/terms commitment, grace bounds, plan/offer linkage, renewal price authorization, archive path examples, preference shape and a synthetic cost stress model. It does not implement billing, filesystem extraction, policy decisions, legal compliance or full archive restore. `examples/economics-scenarios.json` intentionally includes negative stress outcomes; no operating evidence or claim of sustainability is implied.

The full-spec audit suite adds schema, cryptographic and small reference-model regressions for private metadata leakage, content/admission size, administrative intent binding, mixed reserve choices, calendar overflow, retry ordering, manifest rollback and withdrawn relationship state. These reference models describe intended contracts; passing them is not proof that a future concurrent service enforces the same rules.

The consolidation suite guards the seven-document inventory, obsolete document references, internal links and anchors, local schema dependencies, excluded legacy contracts and inline-only optional ranking candidates. Review evidence is in `reviews/`; only `docs/` and the current schemas define the specification.
