"""Randomized adversarial search over committee changes.

An adversary controls the provider and up to f monitors (fewer than one-third of every committee). It publishes
several valid claims at one sequence, chooses which claim each honest monitor sees first, hides or reveals
witnesses and leaves, and replaces monitors within the handover bounds, several times. Honest monitors run the
reference model's own code. After every step the search checks the safety property of settlement:

    at most one claim at a sequence is ever settled, under any committee, at any time.

Signatures are replaced by a fast stand-in for the search only; every rule under test is the model's.
This is a bounded random search with fixed seeds, not a proof.
"""
import hashlib
import random
import unittest
from unittest import mock

import rfc8785
from nacl.signing import SigningKey

import economics_model as em
from test_security_profile import PROVIDER, did

NET = 'bitcoin-mainnet'
T0, T1 = '2027-01-06T12:00:00Z', '2027-01-13T12:00:00Z'


def fast_sign(key, label, obj):
    return 'S' + hashlib.sha256((did(key) + label).encode() + rfc8785.dumps(obj)).hexdigest()


def fast_verify(identity, label, obj, sig):
    if sig != 'S' + hashlib.sha256((identity + label).encode() + rfc8785.dumps(obj)).hexdigest():
        raise ValueError('signature')


class Search:
    def __init__(self, n, seed, directed=False):
        self.directed = directed
        self.rng = random.Random(seed)
        self.n, self.seed = n, seed
        self.btc, self.eth = em.schedule_1(NET), em.schedule_1('ethereum-mainnet')
        self.trust = em.Trust([em.key_certificate()])
        self.chain = em.Chain()
        self.chain.deposit(did(PROVIDER), NET, 1000000)
        self.decl = em.retention_declaration(PROVIDER, em.YEAR, '2026-12-01T00:00:00Z')
        self.counter = 0
        self.monitors = {}  # id -> Monitor
        self.faulty = set()
        self.epoch = 0
        self.committees = []  # list of id lists, one per epoch
        self.witness_epoch = {}  # (monitor id, claim id) -> epoch in which an honest monitor signed
        self.witness_obj = {}  # (monitor id, claim id) -> witness object (honest and faulty)
        self.ever_settled = set()
        self.log = []
        first = [self.new_monitor() for _ in range(n)]
        f = em.max_faulty(first)
        self.faulty = set(self.rng.sample(first, self.rng.randint(0, f)))
        self.committees.append(sorted(first))
        receipts = [em.make_receipt(self.btc, 'first')]
        self.claim1, self.leaves1 = em.make_claim(PROVIDER, NET, [em.leaf_of(r) for r in receipts], '2027-01-05T00:00:00Z',
                                                  '2027-01-06T00:00:00Z', self.decl['declaration_id'])
        for m in first:
            kind, w = self.monitors[m].audit(self.claim1, self.leaves1, T0)
            assert kind == 'witnessed'
            self.witness_obj[(m, self.claim1['claim_id'])] = w
        self.claims = []
        for k in range(self.rng.randint(2, 3)):
            r = [em.make_receipt(self.btc, 'fork %d %d' % (seed, k), '2027-01-12T06:00:00Z')]
            self.claims.append(em.make_claim(PROVIDER, NET, [em.leaf_of(x) for x in r], '2027-01-12T00:00:00Z', '2027-01-13T00:00:00Z',
                                             self.decl['declaration_id'], previous=self.claim1))
        for m in self.faulty:  # a faulty monitor signs every claim
            for claim, _ in self.claims:
                self.witness_obj[(m, claim['claim_id'])] = self.monitors[m]._witness(claim, 0, T1)

    def new_monitor(self):
        self.counter += 1
        key = SigningKey(hashlib.sha256(b'search %d %d %d' % (self.n, self.seed, self.counter)).digest())
        m = em.Monitor(key, self.trust, self.chain, [self.btc, self.eth])
        m.register_declaration(self.decl)
        self.monitors[did(key)] = m
        return did(key)

    @property
    def committee(self):
        return self.committees[self.epoch]

    def honest_witnesses(self, committee, claim_id, upto_epoch):
        return [m for m in committee if m not in self.faulty and self.witness_epoch.get((m, claim_id), 10 ** 9) <= upto_epoch]

    def check(self):
        for k, committee in enumerate(self.committees):
            faulty_here = sum(1 for m in committee if m in self.faulty)
            assert faulty_here <= em.max_faulty(committee), 'search bug: too many faulty monitors'
            for claim, _ in self.claims:
                votes = len(self.honest_witnesses(committee, claim['claim_id'], k)) + faulty_here
                if votes >= em.quorum(committee):
                    self.ever_settled.add(claim['claim_id'])
        return len(self.ever_settled) <= 1

    def show(self):
        """The provider shows one claim to one honest committee monitor that has not witnessed at this sequence."""
        m = self.rng.choice(self.committee)
        if m in self.faulty:
            return
        claim, leaves = self.rng.choice(self.claims)
        kind, result = self.monitors[m].audit(claim, leaves, T1)
        self.log.append(('show', m[-6:], claim['claim_id'][-6:], kind))
        if kind == 'witnessed' and (m, claim['claim_id']) not in self.witness_epoch:
            self.witness_epoch[(m, claim['claim_id'])] = self.epoch
            self.witness_obj[(m, claim['claim_id'])] = result

    def catch_up(self):
        """An honest monitor without a witness adopts a claim for which it is shown a quorum of the current committee."""
        m = self.rng.choice(self.committee)
        if m in self.faulty:
            return
        claim, _ = self.rng.choice(self.claims)
        witnesses = [w for (who, cid), w in self.witness_obj.items() if cid == claim['claim_id'] and who in self.committee]
        try:
            w = self.monitors[m].adopt(claim, witnesses, self.committee, T1)
        except ValueError:
            return
        self.log.append(('catch-up', m[-6:], claim['claim_id'][-6:]))
        if (m, claim['claim_id']) not in self.witness_epoch:
            self.witness_epoch[(m, claim['claim_id'])] = self.epoch
            self.witness_obj[(m, claim['claim_id'])] = w

    def change(self):
        old = self.committee
        limit = em.max_replaced(old)
        leaving = self.rng.sample(old, self.rng.randint(1, limit))
        staying = [m for m in old if m not in leaving]
        incoming = [self.new_monitor() for _ in leaving]
        new = sorted(staying + incoming)
        room = em.max_faulty(new) - sum(1 for m in new if m in self.faulty)
        for m in incoming:  # the adversary may also hold some of the new seats, within the assumption
            if room > 0 and self.rng.random() < 0.3:
                self.faulty.add(m)
                room -= 1
                for claim, _ in self.claims:
                    self.witness_obj[(m, claim['claim_id'])] = self.monitors[m]._witness(claim, 0, T1)
        em.check_committee_change(old, new)
        self.committees.append(new)
        self.epoch += 1
        past = sorted({m for c in self.committees[:-1] for m in c})
        honest_staying = [m for m in staying if m not in self.faulty]
        self.last_change = dict(old=old, incoming=incoming, staying=staying, honest_staying=honest_staying, past=past)
        holds = [h for m in honest_staying for h in self.monitors[m].holds]
        if self.rng.random() < 0.3:  # faulty continuing monitors may publish holds too, naming real claims
            for m in staying:
                if m in self.faulty:
                    ids = sorted(c['claim_id'] for c, _ in self.rng.sample(self.claims, self.rng.randint(1, len(self.claims))))
                    h = {'witness_id': m, 'provider_id': did(PROVIDER), 'network': NET, 'sequence': 2, 'claim_ids': ids, 'held_at': T1}
                    h['witness_signature'] = em.sign(self.monitors[m].key, 'settlement-hold', h)
                    holds.append(h)
        named = {cid for h in holds for cid in h['claim_ids']}
        first_w = [w for (who, cid), w in self.witness_obj.items() if cid == self.claim1['claim_id'] and who in old]
        for m in incoming:
            if m in self.faulty:
                continue
            mon = self.monitors[m]
            mon.adopt(self.claim1, first_w, old, T1)
            self.witness_obj[(m, self.claim1['claim_id'])] = mon._witness(self.claim1, 0, T1)
            candidates = []
            stingy = self.directed and self.rng.random() < 0.7  # minimal disclosure: nothing optional about claim A
            for index, (claim, leaves) in enumerate(self.claims):
                cid = claim['claim_id']
                forced = [w for (who, c), w in self.witness_obj.items() if c == cid and who in honest_staying]
                optional = [w for (who, c), w in self.witness_obj.items() if c == cid and who not in honest_staying and who in past]
                must_serve = bool(forced) or cid in {c for hm in honest_staying for h in self.monitors[hm].holds for c in h['claim_ids']}
                if stingy:
                    shown = forced + (optional if index else [])
                    give_leaves = bool(index)
                    if not (must_serve or index):
                        continue
                else:
                    shown = forced + [w for w in optional if self.rng.random() < 0.5]
                    give_leaves = self.rng.random() < 0.6
                    if not (must_serve or self.rng.random() < 0.6):
                        continue  # the adversary hides this claim from the newcomer entirely
                candidates.append((claim, leaves if give_leaves else None, shown))
            self.rng.shuffle(candidates)
            result = mon.takeover(candidates, old, T1, holds=holds, past_members=past) if candidates else None
            self.log.append(('takeover', m[-6:], [c['claim_id'][-6:] for c, _, _ in candidates], None if result is None else result['claim_id'][-6:]))
            if result is not None and (m, result['claim_id']) not in self.witness_epoch:
                self.witness_epoch[(m, result['claim_id'])] = self.epoch
                self.witness_obj[(m, result['claim_id'])] = result

    def opening(self):
        """The strongest known opening: claim A reaches exactly a quorum with the faulty monitors' help (so its honest
        witnesses are as few as possible), and every other honest monitor is given claim B first."""
        honest = [m for m in self.committee if m not in self.faulty]
        self.rng.shuffle(honest)
        need = em.quorum(self.committee) - len(self.faulty)
        for k, m in enumerate(honest):
            claim, leaves = self.claims[0] if k < need else self.claims[1]
            kind, result = self.monitors[m].audit(claim, leaves, T1)
            if kind == 'witnessed':
                self.witness_epoch[(m, claim['claim_id'])] = self.epoch
                self.witness_obj[(m, claim['claim_id'])] = result
        self.a_witnesses = [m for m in honest[:need]]

    def change_targeted(self):
        """Replace the honest witnesses of claim A first, as fast as the bounds allow."""
        targets = [m for m in self.committee if m in self.a_witnesses]
        original = self.rng.sample
        used = []

        def pick(population, k):
            if used:  # only the choice of who leaves is steered; later draws stay random
                return original(population, k)
            used.append(True)
            chosen = [m for m in targets if m in population][:k]
            rest = [m for m in population if m not in chosen and m not in self.faulty]
            self.rng.shuffle(rest)
            return chosen + rest[:k - len(chosen)]
        self.rng.sample = pick
        try:
            self.change()
        finally:
            self.rng.sample = original

    def run(self, steps):
        if self.directed:
            self.opening()
            if not self.check():
                return False
        for _ in range(steps):
            roll = self.rng.random()
            if self.directed and roll < 0.35 and self.epoch < 6:
                self.change_targeted()
            elif roll < 0.55:
                self.show()
            elif roll < 0.75:
                self.catch_up()
            elif self.epoch < (6 if self.directed else 4):
                self.change()
            if not self.check():
                return False
        return True


