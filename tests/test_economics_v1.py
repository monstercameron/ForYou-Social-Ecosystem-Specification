"""Fee schedule 1, settlement, distribution, retention and key checks.

Many tests reproduce attacks found in review and assert that they fail.
"""
import copy
import json
import re
import unittest

import jsonschema

import economics_model as em
from bitcoin_address_reference import bitcoin_script
from test_operations_profile import structural
from test_security_profile import PROVIDER, SCHEMA, did

X = em.build_example()
BTC, ETH = X['genesis_manifest']['fee_schedules']
POLICY = X['genesis_manifest']['distribution_policy']
M = sorted(did(m) for m in em.MONITORS)
Q = ('2027-01-01T00:00:00Z', '2027-04-01T00:00:00Z')
Q2 = ('2027-04-01T00:00:00Z', '2027-07-01T00:00:00Z')
NOW = '2027-02-01T00:00:00Z'
A, B, C = did(PROVIDER), did(em.PROVIDER_B), did(em.PROVIDER_NEXT)
NET = 'bitcoin-mainnet'
MIN = 10000000  # minimum deposit and payout in msat


def day(n, hour=0):
    return '2027-01-%02dT%02d:00:00Z' % (n, hour)


class FeeScheduleTests(unittest.TestCase):
    def setUp(self):
        self.trust = em.Trust([em.key_certificate()])

    def test_published_example_is_reproducible(self):
        self.assertEqual(json.loads(em.EXAMPLE.read_text(encoding='utf-8')), X)
        bitcoin_script(em.RECIPIENTS['bitcoin-mainnet'])  # raises ValueError on a bad Bech32/Base58 checksum

    def test_schedule_1_amounts(self):
        self.assertEqual((BTC['base_fee_base_units'], BTC['per_kib_fee_base_units']), ('0', '136'))
        self.assertEqual((ETH['base_fee_base_units'], ETH['per_kib_fee_base_units']), ('0', '48900000000'))
        for n, units in [(1, 1), (1024, 1), (1025, 2), (4096, 4), (4097, 5), (1048576, 1024)]:
            self.assertEqual(em.fee(BTC, n), 136 * units)
            self.assertEqual(em.fee(ETH, n), 48900000000 * units)
        text = (em.ROOT / 'docs/03-economics.md').read_text(encoding='utf-8')
        self.assertIn('| `bitcoin-mainnet` | msat | 0 | 136 |', text)
        self.assertIn('| `ethereum-mainnet` | wei | 0 | 48900000000 |', text)

    def test_only_the_release_threshold_approves_a_schedule(self):
        for schedule, approval in zip(X['genesis_manifest']['fee_schedules'], X['genesis_manifest']['fee_schedule_approvals']):
            structural('FeeSchedule', schedule)
            structural('FeeScheduleApproval', approval)
            em.check_approval(schedule, approval, self.trust)
        outsiders = [em.FOUNDATION, em.PROVIDER_B, PROVIDER, em.MONITORS[0]]
        for signers in (outsiders, em.RELEASE_KEYS[:3], em.RELEASE_KEYS[:3] + [em.FOUNDATION]):
            with self.assertRaises(ValueError):  # not the Foundation, not providers, not three of five release keys
                em.check_approval(BTC, em.approve(BTC, signers=signers), self.trust)
        with self.assertRaises(ValueError):
            em.check_approval(BTC, em.approve(ETH), self.trust)
        with self.assertRaises(ValueError):
            em.check_approval(dict(BTC, per_kib_fee_base_units='1'), em.approve(BTC), self.trust)
        with self.assertRaises(ValueError):  # less than 60 days of notice
            em.check_approval(BTC, em.approve(BTC, at='2026-12-01T00:00:00Z'), self.trust)
        with self.assertRaises(ValueError):  # revision 1 cannot be a drift replacement
            em.check_approval(BTC, em.approve(BTC, drift=True), self.trust)

    def revision(self, rate, base=0, approved='2027-04-01T00:00:00Z', drift=False, effective='2027-07-01T00:00:00Z', number=2):
        s = em.make_schedule(NET, rate, revision=number, effective_at=effective, expires_at='2028-07-01T00:00:00Z', base=base)
        return s, em.approve(s, at=approved, drift=drift)

    def test_revision_bound_holds_even_when_approved(self):
        for rate, base in ((68, 0), (136, 0), (272, 0), (136, 100), (100, 36)):  # a base fee may be introduced within the bound
            s, a = self.revision(rate, base)
            em.check_approval(s, a, self.trust, previous=BTC)
        for rate, base in ((67, 0), (273, 0), (100000, 0), (136, 137), (1, 135)):
            s, a = self.revision(rate, base)
            with self.assertRaises(ValueError):
                em.check_approval(s, a, self.trust, previous=BTC)
        s, a = self.revision(136)
        with self.assertRaises(ValueError):  # predecessor required
            em.check_approval(s, a, self.trust)
        with self.assertRaises(ValueError):  # wrong network predecessor
            em.check_approval(s, a, self.trust, previous=ETH)

    def test_revisions_cannot_be_stacked_in_time(self):
        """Reproduces the reviewed attack: ten doublings approved on one day."""
        s2, a2 = self.revision(272, approved='2027-06-10T00:00:00Z', drift=True, effective='2027-06-24T00:00:00Z')
        em.check_approval(s2, a2, self.trust, previous=BTC)  # one drift doubling, 174 days after revision 1
        s3 = em.make_schedule(NET, 544, revision=3, effective_at='2027-06-24T00:00:01Z', expires_at='2028-01-01T00:00:00Z')
        with self.assertRaises(ValueError):  # the next one a second later
            em.check_approval(s3, em.approve(s3, at='2027-06-10T00:00:00Z', drift=True), self.trust, previous=s2)
        s3 = em.make_schedule(NET, 544, revision=3, effective_at='2027-07-24T00:00:00Z', expires_at='2028-01-01T00:00:00Z')
        with self.assertRaises(ValueError):  # approved before its predecessor took effect
            em.check_approval(s3, em.approve(s3, at='2027-06-10T00:00:00Z', drift=True), self.trust, previous=s2)
        em.check_approval(s3, em.approve(s3, at='2027-07-01T00:00:00Z', drift=True), self.trust, previous=s2)
        early, approval = self.revision(200, effective='2027-03-15T00:00:00Z', approved='2027-01-05T00:00:00Z')
        with self.assertRaises(ValueError):  # without drift, 90 days must pass between activations
            em.check_approval(early, approval, self.trust, previous=BTC)

    def test_drift_rule(self):
        s, late = self.revision(200, approved='2027-06-10T00:00:00Z')
        with self.assertRaises(ValueError):  # 21 days of notice without the drift flag
            em.check_approval(s, late, self.trust, previous=BTC)
        s, flagged = self.revision(200, approved='2027-06-10T00:00:00Z', drift=True)
        em.check_approval(s, flagged, self.trust, previous=BTC)
        self.assertFalse(em.drift_allows_revision([100] * 365))
        self.assertFalse(em.drift_allows_revision([49] * 29 + [100] + [49] * 29))
        self.assertTrue(em.drift_allows_revision([100] * 10 + [49] * 30))
        self.assertTrue(em.drift_allows_revision([201] * 30))
        self.assertFalse(em.drift_allows_revision([50] * 60 + [200] * 60))

    def test_schedule_stays_in_force_until_replaced(self):
        later = em.make_schedule(NET, 200, revision=2, effective_at='2028-01-01T00:00:00Z', expires_at='2028-07-01T00:00:00Z')
        schedules = [BTC, ETH, later]
        self.assertEqual(em.in_force(schedules, NET, '2027-12-31T23:59:59Z'), BTC)  # past expires_at, no successor yet
        self.assertEqual(em.in_force(schedules, NET, '2028-01-01T00:00:00Z'), later)
        self.assertEqual(em.in_force(schedules, 'ethereum-mainnet', '2030-01-01T00:00:00Z'), ETH)
        with self.assertRaises(ValueError):
            em.in_force(schedules, NET, '2026-12-31T23:59:59Z')
        both = {BTC['schedule_id'], later['schedule_id']}
        self.assertEqual(em.schedules_in_force_during(schedules, NET, '2028-01-01T00:30:00Z'), both)  # an open quote's schedule
        self.assertEqual(em.schedules_in_force_during(schedules, NET, '2028-01-01T01:00:00Z'), {later['schedule_id']})

    def test_schema_bounds(self):
        with self.assertRaises(jsonschema.ValidationError):
            structural('FeeSchedule', dict(BTC, per_kib_fee_base_units='0'))
        with self.assertRaises(jsonschema.ValidationError):
            structural('FeeSchedule', dict(BTC, profile_minor=1))
        structural('FeeSchedule', dict(BTC, base_fee_base_units='5', per_kib_fee_base_units='0'))
        ops = json.loads((em.ROOT / 'schemas/operations.schema.json').read_text(encoding='utf-8'))
        self.assertEqual(ops['$defs']['FeeQuote']['properties']['billable_bytes']['maximum'], 1048576)
        self.assertEqual(SCHEMA['$defs']['SubmissionReceipt']['properties']['network'], {'enum': [NET, 'ethereum-mainnet']})

    def test_custody_cap(self):
        cap = 136 * 1000000
        self.assertTrue(em.deposit_allowed(BTC, 0, 0, cap))
        self.assertFalse(em.deposit_allowed(BTC, 0, 0, cap + 1))
        self.assertFalse(em.deposit_allowed(BTC, cap - 10, 5, 6))
        self.assertTrue(em.deposit_allowed(dict(BTC, base_fee_base_units='10', per_kib_fee_base_units='0'), 0, 0, 10 * 1000000))
        self.assertEqual(48900000000 * 1000000, 489 * 10 ** 14)  # 0.0489 ETH


class ReleaseAndFoundationKeyTests(unittest.TestCase):
    def test_genesis_manifest(self):
        g = X['genesis_manifest']
        structural('GenesisManifest', g)
        self.assertEqual(len(em.check_genesis(g)), 5)
        for threshold in (1, 3):  # three of five is below two-thirds
            with self.assertRaises(ValueError):
                em.check_genesis(dict(g, release_threshold=threshold))
        with self.assertRaises(ValueError):
            em.check_genesis(em.genesis_manifest(g['foundation_key_certificates'][0], g['fee_schedules'], g['fee_schedule_approvals'],
                                                 g['distribution_policy'], signers=em.RELEASE_KEYS[:3]))
        changed = copy.deepcopy(g)
        changed['fee_schedules'][0]['per_kib_fee_base_units'] = '1'
        with self.assertRaises(ValueError):
            em.check_genesis(changed)
        self.assertTrue(em.valid_key_set(set(range(5)), 4))
        self.assertFalse(em.valid_key_set(set(range(4)), 4))
        self.assertTrue(em.valid_key_set(set(range(6)), 4))
        self.assertFalse(em.valid_key_set(set(range(7)), 4))

    def test_release_key_set_changes_only_by_the_previous_threshold(self):
        ids = {did(k) for k in em.RELEASE_KEYS}
        new_keys = em.RELEASE_KEYS[1:] + em.MONITORS[:2]  # six keys
        update = em.key_set_update(1, new_keys, 4, '2027-06-01T00:00:00Z')
        structural('ReleaseKeySetUpdate', update)
        timeline = em.apply_key_set_updates(ids, 4, [update])
        self.assertEqual(em.key_set_at(timeline, '2027-05-31T23:59:59Z'), (ids, 4))
        self.assertEqual(em.key_set_at(timeline, '2027-06-01T00:00:00Z'), ({did(k) for k in new_keys}, 4))
        for bad in (em.key_set_update(1, new_keys, 4, NOW, signers=[em.FOUNDATION, em.PROVIDER_B, PROVIDER, em.PROVIDER_NEXT]),
                    em.key_set_update(2, new_keys, 4, NOW),  # skipped sequence
                    em.key_set_update(1, new_keys, 3, NOW),  # below two-thirds
                    em.key_set_update(1, new_keys[:4], 4, NOW)):  # fewer than five keys
            with self.assertRaises(ValueError):
                em.apply_key_set_updates(ids, 4, [bad])
        second = em.key_set_update(2, em.RELEASE_KEYS, 4, '2027-09-01T00:00:00Z', signers=new_keys[:4], previous=update)
        em.apply_key_set_updates(ids, 4, [update, second])
        unlinked = em.key_set_update(2, em.RELEASE_KEYS, 4, '2027-09-01T00:00:00Z', signers=new_keys[:4])
        with self.assertRaises(ValueError):  # not chained to the first update
            em.apply_key_set_updates(ids, 4, [update, unlinked])
        rival = em.key_set_update(1, em.RELEASE_KEYS[:4] + em.MONITORS[:1], 4, '2027-06-01T00:00:00Z')
        with self.assertRaises(ValueError):  # two different updates with the same sequence fork the root of trust
            em.apply_key_set_updates(ids, 4, [update, rival])

    def test_objects_signed_under_an_earlier_key_set_stay_valid(self):
        """Reproduces the reviewed break: rotation must not invalidate earlier approvals and certificates."""
        new_keys = em.RELEASE_KEYS[3:] + em.MONITORS[:3]
        carried = [em.key_certificate(), em.approve(BTC), POLICY]
        update = em.key_set_update(1, new_keys, 4, '2027-06-01T00:00:00Z', prior_objects=carried)
        structural('ReleaseKeySetUpdate', update)
        trust = em.Trust([em.key_certificate()], updates=[update])
        em.check_approval(BTC, em.approve(BTC), trust)  # approved in 2026 by the genesis set and carried over
        em.check_policy(POLICY, trust)
        with self.assertRaises(ValueError):  # the retired set backdates an approval that the update did not carry over
            em.check_approval(ETH, em.approve(ETH), trust)
        hostile = em.key_certificate(foundation=em.PROVIDER_NEXT, issued_at='2027-01-01T00:00:00Z', valid_from='2027-02-01T00:00:00Z', valid_until='2028-02-01T00:00:00Z')
        with self.assertRaises(ValueError):  # nor can it certify a hostile Foundation key after the fact
            em.Trust([em.key_certificate(), hostile], updates=[update])
        s = em.make_schedule(NET, 200, revision=2, effective_at='2027-12-01T00:00:00Z', expires_at='2028-06-01T00:00:00Z')
        with self.assertRaises(ValueError):  # the old set can no longer approve
            em.check_approval(s, em.approve(s, at='2027-09-01T00:00:00Z'), trust, previous=BTC)
        em.check_approval(s, em.approve(s, at='2027-09-01T00:00:00Z', signers=new_keys[:4]), trust, previous=BTC)

    def test_certificate_rules(self):
        cert = X['genesis_manifest']['foundation_key_certificates'][0]
        structural('FoundationKeyCertificate', cert)
        ids = set(X['genesis_manifest']['release_key_ids'])
        em.check_certificate(cert, ids, genesis=True)
        for bad in (em.key_certificate(signers=em.RELEASE_KEYS[:3]), em.key_certificate(signers=[em.FOUNDATION, em.PROVIDER_B, PROVIDER, em.PROVIDER_NEXT]),
                    em.key_certificate(valid_until='2028-10-01T00:00:00Z'), dict(cert, release_signatures=cert['release_signatures'][:1] * 4)):
            with self.assertRaises(ValueError):
                em.check_certificate(bad, ids, genesis=True)
        changed = copy.deepcopy(cert)
        changed['recipients']['ethereum-mainnet'] = '0x' + '11' * 20
        with self.assertRaises(ValueError):
            em.check_certificate(changed, ids, genesis=True)
        # A later certificate, and so any recipient change, needs 30 days' notice, whatever the stated reason.
        rushed = em.key_certificate(foundation=em.PROVIDER_NEXT, issued_at='2027-02-01T00:00:00Z', valid_from='2027-02-02T00:00:00Z', valid_until='2028-02-01T00:00:00Z')
        with self.assertRaises(ValueError):
            em.Trust([cert, rushed])
        em.Trust([cert, em.key_certificate(foundation=em.PROVIDER_NEXT, issued_at='2027-02-01T00:00:00Z', valid_from='2027-03-03T00:00:00Z', valid_until='2028-03-01T00:00:00Z')])

    def vault_world(self):
        w = em.build_world()
        vault = em.Vault(w['committee'])
        receipts = []
        for r in w['receipts'][:3]:
            index = next(i for i, leaf in enumerate(w['leaves']) if leaf['receipt_hash'] == em.object_hash(r))
            receipts.append(vault.put(r, em.make_proof(w['claim'], w['leaves'], index, w['witnesses']), '2027-01-07T00:00:00Z'))
        return w, vault, receipts

    def test_open_key_renewal_and_signed_time(self):
        w, vault, receipts = self.vault_world()
        a = receipts[0]
        first = w['trust'].certificates[0]
        renewed = em.key_certificate(issued_at='2027-08-01T00:00:00Z', valid_from='2027-10-01T00:00:00Z', valid_until='2028-10-01T00:00:00Z')
        em.Trust([first, renewed]).verify_foundation(a, a['stored_at'], 'vault-receipt')
        late = dict(em.without(a, 'foundation_signature'), stored_at='2027-11-01T00:00:00Z')
        late['foundation_signature'] = em.sign(em.FOUNDATION, 'vault-receipt', late)
        with self.assertRaises(ValueError):  # signed time outside every certificate
            w['trust'].verify_foundation(late, late['stored_at'], 'vault-receipt')

    def test_closure_rules(self):
        w, vault, receipts = self.vault_world()
        cert, log, a = w['trust'].certificates[0], vault.log, receipts[0]
        size = len(log.entries)
        head = em.log_head(log, '2027-01-20T00:00:00Z')
        structural('FoundationLogHead', head)
        closure = em.key_closure(em.FOUNDATION, NOW, log)
        structural('FoundationKeyClosure', closure)
        closed = em.Trust([cert], [closure], heads=[head])
        proof = log.proof(a, size)
        structural('FoundationLogProof', proof)
        closed.verify_foundation(a, a['stored_at'], 'vault-receipt', proof)
        with self.assertRaises(ValueError):  # no proof
            closed.verify_foundation(a, a['stored_at'], 'vault-receipt')
        with self.assertRaises(ValueError):  # proof against another size
            closed.verify_foundation(a, a['stored_at'], 'vault-receipt', log.proof(a, size - 1))
        forged = dict(em.without(a, 'foundation_signature'), message_id='fy1:' + 'ee' * 32)
        forged['foundation_signature'] = em.sign(em.FOUNDATION, 'vault-receipt', forged)
        with self.assertRaises(ValueError):  # the leaked key backdates an object; it is not in the closed log
            closed.verify_foundation(forged, forged['stored_at'], 'vault-receipt', proof)
        # A leaked key cannot veto its own closure with a larger (possibly backdated) head: the closure stands,
        # and the larger head is evidence for monitors to publish.
        shrunk = em.Trust([cert], [em.key_closure(em.FOUNDATION, NOW, log, size=1)], heads=[head])
        self.assertEqual(shrunk.closure_evidence(), [head])
        self.assertEqual(closed.closure_evidence(), [])
        with self.assertRaises(ValueError):
            shrunk.verify_foundation(receipts[2], receipts[2]['stored_at'], 'vault-receipt', log.proof(receipts[2], size))
        with self.assertRaises(ValueError):  # a closure needs the threshold
            em.Trust([cert], [em.key_closure(em.FOUNDATION, NOW, log, signers=em.RELEASE_KEYS[:3])])
        with self.assertRaises(ValueError):  # the embedded head must be signed by the closed key
            em.Trust([cert], [em.key_closure(em.FOUNDATION, NOW, log, head=em.log_head(log, NOW, key=em.PROVIDER_B))])
        voiding = em.Trust([cert], [em.key_closure(em.FOUNDATION, NOW, log, voided=[em.object_hash(a)])], heads=[head])
        with self.assertRaises(ValueError):
            voiding.verify_foundation(a, a['stored_at'], 'vault-receipt', proof)
        voiding.verify_foundation(receipts[1], receipts[1]['stored_at'], 'vault-receipt', log.proof(receipts[1], size))
        for entry in log.entries:
            structural('FoundationLogEntry', entry)
        hashes = [e['object_hash'] for e in log.entries]
        self.assertTrue(em.heads_conflict(hashes, em.log_head(log, NOW, size=2), ['00' * 32] + hashes[1:], head))
        self.assertFalse(em.heads_conflict(hashes, em.log_head(log, NOW, size=2), hashes, head))

    def test_deposits_survive_a_certificate_lapse_but_not_a_closure(self):
        w = em.build_world()
        chain, cert = em.Chain(), w['trust'].certificates[0]
        chain.deposit(A, NET, 10000, at='2027-12-01T00:00:00Z')  # after valid_until, key still open
        self.assertEqual(chain.deposited(A, NET, w['trust']), MIN)
        chain.deposit(A, NET, 10000, at='2026-09-15T00:00:00Z')  # before the certificate's valid_from
        self.assertEqual(chain.deposited(A, NET, w['trust']), MIN)
        closed = em.Trust([cert], [em.key_closure(em.FOUNDATION, '2027-11-01T00:00:00Z', em.Vault(w['committee']).log)])
        self.assertEqual(chain.deposited(A, NET, closed), 0)