T2 = '2027-01-15T12:00:00Z'


class ChainSearch(Search):
    """Two chained sequences: every fork at the first has a child at the next, optionally signed by a successor key.
    A quorum on a child settles its parent, so the search also checks the ancestor rule and the succession rules."""

    def __init__(self, n, seed, directed=False):
        self.succession = None
        super().__init__(n, seed, directed)
        signer = PROVIDER
        if self.rng.random() < 0.5:
            self.succession = em.key_succession(PROVIDER, em.PROVIDER_NEXT, '2027-01-13T00:00:00Z')
            signer = em.PROVIDER_NEXT
            for m in self.monitors.values():
                m.register_succession(self.succession)
        self.children, self.parent = [], {}
        for k, (claim, _) in enumerate(self.claims):
            r = [em.make_receipt(self.btc, 'child %d %d' % (seed, k), '2027-01-14T06:00:00Z', key=signer)]
            child = em.make_claim(signer, NET, [em.leaf_of(x) for x in r], '2027-01-14T00:00:00Z', '2027-01-15T00:00:00Z',
                                  self.decl['declaration_id'], previous=claim)
            self.children.append(child)
            self.parent[child[0]['claim_id']] = claim
        for m in self.faulty:
            for child, _ in self.children:
                self.witness_obj[(m, child['claim_id'])] = self.monitors[m]._witness(child, 0, T2)
        self.settled_children = set()

    def new_monitor(self):
        m = super().new_monitor()
        if self.succession is not None:
            self.monitors[m].register_succession(self.succession)
        return m

    def check(self):
        super().check()
        for k, committee in enumerate(self.committees):
            faulty_here = sum(1 for m in committee if m in self.faulty)
            for child, _ in self.children:
                if len(self.honest_witnesses(committee, child['claim_id'], k)) + faulty_here >= em.quorum(committee):
                    self.settled_children.add(child['claim_id'])
                    self.ever_settled.add(self.parent[child['claim_id']]['claim_id'])  # a settled claim settles its ancestors
        return len(self.ever_settled) <= 1 and len(self.settled_children) <= 1

    def record(self, m, claim, witness):
        if (m, claim['claim_id']) not in self.witness_epoch:
            self.witness_epoch[(m, claim['claim_id'])] = self.epoch
            self.witness_obj[(m, claim['claim_id'])] = witness

    def show_child(self):
        m = self.rng.choice(self.committee)
        if m in self.faulty:
            return
        child, leaves = self.rng.choice(self.children)
        kind, result = self.monitors[m].audit(child, leaves, T2)
        self.log.append(('show-child', m[-6:], child['claim_id'][-6:], kind))
        if kind == 'witnessed':
            self.record(m, child, result)

    def catch_up_child(self):
        m = self.rng.choice(self.committee)
        if m in self.faulty:
            return
        child, _ = self.rng.choice(self.children)
        witnesses = [w for (who, cid), w in self.witness_obj.items() if cid == child['claim_id'] and who in self.committee]
        try:
            w = self.monitors[m].adopt(child, witnesses, self.committee, T2, ancestors=[self.parent[child['claim_id']]])
        except ValueError:
            return
        self.log.append(('catch-up-child', m[-6:], child['claim_id'][-6:]))
        self.record(m, child, w)

    def change(self):
        super().change()
        c = self.last_change
        holds = [h for m in c['honest_staying'] for h in self.monitors[m].holds]
        ancestors = {child['claim_id']: [self.parent[child['claim_id']]] for child, _ in self.children}
        for m in c['incoming']:
            if m in self.faulty:
                for child, _ in self.children:
                    self.witness_obj[(m, child['claim_id'])] = self.monitors[m]._witness(child, 0, T2)
                continue
            candidates = []
            for child, leaves in self.children:
                cid = child['claim_id']
                forced = [w for (who, x), w in self.witness_obj.items() if x == cid and who in c['honest_staying']]
                optional = [w for (who, x), w in self.witness_obj.items() if x == cid and who not in c['honest_staying'] and who in c['past']]
                named = cid in {x for hm in c['honest_staying'] for h in self.monitors[hm].holds for x in h['claim_ids']}
                if not (forced or named or self.rng.random() < 0.6):
                    continue
                candidates.append((child, leaves if self.rng.random() < 0.6 else None, forced + [w for w in optional if self.rng.random() < 0.5]))
            self.rng.shuffle(candidates)
            if not candidates:
                continue
            try:
                result = self.monitors[m].takeover(candidates, c['old'], T2, holds=holds, past_members=c['past'], ancestors=ancestors)
            except ValueError:
                result = None  # the claim it would adopt does not link to anything this newcomer may follow
            self.log.append(('takeover-child', m[-6:], [x['claim_id'][-6:] for x, _, _ in candidates], None if result is None else result['claim_id'][-6:]))
            if result is not None:
                self.record(m, next(ch for ch, _ in self.children if ch['claim_id'] == result['claim_id']), result)

    def run(self, steps):
        if self.directed:
            self.opening()
            if not self.check():
                return False
        for _ in range(steps):
            roll = self.rng.random()
            if roll < 0.25:
                self.show()
            elif roll < 0.5:
                self.show_child()
            elif roll < 0.6:
                self.catch_up()
            elif roll < 0.75:
                self.catch_up_child()
            elif self.directed and roll < 0.9 and self.epoch < 6:
                self.change_targeted()
            elif self.epoch < 5:
                self.change()
            if not self.check():
                return False
        return True