class SettlementTests(unittest.TestCase):
    """One settlement rule: a quorum of more than two-thirds of the committee monitors, each auditing from public data."""

    def setUp(self):
        self.w = em.build_world()
        self.monitors, self.committee, self.chain, self.trust = self.w['monitors'], self.w['committee'], self.w['chain'], self.w['trust']
        self.decl = self.w['decl_a']['declaration_id']
        self.decl_c = em.retention_declaration(em.PROVIDER_NEXT, em.YEAR, '2026-12-01T00:00:00Z')
        for m in self.monitors:
            m.register_declaration(self.decl_c)

    def claim(self, receipts, d=14, previous='claim2', key=PROVIDER, decl=None, **kw):
        prev = self.w[previous] if isinstance(previous, str) else previous
        return em.make_claim(key, NET, [em.leaf_of(r) for r in receipts], kw.get('start', day(d)), kw.get('end', day(d + 1)),
                             self.decl if decl is None else decl, previous=prev, succession=kw.get('succession'))

    def rotate(self, at, register=True, new=None):
        """A key succession to the next provider key at `at`, with the declaration the new key signs for it."""
        new = em.PROVIDER_NEXT if new is None else new
        s, d = em.key_succession(PROVIDER, new, at), em.retention_declaration(new, em.YEAR, at)
        for m in self.monitors:
            m.register_declaration(d)
            if register:
                m.register_succession(s)
        return s, d['declaration_id']

    def receipts(self, texts, d=14, key=PROVIDER, issued=None):
        return [em.make_receipt(self.w['btc'], t, issued or day(d, 6), key=key) for t in texts]

    def audit(self, claim, leaves, at=NOW, monitors=None):
        return em.committee_audit(self.monitors if monitors is None else monitors, claim, leaves, at)

    def reason(self, claim, leaves, at=NOW):
        witnesses, refusals = self.audit(claim, leaves, at)
        self.assertEqual((len(witnesses), len(refusals)), (0, 5))
        for r in refusals:
            structural('SettlementRefusal', r)
        reasons = {r['reason'] for r in refusals}
        self.assertEqual(len(reasons), 1)  # independent monitors reach the same verdict from public data
        return reasons.pop()

    def state(self, receipt, claim, leaves, witnesses, **kw):
        index = next(i for i, leaf in enumerate(leaves) if leaf['receipt_hash'] == em.object_hash(receipt))
        return em.receipt_state(receipt, em.make_proof(claim, leaves, index, witnesses), kw.pop('committee', self.committee), **kw)

    def test_structures(self):
        for name, key in (('SettlementProof', 'settlement_proof'), ('SettlementClaim', 'settlement_claim'), ('SettlementClaim', 'second_claim'),
                          ('SettlementRefusal', 'settlement_refusal_example'), ('VaultReceipt', 'vault_receipt'), ('VaultStatus', 'vault_status')):
            structural(name, X[key])
        for wit in X['second_claim_witnesses']:
            structural('SettlementWitness', wit)
        structural('SettlementClaimsPage', {'claims': [self.w['claim'], self.w['claim2']]})
        structural('SettlementLeavesPage', {'claim_id': self.w['claim']['claim_id'], 'offset': 0, 'leaves': self.w['leaves']})
        structural('SettlementWitnessesPage', {'witnesses': self.w['witnesses']})
        structural('MonitorWitnessesPage', {'witnesses': self.w['witnesses'][:1], 'refusals': [X['settlement_refusal_example']], 'holds': [], 'claims': [self.w['claim']]})
        structural('EquivocationsPage', {'proofs': [em.equivocation_proof(self.w['claim2'], self.w['claim2'], self.w['claim'])]})
        structural('EquivocationProof', dict(em.equivocation_proof(self.w['claim'], self.w['claim']), predecessor=None))
        structural('EquivocationProof', dict(em.equivocation_proof(self.w['claim2'], self.w['claim2'], self.w['claim']), successions=[X['key_succession']]))
        structural('VaultDelivery', {'message': {}, 'proof': X['settlement_proof']})
        with self.assertRaises(jsonschema.ValidationError):
            structural('SettlementRefusal', dict(X['settlement_refusal_example'], reason='content'))
        self.assertNotIn('content', em.REFUSAL_REASONS)
        self.assertEqual(set(self.w['leaves'][0]), {'receipt_hash', 'schedule_id', 'amount_base_units', 'issued_at'})
        for wit in self.w['witnesses']:
            self.assertGreaterEqual(em.seconds(wit['witnessed_at']), em.seconds(wit['period_end']))
        ops = json.loads((em.ROOT / 'schemas/operations.schema.json').read_text(encoding='utf-8'))['$defs']
        for gone in ('SettlementAttestation', 'SettlementRejection', 'SettlementSubmission', 'SettlementResult'):
            self.assertNotIn(gone, ops)  # the Foundation has no settlement objects at all

    def test_sum_tree_paths_prove_inclusion_and_amount(self):
        base = self.w['leaves']
        for count in range(1, 6):
            leaves = base[:count]
            root, total = em.tree_root(leaves)
            self.assertEqual(total, sum(int(leaf['amount_base_units']) for leaf in leaves))
            for index in range(count):
                path = em.audit_path(index, leaves)
                self.assertEqual(em.root_from_path(leaves[index], index, count, path), (root, total))
                self.assertNotEqual(em.root_from_path(dict(leaves[index], amount_base_units='1'), index, count, path), (root, total))
                with self.assertRaises(ValueError):
                    em.root_from_path(leaves[index], index, count, path + [{'hash': '00' * 32, 'sum': '0'}])
                if path:
                    lowered = copy.deepcopy(path)
                    lowered[0]['sum'] = str(max(0, int(lowered[0]['sum']) - 1))
                    self.assertNotEqual(em.root_from_path(leaves[index], index, count, lowered)[0], root)
                    with self.assertRaises(ValueError):
                        em.root_from_path(leaves[index], index, count, [dict(path[0], sum='-1')] + path[1:])

    def test_deposits_count_only_with_commitment_recipient_and_minimum(self):
        chain = em.Chain()
        chain.deposit(A, NET, 10000)
        chain.deposit(A, NET, 9999)  # below the minimum deposit
        chain.deposit(B, NET, 50000)  # another provider's commitment
        chain.deposit(A, NET, 50000, recipient='bc1qsomeoneelse000000000000000000000000000')
        chain.deposit(A, NET, 50000, data='00' * 32)
        chain.deposit(A, 'ethereum-mainnet', 10 ** 15)
        self.assertEqual(chain.deposited(A, NET, self.trust), MIN)
        self.assertEqual(chain.deposited(A, 'ethereum-mainnet', self.trust), 10 ** 15)
        self.assertNotEqual(em.deposit_commitment(A, NET), em.deposit_commitment(A, 'ethereum-mainnet'))

    def test_monitors_refuse_only_for_listed_reasons(self):
        good = self.receipts(['third'])
        claim, leaves = self.claim(good)
        self.assertEqual(self.reason(dict(claim, total_base_units='1'), leaves), 'bad_signature')
        c, l = self.claim(self.receipts(['third'], issued=day(12, 18)), start=day(12, 12), end=day(13, 12))
        self.assertEqual(self.reason(c, l), 'bad_period')  # overlaps the previous period
        c, l = self.claim(good, end='2027-01-15T00:00:01Z')
        self.assertEqual(self.reason(c, l), 'bad_period')  # longer than 24 hours
        self.assertEqual(self.reason(claim, leaves, at=day(14, 12)), 'bad_period')  # period not over yet
        self.assertEqual(self.reason(claim, leaves, at='2027-04-15T00:00:01Z'), 'bad_period')  # more than 90 days late
        c, l = self.claim(self.receipts(['third'], issued=day(15)))
        self.assertEqual(self.reason(c, l), 'bad_leaf')  # issued outside the period
        odd = [dict(em.leaf_of(good[0]), amount_base_units='137')]
        c, l = em.make_claim(PROVIDER, NET, odd, day(14), day(15), self.decl, previous=self.w['claim2'])
        self.assertEqual(self.reason(c, l), 'bad_leaf')  # not a possible fee under the schedule
        c, l = self.claim(good, d=16, previous=claim)  # its predecessor was never witnessed
        self.assertEqual(self.reason(c, l), 'bad_chain')
        big = self.receipts(['w' * 900000 + str(n) for n in range(90)])
        c, l = self.claim(big)
        self.assertEqual(self.reason(c, l), 'unfunded')
        self.chain.deposit(A, NET, 20000, at='2027-01-30T00:00:00Z')
        witnesses, refusals = self.audit(c, l)  # the same claim, unchanged, after a deposit
        self.assertEqual((len(witnesses), len(refusals)), (5, 0))
        self.assertEqual(int(witnesses[0]['credit_base_units']), 3 * MIN - int(c['cumulative_base_units']))
        self.assertEqual(self.state(big[0], c, l, witnesses), 'settled')

    def test_the_foundation_has_no_vote(self):
        """The Foundation key cannot settle, block or unsettle a claim."""
        good = self.receipts(['third'])
        claim, leaves = self.claim(good)
        forged = dict(em.without(self.w['witnesses2'][0], 'witness_signature'), witness_id=did(em.FOUNDATION))
        forged.update({k: claim[k] for k in em.WITNESSED_FIELDS})
        forged['witness_signature'] = em.sign(em.FOUNDATION, 'settlement-witness', forged)
        self.assertEqual(self.state(good[0], claim, leaves, [forged] * 5), 'unsettled')
        witnesses, _ = self.audit(claim, leaves)
        self.assertEqual(self.state(good[0], claim, leaves, witnesses), 'settled')  # no Foundation object is involved at any step
        text = (em.ROOT / 'docs/03-economics.md').read_text(encoding='utf-8')
        self.assertIn('has no vote', text)

    def test_a_claim_names_its_declaration_and_only_the_claim_decides(self):
        short = em.retention_declaration(PROVIDER, em.YEAR, '2027-01-20T00:00:00Z')
        for m in self.monitors:
            m.register_declaration(short)
        r = self.receipts(['under ten years'])
        c, l = self.claim(r, decl=short['declaration_id'])  # the short declaration takes effect after this period starts
        self.assertEqual(self.reason(c, l), 'bad_period')
        with self.assertRaises(em.Rejected) as caught:
            self.monitors[0].check(c, l, NOW)
        self.assertTrue(caught.exception.provable)  # the named object itself shows the fault
        c, l = self.claim(r)
        self.assertEqual(len(self.audit(c, l)[0]), 5)
        later = self.receipts(['after the change'], d=21)
        # A declaration takes effect on the chain when a claim first names it: publishing it alone changes nothing,
        # so no later-signed declaration can make this claim invalid.
        keep, kl = self.claim(later, d=21, previous=c)
        self.assertIsInstance(self.monitors[0].check(keep, kl, day(22, 12)), int)
        c2, l2 = self.claim(later, d=21, previous=c, decl=short['declaration_id'])
        self.assertEqual(len(self.audit(c2, l2, day(22, 12))[0]), 5)
        # Another provider's declaration cannot be named, and an unknown one proves nothing.
        other, ol = self.claim(self.receipts(['borrowed'], d=22), d=22, previous=c2, decl=self.w['decl_b']['declaration_id'])
        for m in self.monitors:
            m.register_declaration(self.w['decl_b'])
        with self.assertRaises(em.Rejected) as caught:
            self.monitors[0].check(other, ol, day(23, 12))
        self.assertTrue(caught.exception.provable)
        unknown, ul = self.claim(self.receipts(['unknown'], d=22), d=22, previous=c2, decl='fyrd2:' + 'ab' * 32)
        with self.assertRaises(em.Rejected) as caught:
            self.monitors[0].check(unknown, ul, day(23, 12))
        self.assertFalse(caught.exception.provable)

    def test_declaration_cannot_be_backdated_over_claimed_periods(self):
        backdated = em.retention_declaration(PROVIDER, em.YEAR, day(8))  # published later, dated between two claimed periods
        for m in self.monitors:
            m.register_declaration(backdated)
        c, l = self.claim(self.receipts(['next']), decl=backdated['declaration_id'])
        self.assertEqual(self.reason(c, l), 'bad_period')

    def test_duplicate_receipts_and_shared_leaves(self):
        dup = self.w['receipts2']
        c, l = em.make_claim(PROVIDER, NET, [dict(em.leaf_of(dup[0]), issued_at=day(14, 6))], day(14), day(15), self.decl, previous=self.w['claim2'])
        self.assertEqual(self.reason(c, l), 'duplicate_receipt')
        r1 = X['receipt']
        r2 = dict(r1, message_id='fy1:' + 'ab' * 32)  # a second receipt trying to ride on the first one's paid leaf
        r2['provider_signature'] = em.sign(PROVIDER, 'receipt', em.without(r2, 'provider_signature'))
        proof = X['settlement_proof']
        self.assertEqual(em.receipt_state(r1, proof, self.committee), 'settled')
        self.assertEqual(em.receipt_state(r2, proof, self.committee), 'unsettled')

    def test_gaps_and_key_succession(self):
        r = self.receipts(['after a pause'], d=25)
        c, l = self.claim(r, d=25)
        self.assertEqual(len(self.audit(c, l, day(26, 12))[0]), 5)
        r2 = self.receipts(['new key'], d=27, key=em.PROVIDER_NEXT)
        succession, decl = self.rotate(day(26), register=False)
        c2, l2 = self.claim(r2, d=27, previous=c, key=em.PROVIDER_NEXT, decl=decl, succession=succession)
        self.assertEqual(self.reason(c2, l2, at=day(28, 12)), 'unknown_provider_key')  # the named succession is not yet fetched
        for m in self.monitors:
            m.register_succession(succession)
        unnamed, ul = self.claim(r2, d=27, previous=c, key=em.PROVIDER_NEXT, decl=decl)  # another key, naming no succession
        with self.assertRaises(em.Rejected) as caught:
            self.monitors[0].check(unnamed, ul, day(28, 12))
        self.assertEqual((caught.exception.reason, caught.exception.provable), ('unknown_provider_key', True))
        inherited, il = self.claim(r2, d=27, previous=c, key=em.PROVIDER_NEXT, succession=succession)  # the old key's declaration
        with self.assertRaises(em.Rejected) as caught:
            self.monitors[0].check(inherited, il, day(28, 12))
        self.assertEqual((caught.exception.reason, caught.exception.provable), ('bad_period', True))
        witnesses, refusals = self.audit(c2, l2, day(28, 12))
        self.assertEqual((len(witnesses), len(refusals)), (5, 0))  # credit deposited under the old key carries over
        r3 = self.receipts(['second claim of the new key'], d=28, key=em.PROVIDER_NEXT)
        again, al = self.claim(r3, d=28, previous=c2, key=em.PROVIDER_NEXT, decl=decl, succession=succession)
        with self.assertRaises(em.Rejected) as caught:  # only the first claim of a new key names a succession
            self.monitors[0].check(again, al, day(29, 12))
        self.assertTrue(caught.exception.provable)
        c3, l3 = self.claim(r3, d=28, previous=c2, key=em.PROVIDER_NEXT, decl=decl)
        self.assertEqual(len(self.audit(c3, l3, day(29, 12))[0]), 5)
        back, bl = self.claim(self.receipts(['old key again'], d=29), d=29, previous=c3)  # the chain now belongs to the new key
        with self.assertRaises(em.Rejected) as caught:
            self.monitors[0].check(back, bl, day(30, 12))
        self.assertEqual((caught.exception.reason, caught.exception.provable), ('unknown_provider_key', True))
        with self.assertRaises(ValueError):
            self.monitors[0].register_succession(em.key_succession(PROVIDER, em.MONITORS[0], '2027-06-01T00:00:00Z'))

    def test_backdated_or_cheap_schedule_claims_fail(self):
        old = em.make_schedule(NET, 1, effective_at='2017-01-01T00:00:00Z', expires_at='2017-07-01T00:00:00Z')
        monitors = [em.Monitor(k, self.trust, self.chain, [old, self.w['btc'], self.w['eth']]) for k in em.MONITORS]
        for m in monitors:
            m.register_declaration(self.decl_c)
        self.chain.deposit(C, NET, 10000)
        cheap = [em.make_receipt(old, 'cheap', day(14, 6), key=em.PROVIDER_NEXT)]
        c, l = em.make_claim(em.PROVIDER_NEXT, NET, [em.leaf_of(r) for r in cheap], day(14), day(15), self.decl_c['declaration_id'])
        self.assertEqual({r['reason'] for r in self.audit(c, l, monitors=monitors)[1]}, {'bad_leaf'})  # that schedule was not in force
        ancient = [em.make_receipt(old, 'ancient', '2017-03-01T06:00:00Z', key=em.PROVIDER_NEXT)]
        c, l = em.make_claim(em.PROVIDER_NEXT, NET, [em.leaf_of(r) for r in ancient], '2017-03-01T00:00:00Z', '2017-03-02T00:00:00Z', self.decl_c['declaration_id'])
        self.assertEqual({r['reason'] for r in self.audit(c, l, monitors=monitors)[1]}, {'bad_period'})  # a first claim cannot reach back years

    def test_settlement_needs_a_quorum_of_the_current_committee(self):
        claim, leaves, receipt, witnesses = self.w['claim2'], self.w['leaves2'], self.w['receipts2'][0], self.w['witnesses2']
        self.assertEqual(em.quorum(range(5)), 4)
        self.assertEqual(em.quorum(range(7)), 5)
        self.assertEqual(em.quorum(range(6)), 5)
        self.assertEqual(self.state(receipt, claim, leaves, []), 'unsettled')
        self.assertEqual(self.state(receipt, claim, leaves, witnesses[:4]), 'settled')
        self.assertEqual(self.state(receipt, claim, leaves, witnesses[:3]), 'unsettled')  # three of five is a majority but not a quorum
        self.assertEqual(self.state(receipt, claim, leaves, [witnesses[0]] * 4), 'unsettled')  # one monitor four times
        tampered = [dict(w, credit_base_units='1') for w in witnesses]
        self.assertEqual(self.state(receipt, claim, leaves, tampered), 'unsettled')
        other = self.w['receipts'][0]
        self.assertEqual(self.state(other, self.w['claim'], self.w['leaves'], witnesses), 'unsettled')  # witnesses are for another claim
        # Retired monitors: after a committee change, their witnesses count for the 30-day handover only.
        new_committee = sorted(self.committee[3:] + [A, B, C])
        self.assertEqual(self.state(receipt, claim, leaves, witnesses, committee=new_committee), 'unsettled')
        self.assertEqual(self.state(receipt, claim, leaves, witnesses, committee=new_committee, previous_committee=self.committee, changed_at='2027-02-01T00:00:00Z'), 'settled')
        # Retired keys forging or backdating witnesses settle nothing once the handover is over.
        retired = [em.Monitor(k, self.trust, self.chain, [self.w['btc'], self.w['eth']]) for k in (em.PROVIDER_B, em.PROVIDER_NEXT, em.FOUNDATION, PROVIDER)]
        for m in retired:
            m.register_declaration(self.w['decl_a'])
            m.audit(self.w['claim'], self.w['leaves'], day(6, 12))
        forged = [m.audit(claim, leaves, day(13, 12))[1] for m in retired]
        self.assertEqual(self.state(receipt, claim, leaves, forged), 'unsettled')

    def test_one_faulty_monitor_cannot_settle_two_claims(self):
        """Reproduces the reviewed attack: X to {A,B}, Y to {C,D}, and a corrupt monitor E signs both."""
        monitors = self.primed()
        rx, ry = self.receipts(['claim x'], d=12), self.receipts(['claim y'], d=12)
        x, lx = self.claim(rx, d=12, previous='claim')
        y, ly = self.claim(ry, d=12, previous='claim')
        wx = [m.audit(x, lx, day(13, 12))[1] for m in monitors[:2]]
        wy = [m.audit(y, ly, day(13, 12))[1] for m in monitors[2:4]]
        corrupt = monitors[4]
        ex = corrupt.audit(x, lx, day(13, 12))[1]
        corrupt.witnessed.pop((A, NET, 2))  # the faulty monitor ignores "one witness per sequence"
        ey = corrupt.audit(y, ly, day(13, 12))[1]
        self.assertEqual((ex['claim_id'], ey['claim_id']), (x['claim_id'], y['claim_id']))
        self.assertEqual(self.state(rx[0], x, lx, wx + [ex]), 'unsettled')  # three of five each: no quorum for either
        self.assertEqual(self.state(ry[0], y, ly, wy + [ey]), 'unsettled')
        # Even if an honest monitor's view lets one claim reach four, the other cannot: quorums overlap in two monitors.
        for honest_extra in range(0, 3):
            pool_x = len({w['witness_id'] for w in wx + [ex]}) + honest_extra
            pool_y = 5 - 1 - 2 - honest_extra + 1
            self.assertFalse(pool_x >= 4 and pool_y >= 4)
        self.assertIn('fewer than one-third of the committee monitors are faulty', (em.ROOT / 'docs/03-economics.md').read_text(encoding='utf-8'))

    def primed(self):
        monitors = [em.Monitor(k, self.trust, self.chain, [self.w['btc'], self.w['eth']]) for k in em.MONITORS]
        for m in monitors:
            m.register_declaration(self.w['decl_a'])
            m.audit(self.w['claim'], self.w['leaves'], day(6, 12))
        return monitors

    def test_one_deposit_cannot_settle_two_chains(self):
        """Reproduces the reviewed attacks: forks shown to monitors in every order, including smaller claim IDs later."""
        forks = []
        for n in range(6):
            r = self.receipts(['fork %d' % n], d=12)
            forks.append(self.claim(r, d=12, previous='claim') + (r,))
        parent = self.w['claim']
        self.assertTrue(em.equivocation(forks[0][0], forks[1][0], parent))
        self.assertFalse(em.equivocation(forks[0][0], forks[1][0]))  # without the predecessor nothing is proven
        self.assertFalse(em.equivocation(forks[0][0], forks[0][0], parent))
        self.assertFalse(em.equivocation(forks[0][0], dict(forks[1][0], total_base_units='9'), parent))  # not actually signed
        descending = sorted(forks, key=lambda f: f[0]['claim_id'], reverse=True)

        def settled_forks(plan):
            """plan: list of (fork, monitor indexes). Returns how many forks end up with a committee majority."""
            monitors = self.primed()
            got = {}
            for fork, indexes in plan:
                for n in indexes:
                    kind, result = monitors[n].audit(fork[0], fork[1], day(13, 12))
                    if kind == 'witnessed':
                        got.setdefault(fork[0]['claim_id'], []).append(result)
            states = [self.state(fork[2][0], fork[0], fork[1], got.get(fork[0]['claim_id'], [])) for fork, _ in plan]
            return states.count('settled'), monitors

        # Scenario 1 of the review: claim A to monitors {0,1,2}, then a smaller-id claim B to {2,3,4}.
        a, b = descending[0], descending[1]
        count, monitors = settled_forks([(a, [0, 1, 2]), (b, [2, 3, 4])])
        self.assertEqual(count, 0)  # neither reaches a quorum; the equivocating provider has stalled its own chain
        self.assertTrue(monitors[2].equivocations)
        # Scenario 2: six forks in descending claim_id order to all five monitors.
        count, _ = settled_forks([(f, range(5)) for f in descending])
        self.assertEqual(count, 1)
        # Any split of two forks over five monitors settles at most one.
        for k in range(6):
            count, _ = settled_forks([(a, range(k)), (b, range(k, 5))])
            self.assertLessEqual(count, 1, k)
        # A witness, once given, is never withdrawn: a later fork cannot unsettle a settled claim.
        monitors = self.primed()
        first = [m.audit(a[0], a[1], day(13, 12))[1] for m in monitors]
        self.assertEqual(self.state(a[2][0], a[0], a[1], first), 'settled')
        later = [m.audit(b[0], b[1], '2027-02-10T00:00:00Z') for m in monitors]
        self.assertEqual({kind for kind, _ in later}, {'refused'})
        self.assertEqual({r['reason'] for _, r in later}, {'bad_chain'})
        self.assertEqual(self.state(a[2][0], a[0], a[1], first), 'settled')
        self.assertTrue(all(m.witnessed[(A, NET, 2)]['claim_id'] == a[0]['claim_id'] for m in monitors))
        # A corrected claim is allowed only where the monitor refused the first one.
        monitors = self.primed()
        bad = dict(a[0], total_base_units='1')
        self.assertEqual(monitors[0].audit(bad, a[1], day(13, 12))[0], 'refused')
        self.assertEqual(monitors[0].audit(a[0], a[1], day(13, 12))[0], 'witnessed')

    def test_equivocation_proofs_cannot_be_forged(self):
        """Reproduces the reviewed gap: anyone can sign a claim that copies an honest claim's previous_claim_id."""
        parent = self.w['claim']
        honest, _ = self.claim(self.receipts(['honest'], d=12), d=12, previous=parent)
        forged, _ = self.claim(self.receipts(['forged'], d=12, key=em.PROVIDER_B), d=12, previous=parent, key=em.PROVIDER_B)
        self.assertEqual(forged['previous_claim_id'], honest['previous_claim_id'])
        self.assertFalse(em.equivocation(honest, forged, parent))  # an unrelated key is not a proof
        succession = em.key_succession(PROVIDER, em.PROVIDER_B, day(12))  # B signs it too: the proof must still name it
        named, _ = self.claim(self.receipts(['named'], d=12, key=em.PROVIDER_B), d=12, previous=parent, key=em.PROVIDER_B, succession=succession)
        self.assertFalse(em.equivocation(honest, named, parent))  # the succession is not in the proof
        proof = em.equivocation_proof(honest, named, parent, [succession])
        structural('EquivocationProof', proof)
        self.assertTrue(em.equivocation(*proof['claims'], proof['predecessor'], proof['successions']))
        self.assertFalse(em.equivocation(honest, named, self.w['claim2'], [succession]))  # the wrong predecessor
        first, _ = self.claim(self.receipts(['first'], d=1), d=1, previous=None)
        other, _ = self.claim(self.receipts(['other'], d=1, key=em.PROVIDER_B), d=1, previous=None, key=em.PROVIDER_B)
        self.assertFalse(em.equivocation(first, other))  # sequence 1: only the same provider_id
        again, _ = self.claim(self.receipts(['again'], d=1), d=1, previous=None)
        self.assertTrue(em.equivocation(first, again))

    def test_succession_cannot_double_count_deposits_or_be_griefed(self):
        """Reproduces two reviewed attacks: succession onto a key with its own chain, and a third party's deposit blocking a rotation."""
        m = self.monitors[0]
        with self.assertRaises(ValueError):  # B has signed claims of its own chain
            m.register_succession(em.key_succession(PROVIDER, em.PROVIDER_B, '2027-02-01T00:00:00Z'))
        self.chain.deposit(C, NET, 50000)  # anyone sends a deposit carrying the new key's own commitment
        succession, decl = self.rotate(day(13))  # the succession is unaffected
        self.assertEqual(self.chain.deposited(m.line(C), NET, self.trust), MIN)  # and that deposit is not counted for the chain
        r = self.receipts(['signed by the new key'], d=14, key=em.PROVIDER_NEXT)
        c, l = self.claim(r, d=14, key=em.PROVIDER_NEXT, decl=decl, succession=succession)
        witnesses, refusals = self.audit(c, l)
        self.assertEqual((len(witnesses), len(refusals)), (5, 0))
        self.assertEqual(int(witnesses[0]['credit_base_units']), MIN - int(c['cumulative_base_units']))
        with self.assertRaises(ValueError):  # a key cannot be the successor of two keys
            m.register_succession(em.key_succession(em.PROVIDER_B, em.PROVIDER_NEXT, '2027-02-01T00:00:00Z'))
        self.chain.deposit(A, NET, 20000, at='2027-01-20T00:00:00Z')  # top-ups keep using the first key's commitment
        self.assertEqual(self.chain.deposited(m.line(C), NET, self.trust), 3 * MIN)
        # Also on a network whose first claim the new key signs, deposits carry the provider's first key.
        self.chain.deposit(A, 'ethereum-mainnet', 10 ** 15)
        er = [em.make_receipt(self.w['eth'], 'first ethereum claim', day(14, 6), key=em.PROVIDER_NEXT)]
        ec, el = em.make_claim(em.PROVIDER_NEXT, 'ethereum-mainnet', [em.leaf_of(x) for x in er], day(14), day(15), decl)
        self.assertEqual(len(self.audit(ec, el)[0]), 5)

    def test_minority_witness_holders_follow_the_settled_claim(self):
        """Reproduces the reviewed gap: a provider shows A to four monitors and B to one; that one must not be stranded."""
        monitors = self.primed()
        ra, rb = self.receipts(['fork a'], d=12), self.receipts(['fork b'], d=12)
        a, la = self.claim(ra, d=12, previous='claim')
        b, lb = self.claim(rb, d=12, previous='claim')
        wa = [m.audit(a, la, day(13, 12))[1] for m in monitors[:4]]
        self.assertEqual(monitors[4].audit(b, lb, day(13, 12))[0], 'witnessed')
        self.assertEqual(self.state(ra[0], a, la, wa), 'settled')
        nxt = self.receipts(['next'], d=14)
        c3, l3 = self.claim(nxt, d=14, previous=a)
        self.assertEqual(monitors[4].audit(c3, l3, NOW)[1]['reason'], 'bad_chain')  # stranded without the rule
        with self.assertRaises(ValueError):
            monitors[4].follow(a, wa[:3], self.committee)  # only a settled claim can be followed
        monitors[4].follow(a, wa, self.committee)
        self.assertTrue(monitors[4].equivocations)
        self.assertEqual(monitors[4].witnessed[(A, NET, 2)]['claim_id'], b['claim_id'])  # its own witness is never withdrawn
        witnesses, refusals = em.committee_audit(monitors, c3, l3, NOW)
        self.assertEqual((len(witnesses), len(refusals)), (5, 0))
        self.assertEqual(self.state(rb[0], b, lb, [monitors[4].audit(b, lb, NOW)[1]]), 'unsettled')

    def test_a_receipt_is_claimed_by_the_key_that_issued_it(self):
        """Reproduces the reviewed gap: a receipt issued by the old key inside a claim signed by the new key never verifies."""
        succession, decl = self.rotate(day(20))
        old_receipts = self.receipts(['issued by the old key'], d=14)
        wrong, wl = self.claim(old_receipts, d=14, key=em.PROVIDER_NEXT, decl=decl, succession=succession)  # a period before the succession
        self.assertEqual(self.reason(wrong, wl), 'unknown_provider_key')
        with self.assertRaises(em.Rejected) as caught:
            self.monitors[0].check(wrong, wl, NOW)
        self.assertTrue(caught.exception.provable)  # the named succession itself shows the fault
        right, rl = self.claim(old_receipts, d=14)
        witnesses, _ = self.audit(right, rl)
        self.assertEqual(self.state(old_receipts[0], right, rl, witnesses), 'settled')
        self.assertEqual(em.receipt_state(old_receipts[0], em.make_proof(wrong, wl, 0, [m._witness(wrong, 0, NOW) for m in self.monitors]), self.committee), 'unsettled')
        new_receipts = self.receipts(['issued by the new key'], d=21, key=em.PROVIDER_NEXT)
        c, l = self.claim(new_receipts, d=21, previous=right, key=em.PROVIDER_NEXT, decl=decl, succession=succession)
        witnesses, refusals = self.audit(c, l)
        self.assertEqual((len(witnesses), len(refusals)), (5, 0))
        self.assertEqual(self.state(new_receipts[0], c, l, witnesses), 'settled')

    def test_a_monitor_that_missed_a_claim_catches_up(self):
        """Reproduces the reviewed gap: one lapse must not make a monitor refuse the rest of the chain."""
        lagging = em.Monitor(em.MONITORS[0], self.trust, self.chain, [self.w['btc'], self.w['eth']])
        lagging.register_declaration(self.w['decl_a'])
        lagging.audit(self.w['claim'], self.w['leaves'], day(6, 12))  # it never saw claim2
        r = self.receipts(['third'])
        c3, l3 = self.claim(r)
        self.assertEqual(lagging.audit(c3, l3, NOW)[1]['reason'], 'bad_chain')
        others = [w for w in self.w['witnesses2'] if w['witness_id'] != did(em.MONITORS[0])]
        lagging.adopt(self.w['claim2'], others, self.committee, '2027-06-01T00:00:00Z')  # long after the 90 days
        self.assertEqual(lagging.audit(c3, l3, NOW)[0], 'witnessed')  # a refusal is not final; a witness is

    def test_committee_handover_adopts_settled_history(self):
        """Reproduces the reviewed handover gaps: no re-deciding, no lateness failures, no pooling, no late departed witnesses."""
        old = self.committee
        keep = [m for m in self.monitors if did(m.key) in old[3:]]  # two monitors stay
        gone = [m for m in self.monitors if did(m.key) in old[:3]]  # three leave
        newcomers = [em.Monitor(k, self.trust, self.chain, [self.w['btc'], self.w['eth']]) for k in (PROVIDER, em.PROVIDER_B, em.PROVIDER_NEXT)]
        incoming = sorted(old[3:] + [A, B, C])
        changed = '2027-02-01T00:00:00Z'
        long_after = '2028-06-01T00:00:00Z'
        adopted = []
        for mon in newcomers:
            mon.adopt(self.w['claim'], self.w['witnesses'], old, long_after)  # no lateness refusal
            adopted.append(mon.adopt(self.w['claim2'], self.w['witnesses2'], old, long_after))
        structural('SettlementWitness', adopted[0])
        receipt, claim, leaves = self.w['receipts2'][0], self.w['claim2'], self.w['leaves2']
        stayed = [w for w in self.w['witnesses2'] if w['witness_id'] in old[3:]]
        left = [w for w in self.w['witnesses2'] if w['witness_id'] in old[:3]]
        # During the handover the outgoing quorum still settles it; afterwards the new committee does.
        self.assertEqual(self.state(receipt, claim, leaves, self.w['witnesses2'][:4], committee=incoming, previous_committee=old, changed_at=changed), 'settled')
        self.assertEqual(self.state(receipt, claim, leaves, stayed + adopted, committee=incoming), 'settled')
        # Witnesses of the two committees are never added together: three departed plus one newcomer is no quorum of either.
        self.assertEqual(self.state(receipt, claim, leaves, left + adopted[:1], committee=incoming, previous_committee=old, changed_at=changed), 'unsettled')
        # A newcomer cannot adopt a claim without an outgoing quorum, nor a different claim at an adopted sequence.
        r = self.receipts(['alternative'], d=12)
        alt, alt_leaves = self.claim(r, d=12, previous='claim')
        other = em.Monitor(em.FOUNDATION, self.trust, self.chain, [self.w['btc'], self.w['eth']])
        other.adopt(self.w['claim'], self.w['witnesses'], old, long_after)
        with self.assertRaises(ValueError):
            other.adopt(alt, self.w['witnesses2'], old, long_after)
        with self.assertRaises(ValueError):
            other.adopt(self.w['claim2'], self.w['witnesses2'][:3], old, long_after)
        with self.assertRaises(ValueError):
            newcomers[0].adopt(alt, [], old, long_after)
        self.assertEqual(newcomers[0].audit(alt, alt_leaves, long_after)[0], 'refused')
        # The reviewed attack: after the change, departed monitors witness a second claim at a new sequence.
        r3 = self.receipts(['shown to departed monitors'], d=14)
        c3, l3 = self.claim(r3, d=14)
        late = [m.audit(c3, l3, '2027-02-05T00:00:00Z')[1] for m in gone + keep[:1]]
        self.assertEqual(len(late), 4)
        self.assertEqual(self.state(r3[0], c3, l3, late, committee=incoming, previous_committee=old, changed_at=changed), 'unsettled')
        self.assertEqual(self.state(r3[0], c3, l3, late, committee=incoming, previous_committee=old, changed_at='2027-03-01T00:00:00Z'), 'settled')  # same witnesses, made before a later change
        self.assertIn('MUST NOT sign witnesses', (em.ROOT / 'docs/03-economics.md').read_text(encoding='utf-8'))

    def seven(self):
        """A seven-monitor committee (quorum 5, at most 2 faulty) that has witnessed the first claim."""
        keys = em.MONITORS + [em.PROVIDER_B, em.PROVIDER_NEXT]
        monitors = [em.Monitor(k, self.trust, self.chain, [self.w['btc'], self.w['eth']]) for k in keys]
        for m in monitors:
            m.register_declaration(self.w['decl_a'])
            m.audit(self.w['claim'], self.w['leaves'], day(6, 12))
        return monitors, sorted(did(k) for k in keys)

    def test_committee_change_is_bounded(self):
        five, seven = list(range(5)), list(range(7))
        self.assertEqual((em.quorum(five), em.max_faulty(five), em.max_replaced(five)), (4, 1, 2))
        self.assertEqual((em.quorum(seven), em.max_faulty(seven), em.max_replaced(seven)), (5, 2, 2))
        em.check_committee_change(five, [0, 1, 2, 8, 9])
        em.check_committee_change(five, [0, 1, 2, 3, 4, 5, 6])  # growing from five to seven adds two and removes none
        for bad in ([0, 1, 7, 8, 9], [0, 1, 2, 3], [0, 1, 2, 3, 5, 6], [0, 1, 2, 3, 4, 5, 6, 7]):
            with self.assertRaises(ValueError):
                em.check_committee_change(five, bad)
        with self.assertRaises(ValueError):
            em.check_committee_change(seven, [0, 1, 2, 3, 10, 11, 12])
        self.assertIn('replacing at most `q - f - 1` of them', (em.ROOT / 'docs/03-economics.md').read_text(encoding='utf-8'))

    def test_handover_with_split_witnesses_at_seven_monitors(self):
        """Reproduces the reviewed attack at the recommended size: X has 3 honest witnesses, Y has 2 honest and 2 faulty;
        one honest X-witness is replaced; the newcomer must not complete Y, even though Y has more witnesses."""
        monitors, old = self.seven()
        a, b, c, d, e, e1, e2 = monitors
        rx, ry = self.receipts(['x large ' + 'x' * 5000], d=12), self.receipts(['y tiny'], d=12)
        x, lx = self.claim(rx, d=12, previous='claim')
        y, ly = self.claim(ry, d=12, previous='claim')
        wx = [m.audit(x, lx, day(13, 12))[1] for m in (a, b, c)]
        wy = [m.audit(y, ly, day(13, 12))[1] for m in (d, e, e1, e2)]
        newcomer = em.Monitor(em.FOUNDATION, self.trust, self.chain, [self.w['btc'], self.w['eth']])
        newcomer.register_declaration(self.w['decl_a'])
        first = [m.audit(self.w['claim'], self.w['leaves'], day(6, 12))[1] for m in monitors]
        newcomer.adopt(self.w['claim'], first, old, '2027-02-01T00:00:00Z')
        new = sorted(set(old) - {did(c.key)} | {did(em.FOUNDATION)})
        em.check_committee_change(old, new)
        # The newcomer fetched the continuing monitors' pages, so it holds X's witnesses from a and b as well as Y's.
        seen = [(x, lx, [w for w in wx if w['witness_id'] != did(c.key)]), (y, ly, wy)]
        self.assertIsNone(newcomer.takeover(seen, old, '2027-02-01T00:00:00Z'))  # two valid claims: it witnesses neither
        self.assertEqual(self.state(ry[0], y, ly, wy, committee=new), 'unsettled')  # Y stays at four of seven
        # The faulty monitors then add backdated witnesses to X: only X settles, under the outgoing committee.
        e1.witnessed.pop((A, NET, 2)); e2.witnessed.pop((A, NET, 2))
        late = [m.audit(x, lx, day(20))[1] for m in (e1, e2)]
        self.assertEqual(self.state(rx[0], x, lx, wx + late, committee=new, previous_committee=old, changed_at='2027-02-01T00:00:00Z'), 'settled')
        self.assertEqual(self.state(ry[0], y, ly, wy, committee=new, previous_committee=old, changed_at='2027-02-01T00:00:00Z'), 'unsettled')

    def test_handover_blocks_on_a_claim_it_cannot_prove_invalid(self):
        """Reproduces the reviewed attack: A has an outgoing quorum the newcomers cannot see (the faulty monitor's
        witness is hidden) and its leaves are withheld; they must not complete B."""
        monitors = self.primed()
        a_, b_, c_, d_, e_ = monitors  # c_ is faulty and stays; d_ and e_ depart
        ra, rb = self.receipts(['claim A'], d=12), self.receipts(['claim B'], d=12)
        A_, la = self.claim(ra, d=12, previous='claim')
        B_, lb = self.claim(rb, d=12, previous='claim')
        wa = [m.audit(A_, la, day(13, 12))[1] for m in (a_, d_, e_, c_)]
        self.assertEqual(self.state(ra[0], A_, la, wa), 'settled')
        c_.witnessed.pop((A, NET, 2))
        wb = [m.audit(B_, lb, day(13, 12))[1] for m in (b_, c_)]
        old = self.committee
        new = sorted(set(old) - {did(d_.key), did(e_.key)} | {B, C})
        em.check_committee_change(old, new)
        newcomers = [em.Monitor(k, self.trust, self.chain, [self.w['btc'], self.w['eth']]) for k in (em.PROVIDER_B, em.PROVIDER_NEXT)]
        visible_a = [w for w in wa if w['witness_id'] != did(c_.key)]  # three of five: no visible quorum
        got = []
        for n in newcomers:
            n.register_declaration(self.w['decl_a'])
            n.adopt(self.w['claim'], self.w['witnesses'], old, NOW)
            got.append(n.takeover([(A_, None, visible_a), (B_, lb, wb)], old, NOW))  # A's leaves are withheld
        self.assertEqual(got, [None, None])
        self.assertEqual(self.state(rb[0], B_, lb, wb, committee=new), 'unsettled')  # B stays at two
        # The variant: A is merely too old for the first-seen rule. That proves nothing either; with its leaves the
        # newcomer finds both claims valid and still witnesses neither.
        late = em.Monitor(em.FOUNDATION, self.trust, self.chain, [self.w['btc'], self.w['eth']])
        late.register_declaration(self.w['decl_a'])
        late.adopt(self.w['claim'], self.w['witnesses'], old, '2028-01-01T00:00:00Z')
        self.assertIsNone(late.takeover([(A_, la, visible_a), (B_, lb, wb)], old, '2028-01-01T00:00:00Z'))
        # An unfunded claim is not proven invalid: it blocks too.
        poor = em.Monitor(em.PROVIDER, self.trust, em.Chain(), [self.w['btc'], self.w['eth']])
        poor.register_declaration(self.w['decl_a'])
        poor.witnessed[(A, NET, 1)] = self.w['claim']
        self.assertIsNone(poor.takeover([(A_, la, visible_a[:1])], old, NOW))

    def new_monitor(self, key, upto_claim2=False):
        m = em.Monitor(key, self.trust, self.chain, [self.w['btc'], self.w['eth']])
        m.register_declaration(self.w['decl_a'])
        m.adopt(self.w['claim'], self.w['witnesses'], self.committee, NOW)
        return m

    def test_a_block_survives_a_second_committee_change(self):
        """Reproduces the reviewed attack at five monitors: A is settled under C0 with a hidden faulty witness; change 1
        replaces two of A's honest witnesses, change 2 the third. Without holds, the last newcomers complete B."""
        monitors = self.primed()
        h1, h2, h3, h4, f = monitors  # f is faulty and stays throughout
        ra, rb = self.receipts(['claim A'], d=12), self.receipts(['claim B'], d=12)
        A_, la = self.claim(ra, d=12, previous='claim')
        B_, lb = self.claim(rb, d=12, previous='claim')
        wa = [m.audit(A_, la, day(13, 12))[1] for m in (h1, h2, h3, f)]
        f.witnessed.pop((A, NET, 2))
        wb = [m.audit(B_, lb, day(13, 12))[1] for m in (h4, f)]
        c0 = self.committee
        ids = {name: did(m.key) for name, m in (('h1', h1), ('h2', h2), ('h3', h3), ('h4', h4), ('f', f))}
        # Change 1: h1, h2 -> n1, n2. They see h3's witness for A (leaves withheld) and B: they block and publish holds.
        n1, n2 = self.new_monitor(em.PROVIDER_B), self.new_monitor(em.PROVIDER_NEXT)
        c1 = sorted(set(c0) - {ids['h1'], ids['h2']} | {B, C})
        em.check_committee_change(c0, c1)
        visible_a = [w for w in wa if w['witness_id'] == ids['h3']]
        for n in (n1, n2):
            self.assertIsNone(n.takeover([(A_, None, visible_a), (B_, lb, wb)], c0, '2027-02-01T00:00:00Z'))
            self.assertEqual(len(n.holds), 1)
            structural('SettlementHold', n.holds[0])
            self.assertEqual(n.holds[0]['claim_ids'], sorted([A_['claim_id'], B_['claim_id']]))
        structural('MonitorWitnessesPage', {'witnesses': [], 'refusals': [], 'holds': n1.holds, 'claims': [A_, B_]})
        # Change 2, 30 days later: h3 and n1 -> m1, m2. h3 is gone and serves nothing; only B's witnesses are on the pages.
        m1, m2 = self.new_monitor(em.FOUNDATION), self.new_monitor(PROVIDER)
        c2 = sorted(set(c1) - {ids['h3'], B} | {did(em.FOUNDATION), A})
        em.check_committee_change(c1, c2)
        holds = n2.holds  # n2 continues and serves its hold
        # n2 serves its hold together with the signed claim objects it names, so the newcomers hold A's claim (not its leaves).
        results = [m.takeover([(B_, lb, wb), (A_, None, [])], c1, '2027-03-05T00:00:00Z', holds=holds, past_members=c0) for m in (m1, m2)]
        self.assertEqual(results, [None, None])  # A is named in a hold and cannot be proven invalid: B is not completed
        self.assertEqual(self.state(rb[0], B_, lb, wb, committee=c2), 'unsettled')
        # Without the hold the same newcomers would have witnessed B (this is the flaw the hold closes).
        naive = self.new_monitor(em.MONITORS[0])
        self.assertIsNotNone(naive.takeover([(B_, lb, wb)], c1, '2027-03-05T00:00:00Z'))
        # A forged hold (not signed by its monitor) is ignored.
        forged = dict(n2.holds[0], claim_ids=[A_['claim_id']])
        self.assertIsNotNone(self.new_monitor(em.MONITORS[1]).takeover([(B_, lb, wb), (A_, None, [])], c1, '2027-03-05T00:00:00Z', holds=[forged]))
        # The reviewed censorship attack: a faulty continuing monitor serves a validly signed hold naming a claim that does
        # not exist. No signed claim object can be produced for it, so it is ignored and the honest claim proceeds.
        ghost = {'witness_id': ids['f'], 'provider_id': A, 'network': NET, 'sequence': 2, 'claim_ids': ['fysc2:' + 'ab' * 32], 'held_at': NOW}
        ghost['witness_signature'] = em.sign(f.key, 'settlement-hold', ghost)
        structural('SettlementHold', ghost)
        self.assertIsNotNone(self.new_monitor(em.MONITORS[2]).takeover([(B_, lb, wb)], c1, '2027-03-05T00:00:00Z', holds=[ghost]))
        # So is a hold signed by a key that is not a continuing committee monitor.
        stranger = dict(em.without(n2.holds[0], 'witness_signature'), witness_id=did(em.RELEASE_KEYS[0]))
        stranger['witness_signature'] = em.sign(em.RELEASE_KEYS[0], 'settlement-hold', stranger)
        self.assertIsNotNone(self.new_monitor(em.MONITORS[3]).takeover([(B_, lb, wb), (A_, None, [])], c1, '2027-03-05T00:00:00Z', holds=[stranger]))

    def test_a_settled_claim_settles_its_ancestors(self):
        """Reproduces the reviewed gap: the provider equivocates at one sequence, a child of one fork settles, and
        monitors that held the other fork (or newcomers) must still be able to follow."""
        monitors = self.primed()
        m1, m2, m3, m4, m5 = monitors  # m1 is faulty
        ra, rb = self.receipts(['fork a'], d=12), self.receipts(['fork b'], d=12)
        a1, la1 = self.claim(ra, d=12, previous='claim')
        b1, lb1 = self.claim(rb, d=12, previous='claim')
        wa1 = [m.audit(a1, la1, day(13, 12))[1] for m in (m2, m3, m4)]
        self.assertEqual(m5.audit(b1, lb1, day(13, 12))[0], 'witnessed')
        self.assertEqual(self.state(ra[0], a1, la1, wa1), 'unsettled')  # three of five
        rc = self.receipts(['child of a'], d=14)
        a2, la2 = self.claim(rc, d=14, previous=a1)
        wa2 = [m.audit(a2, la2, day(15, 12))[1] for m in (m2, m3, m4)] + [m1._witness(a2, 0, day(15, 12))]
        self.assertEqual(self.state(rc[0], a2, la2, wa2), 'settled')
        # The ancestor is settled through its descendant's quorum.
        index = next(i for i, leaf in enumerate(la1) if leaf['receipt_hash'] == em.object_hash(ra[0]))
        proof = em.make_proof(a1, la1, index, wa2, chain=[a2])
        structural('SettlementProof', proof)
        self.assertEqual(em.receipt_state(ra[0], proof, self.committee), 'settled')
        self.assertEqual(em.receipt_state(ra[0], em.make_proof(a1, la1, index, wa2), self.committee), 'unsettled')  # without the link
        wrong = em.make_proof(b1, lb1, 0, wa2, chain=[a2])  # the rival fork is not an ancestor of the settled claim
        self.assertEqual(em.receipt_state(rb[0], wrong, self.committee), 'unsettled')
        # m5 held the rival: it cannot catch up alone, but adopting with the ancestor lets it follow the chain.
        with self.assertRaises(ValueError):
            m5.adopt(a2, wa2, self.committee, day(15, 13))
        m5.adopt(a2, wa2, self.committee, day(15, 13), ancestors=[a1])
        self.assertEqual(m5.witnessed[(A, NET, 2)]['claim_id'], b1['claim_id'])  # its own witness is kept
        nxt = self.receipts(['next'], d=16)
        a3, la3 = self.claim(nxt, d=16, previous=a2)
        self.assertEqual(m5.audit(a3, la3, '2027-01-17T12:00:00Z')[0], 'witnessed')
        # A newcomer adopts the same way, with no witness of its own at the forked sequence.
        newcomer = self.new_monitor(em.FOUNDATION)
        with self.assertRaises(ValueError):
            newcomer.adopt(a2, wa2, self.committee, NOW)
        self.assertIsNotNone(newcomer.adopt(a2, wa2, self.committee, NOW, ancestors=[a1]))
        with self.assertRaises(ValueError):  # ancestors must really link
            self.new_monitor(em.PROVIDER_B).adopt(a2, wa2, self.committee, NOW, ancestors=[b1])
        # A newcomer that had to hold at the forked sequence (a1's leaves withheld) adopts the settled child through
        # takeover with its ancestors, and its hold there ends.
        held = self.new_monitor(em.PROVIDER_NEXT)
        self.assertIsNone(held.takeover([(a1, None, wa1), (b1, lb1, [])], self.committee, NOW))
        self.assertEqual(len(held.holds), 1)
        self.assertIsNotNone(held.takeover([(a2, la2, wa2)], self.committee, NOW, ancestors=[a1]))
        self.assertEqual(held.holds, [])
        # The verifier's chain check does not accept a change of provider key without a verified succession.
        s = em.key_succession(PROVIDER, em.PROVIDER_NEXT, day(13))
        for named in (None, s):
            other_key, ol = self.claim(self.receipts(['other key'], d=14, key=em.PROVIDER_NEXT), d=14, previous=a1, key=em.PROVIDER_NEXT, succession=named)
            forged = em.make_proof(a1, la1, index, [m._witness(other_key, 0, day(15, 12)) for m in monitors[:4]], chain=[other_key])
            self.assertEqual(em.receipt_state(ra[0], forged, self.committee), 'unsettled')
            self.assertEqual(em.receipt_state(ra[0], forged, self.committee, successions=[s]), 'settled' if named else 'unsettled')
        misdated = em.key_succession(PROVIDER, em.PROVIDER_NEXT, day(15))  # takes effect after the claim's period starts
        other_key, ol = self.claim(self.receipts(['other key'], d=14, key=em.PROVIDER_NEXT), d=14, previous=a1, key=em.PROVIDER_NEXT, succession=misdated)
        forged = em.make_proof(a1, la1, index, [m._witness(other_key, 0, day(15, 12)) for m in monitors[:4]], chain=[other_key])
        self.assertEqual(em.receipt_state(ra[0], forged, self.committee, successions=[misdated]), 'unsettled')

    def test_a_hold_on_a_single_claim_ends_when_it_passes_audit(self):
        blind = em.Monitor(em.FOUNDATION, self.trust, em.Chain(), [self.w['btc'], self.w['eth']])  # sees no deposits yet
        blind.register_declaration(self.w['decl_a'])
        blind.witnessed[(A, NET, 1)] = self.w['claim']
        hw = self.monitors[0]
        self.assertIsNone(blind.takeover([(self.w['claim2'], self.w['leaves2'], self.w['witnesses2'][:1])], self.committee, NOW))
        self.assertEqual(len(blind.holds), 1)
        blind.chain = self.chain  # the deposit is now visible
        self.assertEqual(blind.audit(self.w['claim2'], self.w['leaves2'], NOW)[0], 'witnessed')
        self.assertEqual(blind.holds, [])

    def test_a_late_signed_declaration_cannot_displace_a_claim(self):
        """Reproduces the reviewed attack: after A settles, the provider signs a backdated declaration D2 and a claim B
        naming it, hoping newcomers will find A 'invalid' and complete B. A claim's validity depends only on the claim,
        its predecessor and the declaration it names, so D2 changes nothing about A. B is only a second claim at the
        sequence: the newcomers hold, and B never settles."""
        monitors = self.primed()
        h1, h2, h3, h4, f = monitors
        ra, rb = self.receipts(['claim A'], d=12), self.receipts(['claim B'], d=12)
        A_, la = self.claim(ra, d=12, previous='claim')
        wa = [m.audit(A_, la, day(13, 12))[1] for m in (h1, h2, h3, f)]
        self.assertEqual(self.state(ra[0], A_, la, wa), 'settled')
        d2 = em.retention_declaration(PROVIDER, em.YEAR, day(8))  # signed later, dated between the two claimed periods
        B_, lb = self.claim(rb, d=12, previous='claim', decl=d2['declaration_id'])
        wb = [f._witness(B_, 0, day(13, 12))]
        newcomers = [self.new_monitor(k) for k in (em.PROVIDER_B, em.PROVIDER_NEXT)]
        visible_a = [w for w in wa if w['witness_id'] != did(f.key)]  # three of five visible: no quorum
        for n in newcomers:
            n.register_declaration(d2)
            self.assertIsInstance(n.check(A_, la, NOW, lateness=False), int)  # holding D2 does not touch A
            self.assertIsNone(n.takeover([(A_, la, visible_a), (B_, lb, wb)], self.committee, '2027-02-01T00:00:00Z'))
            self.assertEqual(len(n.holds), 1)
        new = sorted(set(self.committee) - {did(h1.key), did(h2.key)} | {B, C})
        self.assertEqual(self.state(rb[0], B_, lb, wb, committee=new), 'unsettled')

    def test_declaration_and_succession_faults_do_not_block_the_correction(self):
        """The former known limit of the handover: an honest provider publishes a claim with a wrong declaration or a
        misdated succession, a faulty monitor witnesses it, the provider corrects it, and the committee changes before
        the correction has a quorum. The fault is provable from the named object, so newcomers witness the correction."""
        monitors = self.primed()
        f = monitors[4]
        r = self.receipts(['honest mistake'], d=12)
        future = em.retention_declaration(PROVIDER, em.YEAR, day(20))  # not yet in effect for this period
        bad, bl = self.claim(r, d=12, previous='claim', decl=future['declaration_id'])
        good, gl = self.claim(r, d=12, previous='claim')
        for m in monitors[:4]:
            m.register_declaration(future)
            self.assertEqual(m.audit(bad, bl, day(13, 12))[1]['reason'], 'bad_period')
        wbad = [f._witness(bad, 0, day(13, 12))]
        wgood = [m.audit(good, gl, day(13, 13))[1] for m in monitors[2:4]]  # only two honest witnesses before the change
        for key in (em.PROVIDER_B, em.PROVIDER_NEXT):
            n = self.new_monitor(key)
            n.register_declaration(future)
            w = n.takeover([(bad, bl, wbad), (good, gl, wgood)], self.committee, '2027-02-01T00:00:00Z')
            self.assertEqual(w['claim_id'], good['claim_id'])
            self.assertEqual(n.holds, [])
        # The same for a first new-key claim whose named succession takes effect after its period starts.
        monitors = self.primed()
        f = monitors[4]
        late = em.key_succession(PROVIDER, em.PROVIDER_NEXT, day(20))
        fixed = em.key_succession(PROVIDER, em.PROVIDER_NEXT, day(12))
        decl = em.retention_declaration(em.PROVIDER_NEXT, em.YEAR, day(12))
        r = self.receipts(['new key'], d=12, key=em.PROVIDER_NEXT)
        bad, bl = self.claim(r, d=12, previous='claim', key=em.PROVIDER_NEXT, decl=decl['declaration_id'], succession=late)
        good, gl = self.claim(r, d=12, previous='claim', key=em.PROVIDER_NEXT, decl=decl['declaration_id'], succession=fixed)
        for m in monitors[:4]:
            m.register_declaration(decl)
            m.register_succession(late)
            m.register_succession(fixed)
            self.assertEqual(m.audit(bad, bl, day(13, 12))[1]['reason'], 'unknown_provider_key')
        wbad = [f._witness(bad, 0, day(13, 12))]
        wgood = [m.audit(good, gl, day(13, 13))[1] for m in monitors[2:4]]
        self.assertEqual(len(wgood), 2)
        n = self.new_monitor(em.PROVIDER_B)
        n.register_declaration(decl)
        n.register_succession(late)
        n.register_succession(fixed)
        w = n.takeover([(bad, bl, wbad), (good, gl, wgood)], self.committee, '2027-02-01T00:00:00Z')
        self.assertEqual(w['claim_id'], good['claim_id'])
        text = (em.ROOT / 'docs/03-economics.md').read_text(encoding='utf-8')
        self.assertNotIn('Known limit of the handover', text)
        self.assertIn('never blocks an honest provider', text)

    def test_a_period_fault_is_proven_and_does_not_block_the_correction(self):
        """Reproduces the reviewed deadlock: a faulty monitor witnesses the honest provider's too-long-period claim."""
        monitors = self.primed()
        good = self.receipts(['corrected'], d=12)
        fixed, fl = self.claim(good, d=12, previous='claim')
        long_claim, ll = self.claim(good, d=12, previous='claim', end='2027-01-13T00:00:01Z')  # one second over 24 hours
        fw = monitors[4]._witness(long_claim, 0, day(13, 12))
        hw = monitors[0].audit(fixed, fl, day(13, 12))[1]
        newcomer = self.new_monitor(em.FOUNDATION)
        got = newcomer.takeover([(long_claim, ll, [fw]), (fixed, fl, [hw])], self.committee, NOW)
        self.assertIsNotNone(got)
        self.assertEqual(got['claim_id'], fixed['claim_id'])
        # A schedule the newcomer has not fetched proves nothing: that claim blocks.
        blind = em.Monitor(em.PROVIDER_B, self.trust, self.chain, [self.w['eth']])
        blind.register_declaration(self.w['decl_a'])
        blind.witnessed[(A, NET, 1)] = self.w['claim']
        other, ol = self.claim(self.receipts(['other'], d=12), d=12, previous='claim')
        self.assertIsNone(blind.takeover([(fixed, fl, [hw]), (other, ol, [monitors[1]._witness(other, 0, day(13, 12))])], self.committee, NOW))

    def test_handover_ignores_a_claim_that_fails_audit(self):
        """Reproduces the reviewed deadlock: a faulty monitor's witness on a faulty claim must not block the honest correction."""
        monitors = self.primed()
        good = self.receipts(['corrected'], d=12)
        c2, l2 = self.claim(good, d=12, previous='claim')
        bad_leaves = [dict(em.leaf_of(good[0]), amount_base_units='137')]
        bad, bl = em.make_claim(PROVIDER, NET, bad_leaves, day(12), day(13), self.decl, previous=self.w['claim'])
        faulty = monitors[4]
        fw = faulty._witness(bad, 0, day(13, 12))  # the faulty monitor witnesses the invalid claim
        hw = monitors[0].audit(c2, l2, day(13, 12))[1]
        newcomer = em.Monitor(em.FOUNDATION, self.trust, self.chain, [self.w['btc'], self.w['eth']])
        newcomer.register_declaration(self.w['decl_a'])
        newcomer.adopt(self.w['claim'], self.w['witnesses'], self.committee, NOW)
        got = newcomer.takeover([(bad, bl, [fw]), (c2, l2, [hw])], self.committee, NOW)
        self.assertIsNotNone(got)
        self.assertEqual(got['claim_id'], c2['claim_id'])
        # With an outgoing quorum, it simply adopts.
        other = em.Monitor(em.PROVIDER_B, self.trust, self.chain, [self.w['btc'], self.w['eth']])
        other.adopt(self.w['claim'], self.w['witnesses'], self.committee, NOW)
        self.assertEqual(other.takeover([(self.w['claim2'], self.w['leaves2'], self.w['witnesses2'])], self.committee, '2028-01-01T00:00:00Z')['claim_id'], self.w['claim2']['claim_id'])

    def test_pending_is_local_trust_and_delinquency_is_recorded(self):
        """Reproduces the reviewed attacks: receipts that are never claimed, and dodging by eviction or a new key."""
        spam = self.receipts(['never claimed %d' % n for n in range(50)], d=14)
        self.assertEqual(em.pending_states(spam, day(15), trusted_providers={A}), ['pending_settlement'] * 50)
        self.assertEqual(em.pending_states(spam, day(15), trusted_providers=set()), ['unsettled'] * 50)  # an untrusted key gets nothing
        self.assertEqual(em.pending_states(spam, day(21, 5), {A}), ['pending_settlement'] * 50)
        self.assertEqual(em.pending_states(spam, day(21, 6), {A}), ['unsettled'] * 50)  # 7 days
        records = em.new_delinquencies(spam, day(21, 6))
        self.assertEqual(len(records), 50)
        later = self.receipts(['next batch %d' % n for n in range(50)], d=22)
        self.assertEqual(set(em.pending_states(spam + later, day(23), {A})), {'unsettled'})
        # The verifier evicts the old messages, or the provider stops serving them: the record remains.
        self.assertEqual(set(em.pending_states(later, day(23), {A}, records=records)), {'unsettled'})
        # A key succession does not shed the record.
        moved = self.receipts(['after succession'], d=22, key=em.PROVIDER_NEXT)
        line = lambda p: A if p == C else p
        self.assertEqual(em.pending_states(moved, day(23), {A, C}, records=records, line=line), ['unsettled'])
        self.assertEqual(em.pending_states(moved, day(23), {A, C}), ['pending_settlement'])  # a provider with a clean record
        # Only a message fetched from the provider's own read routes can be pending or delinquent:
        # no framing with a restored-fee receipt, and no dodge by serving messages only through relays.
        relayed = self.receipts(['only through relays %d' % n for n in range(5)], d=22)
        self.assertEqual(em.pending_states(relayed, day(23), {A}, served=set()), ['unsettled'] * 5)
        self.assertEqual(em.new_delinquencies(relayed, '2027-02-01T00:00:00Z', served=set()), set())
        own = {r['receipt_id'] for r in relayed[:2]}
        self.assertEqual(em.pending_states(relayed, day(23), {A}, served=own), ['pending_settlement'] * 2 + ['unsettled'] * 3)
        # Future-dated receipts are never pending.
        self.assertEqual(em.pending_states(self.receipts(['future'], d=25), day(23), {A}), ['unsettled'])
        # The honest path (24-hour period, 24-hour witness deadline) plus one corrected claim fits in 7 days.
        honest = self.receipts(['honest'], issued=day(14, 0))
        self.assertEqual(em.pending_states(honest, '2027-01-18T23:59:59Z', {A}), ['pending_settlement'])
        self.assertLess(48 + 48, em.PENDING_LIMIT // 3600)
        self.assertIn('never evidence that a fee was paid', (em.ROOT / 'docs/03-economics.md').read_text(encoding='utf-8'))

    def test_self_run_provider_cannot_settle_without_depositing(self):
        spam = self.receipts(['spam %d' % n for n in range(4)], d=14, key=em.PROVIDER_NEXT)
        claim, leaves = em.make_claim(em.PROVIDER_NEXT, NET, [em.leaf_of(r) for r in spam], day(14), day(15), self.decl_c['declaration_id'])
        self.assertEqual(self.reason(claim, leaves, at=day(15, 12)), 'unfunded')
        own = dict(em.without(self.w['witnesses'][0], 'witness_signature'), witness_id=C)
        own.update({k: claim[k] for k in em.WITNESSED_FIELDS})
        own['witness_signature'] = em.sign(em.PROVIDER_NEXT, 'settlement-witness', own)
        self.assertEqual(self.state(spam[0], claim, leaves, [own]), 'unsettled')  # its own signature is not a committee witness
        self.chain.deposit(A, NET, 10000)  # a deposit carrying someone else's commitment does not help
        self.assertEqual(self.reason(claim, leaves, at=day(15, 13)), 'unfunded')
        vault = em.Vault(self.committee)
        with self.assertRaises(ValueError):  # and the vault stores nothing that is not settled
            vault.put(spam[0], em.make_proof(claim, leaves, 0, [own]), NOW)

    def test_vault_stores_only_settled_messages(self):
        r = X['vault_receipt']
        self.assertNotIn('provider_id', r)  # anyone may deliver a valid message
        self.trust.verify_foundation(r, r['stored_at'], 'vault-receipt')
        vault = em.Vault(self.committee)
        proof = X['settlement_proof']
        first = vault.put(X['receipt'], proof, '2027-03-01T00:00:00Z')
        self.assertEqual(vault.put(X['receipt'], proof, '2027-04-01T00:00:00Z'), first)  # idempotent
        structural('VaultReceipt', first)
        with self.assertRaises(ValueError):  # not settled: three witnesses are a majority but not a quorum
            vault.put(self.w['receipts2'][0], em.make_proof(self.w['claim2'], self.w['leaves2'], 0, self.w['witnesses2'][:3]), NOW)
        with self.assertRaises(ValueError):
            vault.put(self.receipts(['not yet claimed'])[0], None, NOW)
        self.assertEqual({e['kind'] for e in vault.log.entries}, {'vault_receipt'})


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.w = em.build_world()
        self.a, self.b = self.w['claim'], self.w['claim_b']

    def full(self, score):
        return {m: [(0, 90, score)] for m in M}

    def run_quarter(self, attestations, declared, reports, previous=None, quarter=Q, **kw):
        return em.distribute(POLICY, NET, quarter[0], quarter[1], attestations, declared, reports, previous=previous, **kw)

    def entry(self, s, p=A):
        return next(e for e in s['entries'] if e['provider_id'] == p)

    def before(self, proven, accrued=0):
        return {'entries': [{'provider_id': A, 'proven_quarters': proven, 'accrued_base_units': str(accrued)}]}

    def big_attestation(self, texts=400):
        """A settled claim large enough to reach the minimum payout and to prove a quarter."""
        receipts = [em.make_receipt(self.w['btc'], 'b%03d' % n + 'k' * 1000000) for n in range(texts)]
        claim, leaves = em.make_claim(PROVIDER, NET, [em.leaf_of(r) for r in receipts], day(5), day(6), self.w['decl_a']['declaration_id'])
        return claim

    def test_policy_is_approved_by_release_keys_not_the_foundation(self):
        structural('DistributionPolicy', POLICY)
        em.check_policy(POLICY, self.w['trust'])
        self.assertNotIn('foundation_signature', POLICY)
        with self.assertRaises(ValueError):
            em.check_policy(em.distribution_policy(signers=[em.FOUNDATION, em.PROVIDER_B, PROVIDER, em.PROVIDER_NEXT]), self.w['trust'])
        with self.assertRaises(ValueError):  # less than 60 days before the quarter
            em.check_policy(em.distribution_policy(approved_at='2026-12-01T00:00:00Z'), self.w['trust'])
        swap = em.distribution_policy(revision=2, monitors=sorted(POLICY['monitors'][1:] + [B]), approved_at='2027-02-01T00:00:00Z', effective_at='2027-02-15T00:00:00Z')
        em.check_policy(swap, self.w['trust'], previous=POLICY)  # a committee replacement needs only 14 days
        too_many = em.distribution_policy(revision=2, monitors=sorted(POLICY['monitors'][3:] + [A, B, C]), approved_at='2027-02-01T00:00:00Z', effective_at='2027-02-15T00:00:00Z')
        with self.assertRaises(ValueError):  # three of five replaced at once
            em.check_policy(too_many, self.w['trust'], previous=POLICY)
        soon = em.distribution_policy(revision=2, monitors=sorted(POLICY['monitors'][1:] + [B]), approved_at='2027-01-02T00:00:00Z', effective_at='2027-01-20T00:00:00Z')
        with self.assertRaises(ValueError):  # less than 30 days after the previous committee took effect
            em.check_policy(soon, self.w['trust'], previous=POLICY)
        with self.assertRaises(ValueError):
            em.check_policy(swap, self.w['trust'])
        with self.assertRaises(ValueError):  # but not when it also changes the shares
            em.check_policy(em.distribution_policy(revision=2, vault_share_bp=9000, approved_at='2027-02-01T00:00:00Z', effective_at='2027-02-15T00:00:00Z'), self.w['trust'], previous=POLICY)
        with self.assertRaises(ValueError):
            em.check_policy(em.distribution_policy(monitor_share_bp=1001), self.w['trust'])
        for change in ({'vault_share_bp': 2499}, {'monitors': POLICY['monitors'][:4]}, {'min_reports': 2}):
            bad = em.distribution_policy(**change)
            with self.assertRaises(jsonschema.ValidationError):
                structural('DistributionPolicy', bad)
            with self.assertRaises(ValueError):
                em.check_policy(bad, self.w['trust'])

    def test_statement_is_recomputable(self):
        s = X['distribution_statement']
        structural('DistributionStatement', s)
        for e in s['entries']:
            paid = int(e['settled_fees_base_units'])
            retention_bp = 5000 + 5000 * e['retention_years'] // 10
            self.assertEqual(int(e['amount_base_units']), paid * 5000 * e['quality_bp'] * retention_bp // 10 ** 12)
            self.assertEqual((e['retention_years'], e['proven_quarters']), (1, 0))  # tiny settled fees prove nothing
            self.assertEqual(e['accrued_base_units'], e['amount_base_units'])  # below the minimum payout: accrued, not paid
            self.assertIsNone(e['payout'])
        self.assertEqual(self.entry(s, A)['quality_bp'], 9800)  # monitor means 9800, 9800, 9600 -> lower median
        self.assertEqual(self.entry(s, B)['quality_bp'], 9000)  # the 30-day monitor has no score
        self.assertEqual(s['distributed_base_units'], '0')
        seat = int(s['received_base_units']) * 500 // 10000 // 5
        self.assertEqual([p['amount_base_units'] for p in s['monitor_payments']], [str(seat)] * 5)
        lazy = em.distribute(POLICY, NET, Q[0], Q[1], [self.a], {A: [em.YEAR]}, {A: self.full(9000)}, complete_monitors=M[:4])
        self.assertEqual([p['amount_base_units'] for p in lazy['monitor_payments']].count('0'), 1)  # a monitor that missed a claim is unpaid
        answers = {M[0]: (100, 100), M[1]: (95, 100), M[2]: (94, 100), M[3]: (0, 100), M[4]: (40, 40)}  # (witnesses by the cut-off, claims counted in its membership)
        judged = em.distribute(POLICY, NET, Q[0], Q[1], [self.a], {A: [em.YEAR]}, {A: self.full(9000)}, monitor_answers=answers)
        paid = [p['monitor_id'] for p in judged['monitor_payments'] if p['amount_base_units'] != '0']
        self.assertEqual(paid, sorted([M[0], M[1], M[4]]))  # silence and refusing what the committee settles forfeit the seat; a mid-quarter member is judged on its own claims

    def test_no_provider_gets_back_more_than_it_keeps(self):
        for years, proven, score in ((100, 400, 10000), (1, 0, 10000), (10, 39, 9999), (10, 40, 1)):
            e = self.entry(self.run_quarter([self.a], {A: [years * em.YEAR]}, {A: self.full(score)}, previous=self.before(proven)))
            paid = int(e['settled_fees_base_units'])
            self.assertLessEqual(int(e['amount_base_units']), paid * 5000 // 10000)
            self.assertLess(int(e['amount_base_units']), paid)

    def test_amount_does_not_depend_on_other_providers(self):
        alone = self.entry(self.run_quarter([self.a], {A: [em.YEAR]}, {A: self.full(9000)}))
        for other_score, other_years in ((1, 1), (10000, 100)):
            together = self.entry(self.run_quarter([self.a, self.b], {A: [em.YEAR], B: [other_years * em.YEAR]},
                                                   {A: self.full(9000), B: self.full(other_score)}))
            self.assertEqual(together, alone)  # no pool to compete for, so Sybils and collusion change nothing

    def test_padding_and_wash_posting_lose_money(self):
        btc = self.w['btc']

        def quarter(extra):
            receipts = [em.make_receipt(btc, 'p%04d' % n + 'x' * 300) for n in range(40)] + [em.make_receipt(btc, t) for t in extra]
            a, leaves = em.make_claim(PROVIDER, NET, [em.leaf_of(r) for r in receipts], day(5), day(6), self.w['decl_a']['declaration_id'])
            e = self.entry(self.run_quarter([a], {A: [10 * em.YEAR]}, {A: self.full(10000)}, previous=self.before(40)))
            return int(e['amount_base_units']), int(e['settled_fees_base_units'])

        back0, paid0 = quarter([])
        back1, paid1 = quarter(['pad%04d' % n + 'z' * 960 for n in range(100)])
        self.assertGreater(paid1, paid0)
        self.assertLessEqual(back1 - back0, (paid1 - paid0) // 2 + 1)  # each extra unit of fee returns at most half, even at the best multiplier

    def test_better_quality_and_longer_proven_retention_keep_more(self):
        rate = lambda e: int(e['amount_base_units']) / int(e['settled_fees_base_units'])
        low = self.entry(self.run_quarter([self.a], {A: [em.YEAR]}, {A: self.full(6000)}))
        high = self.entry(self.run_quarter([self.a], {A: [em.YEAR]}, {A: self.full(9900)}))
        self.assertGreater(rate(high), rate(low))
        old = self.entry(self.run_quarter([self.a], {A: [10 * em.YEAR]}, {A: self.full(9900)}, previous=self.before(36)))
        self.assertGreater(rate(old), rate(high))
        self.assertAlmostEqual(rate(old), 0.5 * 0.99, places=2)
        self.assertAlmostEqual(rate(high), 0.5 * 0.99 * 0.55, places=2)

    def test_retention_is_proven_by_quarters_of_real_service(self):
        ten = {A: [10 * em.YEAR]}
        big = self.big_attestation()
        self.assertGreaterEqual(int(big['total_base_units']), MIN)
        new = self.entry(self.run_quarter([big], ten, {A: self.full(9000)}))
        self.assertEqual((new['retention_years'], new['proven_quarters']), (1, 1))  # a ten-year declaration by a new provider counts as one
        # Farming with a few tiny posts a quarter proves nothing.
        tiny = self.entry(self.run_quarter([self.a], ten, {A: self.full(9000)}, previous=self.before(7)))
        self.assertEqual(tiny['proven_quarters'], 7)
        # Nor does a quarter with poor quality.
        self.assertEqual(self.entry(self.run_quarter([big], ten, {A: self.full(4999)}))['proven_quarters'], 0)
        self.assertEqual(self.entry(self.run_quarter([big], ten, {A: self.full(9000)}, previous=self.before(7)))['retention_years'], 3)
        # The smallest declaration named in the quarter counts, so declaring long only at quarter end does not help.
        self.assertEqual(self.entry(self.run_quarter([big], {A: [10 * em.YEAR, em.YEAR]}, {A: self.full(9000)}, previous=self.before(40)))['retention_years'], 1)
        self.assertEqual(self.entry(self.run_quarter([big], {A: [100 * em.YEAR]}, {A: self.full(9000)}, previous=self.before(40)))['retention_years'], 10)

    def test_proven_quarters_survive_a_quarter_without_an_entry(self):
        big = self.big_attestation()
        skipped = {'entries': []}  # no settled fees and no accrued balance last quarter
        back = self.entry(self.run_quarter([big], {A: [10 * em.YEAR]}, {A: self.full(9000)}, previous=skipped, earlier=[self.before(7)]))
        self.assertEqual((back['proven_quarters'], back['retention_years']), (8, 3))
        newer = self.entry(self.run_quarter([big], {A: [10 * em.YEAR]}, {A: self.full(9000)}, previous=skipped, earlier=[self.before(2), self.before(7)]))
        self.assertEqual(newer['proven_quarters'], 3)  # the most recent entry counts

    def test_new_provider_is_scored_on_the_days_it_was_active(self):
        self.assertIsNone(em.monitor_score([(60, 90, 9000)]))  # 30 days is not enough for an established provider
        self.assertEqual(em.monitor_score([(60, 90, 9000)], active_days=30), 9000)  # but covers a provider that started 30 days ago
        self.assertIsNone(em.monitor_score([(60, 79, 9000)], active_days=30))  # 19 of 30 days is under two-thirds
        reports = {m: [(60, 90, 9000)] for m in M}
        self.assertEqual(self.entry(self.run_quarter([self.a], {A: [em.YEAR]}, {A: reports}))['quality_bp'], 0)
        self.assertEqual(self.entry(self.run_quarter([self.a], {A: [em.YEAR]}, {A: reports}, active_days={A: 30}))['quality_bp'], 9000)

    def test_quality_rules(self):
        self.assertEqual(em.monitor_score([(0, 59, 0), (59, 60, 10000)]), 166)  # weighted by days, not per report
        self.assertEqual(em.monitor_score([(0, 31, 10000), (31, 62, 2000)]), 6000)
        self.assertIsNone(em.monitor_score([(0, 31, 9000), (20, 51, 9000), (40, 71, 9000)]))  # overlapping reports are invalid
        self.assertIsNone(em.monitor_score([(0, 59, 9000)]))
        self.assertIsNone(em.monitor_score([(0, 90, None)]))  # an unknown score gives no coverage
        two = {M[0]: [(0, 90, 9000)], M[1]: [(0, 90, 9000)]}
        outsider = dict(two, **{did(PROVIDER): [(0, 90, 9999)]})
        for reports in (two, outsider):
            self.assertEqual(self.entry(self.run_quarter([self.a], {A: [em.YEAR]}, {A: reports}))['quality_bp'], 0)
        skewed = {M[0]: [(0, 90, 0)], M[1]: [(0, 90, 9000)], M[2]: [(0, 90, 9100)]}
        self.assertEqual(self.entry(self.run_quarter([self.a], {A: [em.YEAR]}, {A: skewed}))['quality_bp'], 9000)  # one outlier cannot zero it
        ids = ['fyqr2:' + ('%02x' % n) * 32 for n in range(3)]
        e = self.entry(self.run_quarter([self.a], {A: [em.YEAR]}, {A: self.full(9000)}, report_ids={A: ids[::-1]}))
        self.assertEqual(e['report_ids'], ids)  # the statement names the reports used, so an omitted report is provable

    def test_small_amounts_accrue_until_payable(self):
        big = self.big_attestation()
        payout = {'network': NET, 'txid': 'ab' * 32, 'output_index': 0}
        first = self.run_quarter([self.a], {A: [em.YEAR]}, {A: self.full(9000)}, recipients={A})
        self.assertEqual(first['distributed_base_units'], '0')
        second = em.distribute(POLICY, NET, Q[0], Q[1], [big], {A: [em.YEAR]}, {A: self.full(9000)}, previous=first, recipients={A}, payouts={A: payout})
        e = self.entry(second)
        owed = int(self.entry(first)['accrued_base_units']) + int(e['amount_base_units'])
        self.assertGreaterEqual(owed, MIN)
        self.assertEqual(e['payout'], payout)
        self.assertEqual(int(second['distributed_base_units']) + int(e['accrued_base_units']), owed)
        self.assertEqual(int(second['distributed_base_units']) % 1000, 0)  # whole satoshis
        no_recipient = self.entry(em.distribute(POLICY, NET, Q[0], Q[1], [big], {A: [em.YEAR]}, {A: self.full(9000)}, previous=first))
        self.assertIsNone(no_recipient['payout'])
        self.assertEqual(int(no_recipient['accrued_base_units']), owed)
        structural('DistributionStatement', second)
        with self.assertRaises(ValueError):  # a claim is counted in the quarter of its period_end
            self.run_quarter([self.a], {}, {}, quarter=Q2)


class RetentionAndKeyTests(unittest.TestCase):
    def test_retention_follows_the_declaration_named_by_the_claim(self):
        w = em.build_world()
        declarations = X['retention_declarations']
        for d in declarations:
            structural('RetentionDeclaration', d)
        structural('RetentionDeclarationsPage', {'declarations': declarations})
        issued = w['receipts'][0]['issued_at']
        self.assertEqual(em.retain_until(issued, w['claim'], declarations), em.seconds(issued) + 10 * em.YEAR)
        self.assertEqual(em.retain_until(issued, w['claim_b'], declarations), em.seconds(issued) + em.YEAR)
        with self.assertRaises(ValueError):  # another provider's declaration cannot be borrowed
            em.retain_until(issued, dict(w['claim'], declaration_id=w['decl_b']['declaration_id']), declarations)
        with self.assertRaises(ValueError):
            em.retain_until(issued, w['claim'], [dict(declarations[0], retention_seconds=20 * em.YEAR)])
        with self.assertRaises(jsonschema.ValidationError):
            structural('RetentionDeclaration', dict(declarations[0], retention_seconds=em.YEAR - 1))

    def test_key_succession_needs_both_keys(self):
        s = X['key_succession']
        jsonschema.Draft202012Validator(dict(SCHEMA, **{'$ref': '#/$defs/KeySuccession'}),
                                        format_checker=jsonschema.FormatChecker()).validate(s)
        em.check_succession(s)
        stolen = em.key_succession(PROVIDER, em.MONITORS[0], '2027-06-01T00:00:00Z')
        with self.assertRaises(ValueError):
            em.check_succession(dict(s, new_signature=stolen['new_signature']))
        with self.assertRaises(ValueError):
            em.check_succession(dict(s, effective_at='2027-06-02T00:00:00Z'))

    def test_media_slot_size_is_optional_and_bounded(self):
        validator = jsonschema.Draft202012Validator(dict(SCHEMA, **{'$ref': '#/$defs/MediaReference'}))
        slot = {'id': 'a', 'url': 'https://media.example/a', 'kind': 'image', 'sha256': '0' * 64}
        self.assertTrue(validator.is_valid(slot))
        self.assertTrue(validator.is_valid(dict(slot, size_bytes=1)))
        for bad in (0, -1, 1.5, '10', 2 ** 53):
            self.assertFalse(validator.is_valid(dict(slot, size_bytes=bad)))
        self.assertTrue(validator.is_valid(dict(slot, alt_text='x' * 2000)))
        self.assertFalse(validator.is_valid(dict(slot, alt_text='x' * 2001)))

    def test_withdrawal_objects(self):
        request = {'provider_id': A, 'author_id': B, 'network': NET, 'amount_base_units': '5000',
                   'recipient': em.RECIPIENTS[NET], 'request_id': 'A' * 43}
        structural('WithdrawalRequest', request)
        status = dict(request, status='pending', transfer=None, updated_at=NOW, provider_signature='A' * 86)
        structural('WithdrawalStatus', status)
        ethereum = 'ethereum-mainnet'  # every Ethereum address is also alphanumeric, so the address union must not be exclusive
        structural('WithdrawalRequest', dict(request, network=ethereum, recipient=em.RECIPIENTS[ethereum]))
        structural('WithdrawalStatus', dict(status, network=ethereum, recipient=em.RECIPIENTS[ethereum]))
        for kind, bad in (('WithdrawalRequest', dict(request, amount_base_units='0')), ('WithdrawalRequest', dict(request, recipient='not an address!')),
                          ('WithdrawalStatus', dict(status, status='cancelled'))):
            with self.assertRaises(jsonschema.ValidationError):
                structural(kind, bad)


class DocumentAgreementTests(unittest.TestCase):
    def setUp(self):
        self.docs = {p.name: p.read_text(encoding='utf-8') for p in (em.ROOT / 'docs').glob('*.md')}
        self.ops = json.loads((em.ROOT / 'schemas/operations.schema.json').read_text(encoding='utf-8'))['$defs']

    def test_goal_table_is_complete(self):
        self.assertEqual(re.findall(r'^\| (G\d+) \|', self.docs['01-overview.md'], flags=re.M), ['G%d' % n for n in range(1, 12)])

    def test_stale_design_terms_are_gone(self):
        names = [n for n in self.docs if n[:2] in ('01', '02', '03', '04', '05', '06', '07', '08', '09') or n == 'API-catalog.md']
        stale = ('Foundation-approved', 'carry_in', 'settled_bytes', 'release-pinned', 'pinned in the frozen release', 'good standing',
                 '14 days ago', '28 days', 'vault_delivered', 'no later than the settlement', 'in force at `issued_at`',
                 'FoundationKeyRevocation', 'latest settlement period fully ingested', 'pool_base_units', 'known credit',
                 'two trusted monitors', 'two different monitors', 'one transfer per', 'distribution weight', 'at most 7 days',
                 'within 7 days after finalization', 'log_root`', 'majority of the set and never fewer than two',
                 'SettlementAttestation', 'SettlementRejection', 'attested_at', 'POST /v1/settlements`', 'log_proof?', '96 hours',
                 'QualityReportReceipt', 'floor((A + R) / 2)', 'ASCII-smallest `claim_id`', 'withdrawing any other witness', 'fyst2', 'the sum for both keys',
                 'or of the previous committee during the 30 days', 'no deposit carrying its commitment', 'holds one of them',
                 'whichever key signs the chain', 'rubber-stamping earns', 'Foundation schedule approval', 'honest majority', 'dated within 48 hours', 'the most outgoing witnesses', 'a two-thirds quorum', 'If exactly one of them passes', 'MAY take effect at any time', 'every other claim with an outgoing witness at that sequence', 'a declaration that is not the governing one, the wrong key for the period', 'No honest monitor is therefore left behind')
        for name in names:
            for term in stale:
                self.assertNotIn(term, self.docs[name], (name, term))

    def test_numbers_agree_across_documents(self):
        for name in ('03-economics.md', '05-portability.md', '07-clients.md'):
            self.assertIn('7 days', self.docs[name], name)
        self.assertIn('at most 24 hours', self.docs['03-economics.md'])
        self.assertIn('more than two-thirds', self.docs['03-economics.md'])
        self.assertIn('more than two-thirds', self.docs['07-clients.md'])
        for name in ('01-overview.md', '03-economics.md', '05-portability.md', '07-clients.md', '08-operator-guide.md'):
            self.assertNotIn('more than half', self.docs[name], name)
        self.assertIn('two-thirds', self.docs['06-governance.md'])

    def test_every_object_named_in_economics_has_a_schema(self):
        text = self.docs['03-economics.md'] + self.docs['06-governance.md']
        launch = SCHEMA['$defs']
        named = set(re.findall(r'`((?:Settlement|Distribution|Foundation|Vault|Withdrawal|Retention|FeeSchedule|QualityReport|ReleaseKeySet|Genesis)[A-Za-z]*)`', text))
        self.assertGreater(len(named), 25)
        self.assertEqual(sorted(n for n in named if n not in self.ops and n not in launch), [])

    def test_prose_field_lists_match_schemas(self):
        """Every `Name` `{a,b,c}` field list in the economics and governance documents equals the schema's properties."""
        text = self.docs['03-economics.md'] + self.docs['06-governance.md']
        checked = 0
        for name, fields in re.findall(r'`([A-Z][A-Za-z]+)`(?: is| object| objects)? `\{([a-z_,?]+)\}`', text):
            schema = self.ops.get(name) or SCHEMA['$defs'].get(name)
            if schema is None or 'properties' not in schema:
                continue
            prose = {f.rstrip('?') for f in fields.split(',')}
            self.assertEqual(prose, set(schema['properties']), name)
            checked += 1
        self.assertGreaterEqual(checked, 14)

    def test_prefixes_are_listed(self):
        prefixes = set(re.findall(r'`(fy[a-z]{2}2):', self.docs['03-economics.md'] + self.docs['06-governance.md']))
        for prefix in prefixes:
            self.assertIn('`%s:`' % prefix, self.docs['02-protocol.md'], prefix)

    def test_catalog_routes_exist_in_owning_documents(self):
        owners = ''.join(self.docs[n] for n in self.docs if n != 'API-catalog.md')
        routes = set(re.findall(r'`((?:GET|POST|PUT) /v1/[^` ?]*)', self.docs['API-catalog.md']))
        self.assertGreater(len(routes), 38)
        self.assertEqual(sorted(r for r in routes if r not in owners), [])
        owned = set(re.findall(r'`((?:GET|POST|PUT) /v1/[^` ?]*)', self.docs['03-economics.md'] + self.docs['06-governance.md']))
        self.assertEqual(sorted(r for r in owned if r not in self.docs['API-catalog.md']), [])


if __name__ == '__main__':
    unittest.main()