class SettlementSearchTests(unittest.TestCase):
    def search(self, n, seeds, directed=False):
        with mock.patch.object(em, 'sign', fast_sign), mock.patch.object(em, 'verify', fast_verify):
            for seed in seeds:
                s = Search(n, seed, directed)
                ok = s.run(40)
                self.assertTrue(ok, 'two claims settled at one sequence: n=%d seed=%d\n%s' % (n, seed, '\n'.join(map(str, s.log))))
        return True

    def test_no_double_settlement_with_five_monitors(self):
        self.search(5, range(400))

    def test_no_double_settlement_with_seven_monitors(self):
        self.search(7, range(400))

    def test_directed_search_with_five_monitors(self):
        self.search(5, range(400), directed=True)

    def test_directed_search_with_seven_monitors(self):
        self.search(7, range(400), directed=True)

    def chain_search(self, n, seeds, directed=False):
        with mock.patch.object(em, 'sign', fast_sign), mock.patch.object(em, 'verify', fast_verify):
            for seed in seeds:
                s = ChainSearch(n, seed, directed)
                ok = s.run(60)
                self.assertTrue(ok, 'double settlement in a chained search: n=%d seed=%d succession=%s\n%s'
                                % (n, seed, s.succession is not None, '\n'.join(map(str, s.log))))

    def test_chained_sequences_and_successions_with_five_monitors(self):
        self.chain_search(5, range(300))
        self.chain_search(5, range(300, 450), directed=True)

    def test_chained_sequences_and_successions_with_seven_monitors(self):
        self.chain_search(7, range(300))
        self.chain_search(7, range(300, 450), directed=True)

    def test_the_chained_search_finds_a_break_without_the_one_witness_rule(self):
        """Sanity check: if honest monitors could witness two claims at a sequence, the chained search must notice."""
        original = em.Monitor.audit

        def forgetful(self, claim, leaves, seen_at, lateness=True):
            slot = (self.line(claim['provider_id']), claim['network'], claim['sequence'])
            self.witnessed.pop(slot, None)
            return original(self, claim, leaves, seen_at, lateness)

        with mock.patch.object(em, 'sign', fast_sign), mock.patch.object(em, 'verify', fast_verify), \
                mock.patch.object(em.Monitor, 'audit', forgetful):
            found = any(not ChainSearch(5, seed).run(60) for seed in range(200))
        self.assertTrue(found)

    def test_the_directed_search_finds_the_missing_hold_flaw(self):
        """Sanity check: with holds switched off, the directed search rediscovers the two-change attack."""
        original = em.Monitor.takeover

        def no_holds(self, candidates, outgoing_committee, at, holds=(), past_members=()):
            return original(self, candidates, outgoing_committee, at, holds=(), past_members=past_members)

        with mock.patch.object(em, 'sign', fast_sign), mock.patch.object(em, 'verify', fast_verify),                 mock.patch.object(em.Monitor, 'takeover', no_holds):
            found = any(not Search(5, seed, True).run(40) for seed in range(400))
        self.assertTrue(found)

    def test_the_search_can_find_a_real_break(self):
        """Sanity check of the search itself: with a simple-majority quorum it must find a double settlement."""
        with mock.patch.object(em, 'sign', fast_sign), mock.patch.object(em, 'verify', fast_verify), \
                mock.patch.object(em, 'quorum', lambda committee: len(set(committee)) // 2 + 1):
            found = False
            for seed in range(300):
                s = Search(5, seed)
                if not s.run(40):
                    found = True
                    break
        self.assertTrue(found)


if __name__ == '__main__':
    unittest.main()
