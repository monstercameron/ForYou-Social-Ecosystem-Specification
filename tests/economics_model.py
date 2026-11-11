"""Reference model for fee schedule 1, settlement, distribution and retention.

Synthetic keys and amounts only. This is a test model, not a payment or
custody implementation. Run `python tests/economics_model.py --write` to
regenerate examples/settlement.example.json after an intended change.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import rfc8785
from nacl.signing import SigningKey

from test_security_profile import PROVIDER, I, b64, did, mid, pre, sign, verify

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'examples/settlement.example.json'
FOUNDATION = SigningKey(bytes(range(128, 160)))
PROVIDER_B = SigningKey(bytes(range(160, 192)))
PROVIDER_NEXT = SigningKey(bytes(range(192, 224)))
MONITORS = [SigningKey(hashlib.sha256(b'synthetic monitor %d' % n).digest()) for n in range(5)]
RELEASE_KEYS = [SigningKey(hashlib.sha256(b'synthetic release key %d' % n).digest()) for n in range(5)]
RELEASE_THRESHOLD = 4
HOUR = 3600
YEAR = 31536000
DAY = 86400
RATES = {'bitcoin-mainnet': ('millisatoshi', 136), 'ethereum-mainnet': ('wei', 48900000000)}
RECIPIENTS = {'bitcoin-mainnet': 'bc1qw508d4ejxtdg4y5r3zarvary0c5xw7kv8f3t4', 'ethereum-mainnet': '0x' + '5a' * 20}
MIN_DEPOSIT = {'bitcoin-mainnet': 10000, 'ethereum-mainnet': 10 ** 15}  # satoshis, wei
CHAIN_TO_BASE = {'bitcoin-mainnet': 1000, 'ethereum-mainnet': 1}
MAX_BALANCE_POSTS = 1000000
REFUSAL_REASONS = ('bad_signature', 'bad_chain', 'bad_period', 'bad_leaf', 'duplicate_receipt', 'bad_totals', 'unfunded', 'unknown_provider_key')


class Rejected(ValueError):
    """`provable` is True when the fault is shown by the claim and public objects alone, independent of time and funding."""

    def __init__(self, reason, provable=False):
        assert reason in REFUSAL_REASONS
        super().__init__(reason)
        self.reason, self.provable = reason, provable


def seconds(text):
    return int(datetime.strptime(text, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp())


def content_id(prefix, label, obj):
    return prefix + ':' + hashlib.sha256(pre(label, obj)).hexdigest()


def without(obj, *names):
    return {k: v for k, v in obj.items() if k not in names}


def object_hash(obj):
    return hashlib.sha256(rfc8785.dumps(obj)).hexdigest()


# ---- Release keys and threshold signatures
def release_sign(label, body, signers=None):
    signers = RELEASE_KEYS[:RELEASE_THRESHOLD] if signers is None else signers
    return sorted(({'release_key_id': did(k), 'signature': sign(k, label, body)} for k in signers), key=lambda e: e['release_key_id'])


def check_threshold(label, body, entries, release_ids, threshold):
    ids = [e['release_key_id'] for e in entries]
    if ids != sorted(set(ids)):
        raise ValueError('release signatures order')
    good = 0
    for e in entries:
        if e['release_key_id'] in release_ids:
            verify(e['release_key_id'], label, body, e['signature'])
            good += 1
    if good < threshold:
        raise ValueError('release threshold')


# ---- Plain RFC 6962 tree for the Foundation log
def _split(n):
    k = 1
    while k * 2 < n:
        k *= 2
    return k


def _mth(hashes):
    if len(hashes) == 1:
        return hashlib.sha256(b'\x00' + hashes[0]).digest()
    k = _split(len(hashes))
    return hashlib.sha256(b'\x01' + _mth(hashes[:k]) + _mth(hashes[k:])).digest()


def _mpath(index, hashes):
    if len(hashes) == 1:
        return []
    k = _split(len(hashes))
    if index < k:
        return _mpath(index, hashes[:k]) + [_mth(hashes[k:])]
    return _mpath(index - k, hashes[k:]) + [_mth(hashes[:k])]


def _sides(index, count):
    """For each level from leaf to root, the side on which the sibling sits."""
    if not 0 <= index < count:
        raise ValueError('leaf index')
    sides, n, i = [], count, index
    while n > 1:
        k = _split(n)
        if i < k:
            sides.append('right'); n = k
        else:
            sides.append('left'); i -= k; n -= k
    sides.reverse()
    return sides


class FoundationLog:
    def __init__(self):
        self.entries = []

    def append(self, kind, obj):
        self.entries.append({'index': len(self.entries), 'kind': kind, 'object_hash': object_hash(obj)})
        return obj

    def root(self, size=None):
        size = len(self.entries) if size is None else size
        return _mth([bytes.fromhex(e['object_hash']) for e in self.entries[:size]]).hex()

    def proof(self, obj, size):
        h = object_hash(obj)
        index = next(e['index'] for e in self.entries[:size] if e['object_hash'] == h)
        hashes = [bytes.fromhex(e['object_hash']) for e in self.entries[:size]]
        return {'index': index, 'size': size, 'audit_path': [p.hex() for p in _mpath(index, hashes)]}


def log_root_from_proof(obj, proof):
    sides = _sides(proof['index'], proof['size'])
    if len(sides) != len(proof['audit_path']):
        raise ValueError('path length')
    node = hashlib.sha256(b'\x00' + bytes.fromhex(object_hash(obj))).digest()
    for side, p in zip(sides, map(bytes.fromhex, proof['audit_path'])):
        node = hashlib.sha256(b'\x01' + (node + p if side == 'right' else p + node)).digest()
    return node.hex()


# ---- Release key set updates
def key_set_update(sequence, new_keys, new_threshold, effective_at, signers=None, previous=None, prior_objects=()):
    u = {'sequence': sequence, 'previous_update_id': None if previous is None else previous['update_id'],
         'release_key_ids': sorted(did(k) for k in new_keys), 'release_threshold': new_threshold,
         'prior_objects': sorted(object_hash(o) for o in prior_objects), 'effective_at': effective_at}
    u['update_id'] = content_id('fyku2', 'release-key-set-update-id', u)
    u['release_signatures'] = release_sign('release-key-set-update', u, signers)
    return u


def valid_key_set(ids, threshold):
    """At least five keys and a threshold of at least two-thirds, rounded up."""
    return len(ids) >= 5 and len(ids) >= threshold and threshold * 3 >= 2 * len(ids)


def apply_key_set_updates(release_ids, threshold, updates):
    """Apply updates in order from the genesis set. Returns the timeline [(effective_at or None, ids, threshold)].
    Each update is signed by the previous set's threshold; a fork of the chain stops everything."""
    by_sequence = {}
    for u in updates:
        if by_sequence.setdefault(u['sequence'], u)['update_id'] != u['update_id']:
            raise ValueError('forked root of trust')
    timeline, ids, previous = [(None, set(release_ids), threshold)], set(release_ids), None
    for expected in range(1, len(by_sequence) + 1):
        u = by_sequence.get(expected)
        if u is None or not valid_key_set(set(u['release_key_ids']), u['release_threshold']):
            raise ValueError('key set update')
        if u['update_id'] != content_id('fyku2', 'release-key-set-update-id', without(u, 'update_id', 'release_signatures')):
            raise ValueError('update ID')
        if u['previous_update_id'] != (None if previous is None else previous['update_id']):
            raise ValueError('update chain')
        if previous is not None and seconds(u['effective_at']) <= seconds(previous['effective_at']):
            raise ValueError('update order')
        check_threshold('release-key-set-update', without(u, 'release_signatures'), u['release_signatures'], ids, threshold)
        ids, threshold, previous = set(u['release_key_ids']), u['release_threshold'], u
        timeline.append((u['effective_at'], ids, threshold, set(u['prior_objects'])))
    return timeline


def key_set_at(timeline, at, obj=None):
    """The set in force at a signed time. An object signed under a superseded set must be listed by the update that replaced it."""
    t = seconds(at)
    index = 0
    for n, entry in enumerate(timeline[1:], 1):
        if seconds(entry[0]) <= t:
            index = n
    if obj is not None and index + 1 < len(timeline) and object_hash(obj) not in timeline[index + 1][3]:
        raise ValueError('not carried over by the key-set update')
    return timeline[index][1], timeline[index][2]


# ---- Foundation key certificate, log heads and closure
def key_certificate(foundation=FOUNDATION, valid_from='2026-10-01T00:00:00Z', valid_until='2027-10-01T00:00:00Z', signers=None, recipients=None, issued_at='2026-09-01T00:00:00Z'):
    c = {'foundation_id': did(foundation), 'recipients': dict(recipients or RECIPIENTS), 'issued_at': issued_at, 'valid_from': valid_from, 'valid_until': valid_until}
    c['certificate_id'] = content_id('fyfc2', 'foundation-key-certificate-id', c)
    c['release_signatures'] = release_sign('foundation-key-certificate', c, signers)
    return c


def check_certificate(c, release_ids, threshold=RELEASE_THRESHOLD, genesis=False):
    if c['certificate_id'] != content_id('fyfc2', 'foundation-key-certificate-id', without(c, 'certificate_id', 'release_signatures')):
        raise ValueError('certificate ID')
    if not 0 < seconds(c['valid_until']) - seconds(c['valid_from']) <= 366 * DAY:
        raise ValueError('certificate validity')
    if not genesis and seconds(c['valid_from']) - seconds(c['issued_at']) < 30 * DAY:
        raise ValueError('certificate notice')
    check_threshold('foundation-key-certificate', without(c, 'release_signatures'), c['release_signatures'], release_ids, threshold)


def log_head(log, signed_at, size=None, key=FOUNDATION):
    size = len(log.entries) if size is None else size
    h = {'foundation_id': did(key), 'size': size, 'root': log.root(size) if size else '00' * 32, 'signed_at': signed_at}
    h['foundation_signature'] = sign(key, 'foundation-log-head', h)
    return h


def key_closure(foundation, closed_at, log, size=None, signers=None, voided=(), head=None):
    head = log_head(log, closed_at, size=size, key=foundation) if head is None else head
    r = {'foundation_id': did(foundation), 'closed_at': closed_at, 'head': head, 'voided': sorted(voided)}
    r['release_signatures'] = release_sign('foundation-key-closure', r, signers)
    return r


class Trust:
    """What a verifier pins: the release key set, plus certificates, closures and log heads it has verified."""

    def __init__(self, certificates, closures=(), heads=(), release_keys=RELEASE_KEYS, threshold=RELEASE_THRESHOLD, updates=(), genesis_certificates=1):
        self.release_ids = {did(k) for k in release_keys}
        self.threshold = threshold
        if not valid_key_set(self.release_ids, threshold):
            raise ValueError('release key set')
        self.timeline = apply_key_set_updates(self.release_ids, threshold, updates)
        self.certificates = []
        for n, c in enumerate(certificates):
            ids, thr = key_set_at(self.timeline, c['issued_at'], c)
            check_certificate(c, ids, thr, genesis=n < genesis_certificates)
            self.certificates.append(c)
        self.heads = []
        for h in heads:
            verify(h['foundation_id'], 'foundation-log-head', without(h, 'foundation_signature'), h['foundation_signature'])
            self.heads.append(h)
        self.closures = {}
        for r in closures:
            ids, thr = key_set_at(self.timeline, r['closed_at'])
            check_threshold('foundation-key-closure', without(r, 'release_signatures'), r['release_signatures'], ids, thr)
            head = r['head']
            if head['foundation_id'] != r['foundation_id']:
                raise ValueError('closure head')
            verify(head['foundation_id'], 'foundation-log-head', without(head, 'foundation_signature'), head['foundation_signature'])
            self.closures[r['foundation_id']] = r  # authoritative once it verifies

    def closure_evidence(self):
        """Heads larger than a closure's head: evidence for monitors to publish, never a veto."""
        return [h for h in self.heads for r in self.closures.values()
                if h['foundation_id'] == r['foundation_id'] and h['size'] > r['head']['size']]

    def release_set(self, at, obj=None):
        return key_set_at(self.timeline, at, obj)

    def recipients(self, network, at):
        """Recipients of every certificate whose key is open at that time."""
        t = seconds(at)
        out = set()
        for c in self.certificates:
            closure = self.closures.get(c['foundation_id'])
            if t >= seconds(c['valid_from']) and (closure is None or t < seconds(closure['closed_at'])):
                out.add(c['recipients'][network])
        return out

    def verify_foundation(self, obj, signed_time, label, log_proof=None):
        fid, t = obj['foundation_id'], seconds(signed_time)
        if not any(c['foundation_id'] == fid and seconds(c['valid_from']) <= t < seconds(c['valid_until']) for c in self.certificates):
            raise ValueError('foundation key not certified at the signed time')
        verify(fid, label, without(obj, 'foundation_signature'), obj['foundation_signature'])
        closure = self.closures.get(fid)
        if closure is None:
            return
        head = closure['head']
        if log_proof is None or log_proof['size'] != head['size'] or head['size'] == 0:
            raise ValueError('closed key: log proof required')
        if log_root_from_proof(obj, log_proof) != head['root']:
            raise ValueError('object not in the closed log')
        if object_hash(obj) in closure['voided']:
            raise ValueError('object voided by the closure')


def heads_conflict(log_a_hashes, head_a, log_b_hashes, head_b):
    """Two heads from one key conflict when the smaller log is not a prefix of the larger."""
    small, big = sorted(((head_a, log_a_hashes), (head_b, log_b_hashes)), key=lambda x: x[0]['size'])
    return small[1][:small[0]['size']] != big[1][:small[0]['size']]


# ---- Fee schedule
def fee(schedule, billable_bytes):
    units = (billable_bytes + 1023) // 1024
    return int(schedule['base_fee_base_units']) + int(schedule['per_kib_fee_base_units']) * units


def make_schedule(network, per_kib, revision=1, effective_at='2027-01-01T00:00:00Z', expires_at='2027-07-01T00:00:00Z', base=0):
    s = {'profile_major': 2, 'profile_minor': 0, 'revision': revision, 'network': network,
         'denomination': RATES[network][0], 'base_fee_base_units': str(base), 'per_kib_fee_base_units': str(per_kib),
         'effective_at': effective_at, 'expires_at': expires_at}
    s['schedule_id'] = content_id('fyfs2', 'fee-schedule-id', s)
    return s


def schedule_1(network):
    return make_schedule(network, RATES[network][1])


def approve(schedule, at='2026-11-01T00:00:00Z', signers=None, drift=False):
    a = {'schedule_id': schedule['schedule_id'], 'approved_at': at, 'drift': drift}
    a['release_signatures'] = release_sign('fee-schedule-approval', a, signers)
    return a


def check_approval(schedule, approval, trust, previous=None):
    if schedule['schedule_id'] != content_id('fyfs2', 'fee-schedule-id', without(schedule, 'schedule_id')):
        raise ValueError('schedule ID')
    if int(schedule['base_fee_base_units']) == 0 and int(schedule['per_kib_fee_base_units']) == 0:
        raise ValueError('zero schedule')
    if approval['schedule_id'] != schedule['schedule_id']:
        raise ValueError('approval binding')
    notice = (14 if approval['drift'] else 60) * DAY
    if seconds(schedule['effective_at']) - seconds(approval['approved_at']) < notice:
        raise ValueError('notice period')
    ids, thr = trust.release_set(approval['approved_at'], approval)
    check_threshold('fee-schedule-approval', without(approval, 'release_signatures'), approval['release_signatures'], ids, thr)
    if schedule['revision'] == 1:
        if previous is not None or approval['drift']:
            raise ValueError('revision')
        return
    if previous is None or previous['network'] != schedule['network'] or schedule['revision'] != previous['revision'] + 1:
        raise ValueError('revision')
    gap = seconds(schedule['effective_at']) - seconds(previous['effective_at'])
    if gap < (30 if approval['drift'] else 90) * DAY or seconds(approval['approved_at']) < seconds(previous['effective_at']):
        raise ValueError('revision spacing')
    for size in (1024, 1048576):  # the fee of a 1 KiB post and of a 1 MiB post
        old, new = fee(previous, size), fee(schedule, size)
        if not (old <= 2 * new and new <= 2 * old):
            raise ValueError('revision bound')


def in_force(schedules, network, at):
    """The schedule with the greatest effective_at not later than `at`; expires_at never stops admission."""
    t = seconds(at)
    live = [s for s in schedules if s['network'] == network and seconds(s['effective_at']) <= t]
    if not live:
        raise ValueError('no schedule in force')
    return max(live, key=lambda s: seconds(s['effective_at']))


def schedules_in_force_during(schedules, network, at, window=3600):
    """IDs of every schedule in force at some instant in the `window` seconds ending at `at`."""
    t = seconds(at)
    ids = {s['schedule_id'] for s in schedules if s['network'] == network and t - window < seconds(s['effective_at']) <= t}
    earlier = [s for s in schedules if s['network'] == network and seconds(s['effective_at']) <= t - window]
    if earlier:
        ids.add(max(earlier, key=lambda s: seconds(s['effective_at']))['schedule_id'])
    return ids


def possible_fee(schedule, amount):
    base, rate = int(schedule['base_fee_base_units']), int(schedule['per_kib_fee_base_units'])
    if rate == 0:
        return amount == base
    k, rem = divmod(amount - base, rate)
    return rem == 0 and 1 <= k <= 1024


def drift_allows_revision(daily_values_micro_usd, target=100):
    """30 consecutive days below half or above twice the target (millionths of a US dollar per KiB)."""
    run_low = run_high = 0
    for v in daily_values_micro_usd:
        run_low = run_low + 1 if 2 * v < target else 0
        run_high = run_high + 1 if v > 2 * target else 0
        if run_low >= 30 or run_high >= 30:
            return True
    return False


def deposit_allowed(schedule, balance, pending, amount):
    return balance + pending + amount <= MAX_BALANCE_POSTS * fee(schedule, 1024)


# ---- Receipts and leaves
def make_receipt(schedule, text, issued_at='2027-01-05T00:00:00Z', key=PROVIDER):
    intent = json.loads(json.dumps(I))
    intent['payload']['text'] = text
    ident = mid(intent)
    r = {'provider_id': did(key), 'author_id': intent['author_id'], 'message_id': ident,
         'receipt_id': b64(hashlib.sha256(('receipt ' + ident + issued_at + did(key)).encode()).digest()),
         'quote_id': 'fyfq2:' + hashlib.sha256(ident.encode()).hexdigest(), 'schedule_id': schedule['schedule_id'],
         'network': schedule['network'], 'amount_base_units': str(fee(schedule, len(rfc8785.dumps(intent)))),
         'authorization_at': issued_at, 'issued_at': issued_at}
    r['provider_signature'] = sign(key, 'receipt', r)
    return r


def leaf_of(receipt):
    return {'receipt_hash': object_hash(receipt), 'schedule_id': receipt['schedule_id'],
            'amount_base_units': receipt['amount_base_units'], 'issued_at': receipt['issued_at']}


# ---- Merkle sum tree, RFC 6962 shape
def _u128(n):
    if not 0 <= n < 2 ** 128:
        raise ValueError('sum range')
    return n.to_bytes(16, 'big')


def _leaf_node(leaf):
    return hashlib.sha256(b'\x00' + pre('settlement-leaf', leaf)).digest(), int(leaf['amount_base_units'])


def _join(left, right):
    return hashlib.sha256(b'\x01' + left[0] + _u128(left[1]) + right[0] + _u128(right[1])).digest(), left[1] + right[1]


def _root(nodes):
    if len(nodes) == 1:
        return nodes[0]
    k = _split(len(nodes))
    return _join(_root(nodes[:k]), _root(nodes[k:]))


def _path(index, nodes):
    if len(nodes) == 1:
        return []
    k = _split(len(nodes))
    if index < k:
        return _path(index, nodes[:k]) + [_root(nodes[k:])]
    return _path(index - k, nodes[k:]) + [_root(nodes[:k])]


def sort_leaves(leaves):
    return sorted(leaves, key=lambda leaf: leaf['receipt_hash'])


def tree_root(leaves):
    if not leaves:
        raise ValueError('no receipts')
    h, total = _root([_leaf_node(leaf) for leaf in leaves])
    return h.hex(), total


def audit_path(index, leaves):
    return [{'hash': h.hex(), 'sum': str(s)} for h, s in _path(index, [_leaf_node(leaf) for leaf in leaves])]


def root_from_path(leaf, index, count, path):
    sides = _sides(index, count)
    if len(sides) != len(path):
        raise ValueError('path length')
    node = _leaf_node(leaf)
    for side, p in zip(sides, path):
        if not (isinstance(p['sum'], str) and p['sum'].isdigit() and (p['sum'] == '0' or p['sum'][0] != '0')):
            raise ValueError('sibling sum')
        sibling = (bytes.fromhex(p['hash']), int(p['sum']))
        node = _join(node, sibling) if side == 'right' else _join(sibling, node)
    return node[0].hex(), node[1]


# ---- Settlement deposits (public chain) and the claim chain
def deposit_commitment(provider_id, network):
    return hashlib.sha256(pre('settlement-deposit', {'provider_id': provider_id, 'network': network})).hexdigest()


class Chain:
    """Synthetic confirmed transfers: (network, recipient, chain units, data, block time)."""

    def __init__(self):
        self.transfers = []

    def deposit(self, provider_id, network, units, recipient=None, data=None, at='2026-12-20T00:00:00Z'):
        self.transfers.append((network, RECIPIENTS[network] if recipient is None else recipient, units,
                               deposit_commitment(provider_id, network) if data is None else data, at))

    def deposited(self, provider_ids, network, trust):
        """Base units any observer credits to a provider (all keys of one succession line)."""
        ids = [provider_ids] if isinstance(provider_ids, str) else list(provider_ids)
        want = {deposit_commitment(p, network) for p in ids}
        total = 0
        for net, recipient, units, data, at in self.transfers:
            if net == network and data in want and units >= MIN_DEPOSIT[network] and recipient in trust.recipients(network, at):
                total += units * CHAIN_TO_BASE[network]
        return total


def make_claim(key, network, leaves, start, end, declaration_id, previous=None):
    leaves = sort_leaves(leaves)
    root, total = tree_root(leaves)
    claim = {'provider_id': did(key), 'network': network,
             'sequence': 1 if previous is None else previous['sequence'] + 1,
             'previous_claim_id': None if previous is None else previous['claim_id'],
             'period_start': start, 'period_end': end, 'declaration_id': declaration_id,
             'receipt_count': len(leaves), 'total_base_units': str(total),
             'cumulative_base_units': str(total + (0 if previous is None else int(previous['cumulative_base_units']))),
             'receipts_root': root}
    claim['claim_id'] = content_id('fysc2', 'settlement-claim-id', claim)
    claim['provider_signature'] = sign(key, 'settlement-claim', claim)
    return claim, leaves


def check_claim_object(claim):
    if claim['claim_id'] != content_id('fysc2', 'settlement-claim-id', without(claim, 'claim_id', 'provider_signature')):
        raise ValueError('claim ID')
    verify(claim['provider_id'], 'settlement-claim', without(claim, 'provider_signature'), claim['provider_signature'])


def check_link(claim, previous, successors=None):
    """Chain rules between a claim and its predecessor (None for sequence 1)."""
    prior = 0 if previous is None else int(previous['cumulative_base_units'])
    same_line = previous is None or previous['provider_id'] == claim['provider_id'] or (successors or {}).get(previous['provider_id']) == claim['provider_id']
    if previous is not None and (not same_line or previous['network'] != claim['network']):
        raise ValueError('key')
    if not (claim['sequence'] == (1 if previous is None else previous['sequence'] + 1)
            and claim['previous_claim_id'] == (None if previous is None else previous['claim_id'])
            and int(claim['cumulative_base_units']) == prior + int(claim['total_base_units'])):
        raise ValueError('chain')
    span = seconds(claim['period_end']) - seconds(claim['period_start'])
    if not 0 < span <= 24 * HOUR or (previous is not None and seconds(claim['period_start']) < seconds(previous['period_end'])):
        raise ValueError('period')


def quorum(committee):
    """More than two-thirds of the committee: 4 of 5, 5 of 7. Safe while fewer than one-third are faulty."""
    return 2 * len(set(committee)) // 3 + 1


def max_faulty(committee):
    """The largest number of faulty monitors the assumption allows: the largest integer below n/3."""
    return (len(set(committee)) - 1) // 3


def max_replaced(committee):
    """A committee change replaces at most q - f - 1 monitors, so an honest witness of any settled claim stays."""
    return quorum(committee) - max_faulty(committee) - 1


def check_committee_change(old, new):
    """Either replace (same size, at most q - f - 1 replaced) or add (none removed, at most q - f - 1 added)."""
    old, new = set(old), set(new)
    limit = max_replaced(old)
    replace = len(old) == len(new) and len(old - new) <= limit
    add = old < new and len(new - old) <= limit
    if not (replace or add or old == new):
        raise ValueError('committee change outside the bounds')


WITNESSED_FIELDS = ('claim_id', 'provider_id', 'network', 'sequence', 'period_end', 'total_base_units', 'cumulative_base_units', 'receipts_root')


class Monitor:
    """One member of the settlement committee. It audits published claims from public data and signs a witness or a refusal.
    State: the claim it witnessed at each sequence, the receipt hashes it has seen, declarations and successions."""

    def __init__(self, key, trust, chain, schedules):
        self.key, self.trust, self.chain, self.schedules = key, trust, chain, schedules
        self.witnessed, self.seen, self.declarations, self.successors = {}, {}, {}, {}
        self.followed, self.succession_at, self.holds = {}, {}, []
        self.equivocations = []

    def line(self, provider_id):
        back = {new: old for old, new in self.successors.items()}
        while provider_id in back:
            provider_id = back[provider_id]
        return provider_id

    def line_keys(self, provider_id):
        keys = [self.line(provider_id)]
        while keys[-1] in self.successors:
            keys.append(self.successors[keys[-1]])
        return keys

    def register_succession(self, s):
        """A provider succession is accepted only onto an unused key, so no deposit is counted for two chains."""
        check_succession(s)
        if self.successors.get(s['old_id']) == s['new_id']:
            return
        new, involved = s['new_id'], set(self.successors) | set(self.successors.values())
        if s['old_id'] in self.successors or new in involved:
            raise ValueError('conflicting succession')
        if any(c['provider_id'] == new for c in self.witnessed.values()):
            raise ValueError('successor key already signed claims')
        if any(c['provider_id'] == s['old_id'] and seconds(c['period_end']) > seconds(s['effective_at']) for c in self.witnessed.values()):
            raise ValueError('succession dated before a claim the old key already published')
        self.successors[s['old_id']] = new
        self.succession_at[s['old_id']] = s['effective_at']

    def register_declaration(self, d):
        if d['declaration_id'] != content_id('fyrd2', 'retention-declaration-id', without(d, 'declaration_id', 'provider_signature')):
            raise ValueError('declaration ID')
        verify(d['provider_id'], 'retention-declaration', without(d, 'provider_signature'), d['provider_signature'])
        self.declarations.setdefault(self.line(d['provider_id']), []).append(d)

    def governing_declaration(self, provider_id, period_start):
        live = [d for d in self.declarations.get(self.line(provider_id), []) if seconds(d['effective_at']) <= seconds(period_start)]
        return max(live, key=lambda d: seconds(d['effective_at']))['declaration_id'] if live else None

    def check(self, claim, leaves, seen_at, lateness=True):
        try:
            check_claim_object(claim)
        except ValueError:
            raise Rejected('bad_signature', True)
        chain_key = (self.line(claim['provider_id']), claim['network'])
        previous = self.predecessor(chain_key + (claim['sequence'] - 1,))
        if previous is None and claim['sequence'] > 1:
            known = [c for (line, net, seq), c in self.witnessed.items() if c['claim_id'] == claim['previous_claim_id']]
            raise Rejected('unknown_provider_key' if known else 'bad_chain')
        try:
            check_link(claim, previous, self.successors)
        except ValueError as e:
            raise Rejected({'key': 'unknown_provider_key', 'chain': 'bad_chain', 'period': 'bad_period'}[str(e)], str(e) != 'key')
        signer = claim['provider_id']
        if signer in self.succession_at and seconds(claim['period_end']) > seconds(self.succession_at[signer]):
            raise Rejected('unknown_provider_key')  # the old key signs only periods that end by the succession
        old = next((o for o, n in self.successors.items() if n == signer), None)
        if old is not None and seconds(claim['period_start']) < seconds(self.succession_at[old]):
            raise Rejected('unknown_provider_key')  # the new key signs only periods that start at or after it
        age = seconds(seen_at) - seconds(claim['period_end'])
        if age < 0 or (lateness and age > 90 * DAY):
            raise Rejected('bad_period')
        if claim['declaration_id'] != self.governing_declaration(claim['provider_id'], claim['period_start']):
            raise Rejected('bad_period')  # a provider can sign a declaration later, so this is never proof
        if previous is not None and claim['declaration_id'] != previous['declaration_id']:
            new = next(d for d in self.declarations[self.line(claim['provider_id'])] if d['declaration_id'] == claim['declaration_id'])
            if seconds(new['effective_at']) < seconds(previous['period_end']):
                raise Rejected('bad_period')  # a declaration cannot be backdated over periods already claimed
        hashes = [leaf['receipt_hash'] for leaf in leaves]
        if leaves != sort_leaves(leaves) or len(set(hashes)) != len(hashes) or not 1 <= len(leaves) <= 10000:
            raise Rejected('bad_leaf', True)
        for leaf in leaves:
            if not seconds(claim['period_start']) <= seconds(leaf['issued_at']) < seconds(claim['period_end']):
                raise Rejected('bad_leaf', True)
            schedule = next((s for s in self.schedules if s['schedule_id'] == leaf['schedule_id']), None)
            if schedule is None:
                raise Rejected('bad_leaf')  # a schedule this monitor has not fetched proves nothing
            if (leaf['schedule_id'] not in schedules_in_force_during(self.schedules, claim['network'], leaf['issued_at'])
                    or not possible_fee(schedule, int(leaf['amount_base_units']))):
                raise Rejected('bad_leaf', True)
            if self.seen.get((chain_key, leaf['receipt_hash']), claim['sequence']) != claim['sequence']:
                raise Rejected('duplicate_receipt', True)
        root, total = tree_root(leaves)
        if claim['receipt_count'] != len(leaves) or int(claim['total_base_units']) != total or claim['receipts_root'] != root:
            raise Rejected('bad_totals', True)
        credit = self.chain.deposited(self.line(claim['provider_id']), claim['network'], self.trust) - int(claim['cumulative_base_units'])
        if credit < 0:
            raise Rejected('unfunded')
        return credit

    def predecessor(self, slot):
        """The claim this monitor chains from at a sequence: the settled claim it follows, else its own witness."""
        return self.followed.get(slot) or self.witnessed.get(slot)

    def follow(self, settled_claim, witnesses, committee):
        """A monitor that witnessed a different claim where another one settled keeps its witness, records the
        equivocation and chains later sequences from the settled claim."""
        slot = (self.line(settled_claim['provider_id']), settled_claim['network'], settled_claim['sequence'])
        held = self.witnessed.get(slot)
        if held is None or held['claim_id'] == settled_claim['claim_id']:
            raise ValueError('nothing to follow')
        check_claim_object(settled_claim)
        good = set()
        for w in witnesses:
            if w['witness_id'] in committee and all(w[f] == settled_claim[f] for f in WITNESSED_FIELDS):
                verify(w['witness_id'], 'settlement-witness', without(w, 'witness_signature'), w['witness_signature'])
                good.add(w['witness_id'])
        if len(good) < quorum(committee):
            raise ValueError('not settled')
        self.equivocations.append((held, settled_claim))
        self.followed[slot] = settled_claim

    def _refuse(self, claim, reason, at):
        r = {'witness_id': did(self.key), 'claim_id': claim.get('claim_id'), 'provider_id': claim['provider_id'],
             'network': claim['network'], 'sequence': claim['sequence'], 'reason': reason, 'refused_at': at}
        r['witness_signature'] = sign(self.key, 'settlement-refusal', r)
        return 'refused', r

    def audit(self, claim, leaves, seen_at, lateness=True):
        """Returns ('witnessed', witness) or ('refused', refusal). The first witness at a sequence is final:
        the monitor never signs a second claim there, whatever its claim_id."""
        slot = (self.line(claim['provider_id']), claim['network'], claim['sequence'])
        held = self.witnessed.get(slot)
        if held is not None and held['claim_id'] != claim['claim_id']:
            try:
                check_claim_object(claim)
                self.equivocations.append((held, claim))
            except ValueError:
                pass
            return self._refuse(claim, 'bad_chain', seen_at)
        mine = [h for h in self.holds if (self.line(h['provider_id']), h['network'], h['sequence']) == slot]
        if held is None and mine:
            if any(h['claim_ids'] != [claim.get('claim_id')] for h in mine):
                return self._refuse(claim, 'bad_chain', seen_at)  # its own hold stands: it witnesses nothing at this sequence
            self.holds = [h for h in self.holds if h not in mine]  # a hold on this one claim alone ends when it passes audit
        try:
            credit = self.check(claim, leaves, seen_at, lateness)
        except Rejected as e:
            return self._refuse(claim, e.reason, seen_at)
        self.witnessed[slot] = claim
        for leaf in leaves:
            self.seen[(slot[:2], leaf['receipt_hash'])] = claim['sequence']
        return 'witnessed', self._witness(claim, credit, seen_at)

    def _witness(self, claim, credit, at):
        w = {'witness_id': did(self.key)}
        w.update({k: claim[k] for k in WITNESSED_FIELDS})
        w.update(credit_base_units=str(credit), witnessed_at=at)
        w['witness_signature'] = sign(self.key, 'settlement-witness', w)
        return w

    def takeover(self, candidates, outgoing_committee, at, holds=(), past_members=(), ancestors=()):
        """Handover at one sequence. candidates: [(claim, leaves or None, committee witnesses held for it)]: the provider-signed
        claim objects gathered from every continuing monitor's page and any other source; `holds` are the continuing monitors' holds;
        `past_members` are earlier committee members whose witnesses also make a claim known.
        Returns a witness, or None when it must witness nothing (it then publishes a hold).
        A claim blocks unless it is PROVEN invalid from the claim and public objects the newcomer holds."""
        members = set(outgoing_committee) | set(past_members)
        valid, blocking, known = [], 0, set()
        by_id = {claim['claim_id']: (claim, leaves) for claim, leaves, _ in candidates}
        held_ids = {cid for h in holds for cid in h['claim_ids'] if h.get('witness_id') in outgoing_committee and self._hold_ok(h)}
        for claim, leaves, witnesses in candidates:
            good, outgoing = set(), set()
            for w in witnesses:
                try:
                    if w['witness_id'] in members and all(w[f] == claim[f] for f in WITNESSED_FIELDS):
                        verify(w['witness_id'], 'settlement-witness', without(w, 'witness_signature'), w['witness_signature'])
                        good.add(w['witness_id'])
                        if w['witness_id'] in outgoing_committee:
                            outgoing.add(w['witness_id'])
                except (ValueError, KeyError):
                    continue
            if not good and claim['claim_id'] not in held_ids:
                continue
            known.add(claim['claim_id'])
            if len(outgoing) >= quorum(outgoing_committee):
                chain = ancestors.get(claim['claim_id'], ()) if isinstance(ancestors, dict) else ancestors
                return self.adopt(claim, witnesses, outgoing_committee, at, ancestors=chain)
            if leaves is None:
                try:
                    check_claim_object(claim)
                    blocking += 1  # signed by the provider but not auditable: not proven invalid
                except ValueError:
                    pass  # not a claim the provider signed
                continue
            try:
                self.check(claim, leaves, at, lateness=False)
                valid.append((claim, leaves))
            except Rejected as e:
                if not e.provable:
                    blocking += 1
        # A claim named in a hold counts only when its provider-signed claim object was produced (it is then a candidate).
        if len(valid) == 1 and not blocking:
            only = valid[0][0]
            slot = (self.line(only['provider_id']), only['network'], only['sequence'])
            self.holds = [h for h in self.holds if (self.line(h['provider_id']), h['network'], h['sequence']) != slot]
            kind, result = self.audit(valid[0][0], valid[0][1], at, lateness=False)
            return result if kind == 'witnessed' else None
        if known and candidates:
            first = candidates[0][0]
            h = {'witness_id': did(self.key), 'provider_id': first['provider_id'], 'network': first['network'],
                 'sequence': first['sequence'], 'claim_ids': sorted(known), 'held_at': at}
            h['witness_signature'] = sign(self.key, 'settlement-hold', h)
            self.holds.append(h)
        return None

    @staticmethod
    def _hold_ok(h):
        try:
            verify(h['witness_id'], 'settlement-hold', without(h, 'witness_signature'), h['witness_signature'])
            return True
        except (ValueError, KeyError):
            return False

    def adopt(self, claim, outgoing_witnesses, outgoing_committee, at, successions=(), ancestors=()):
        """Handover or catching up: adopt the claim that a quorum of a committee (the outgoing one, or the current one
        for a monitor that missed a sequence) witnessed. It checks the claim, its link, the witnesses and the deposits;
        it does not re-apply lateness or leaf rules. `successions` are the key successions the adopted claims imply."""
        for s in successions:
            self.register_succession(s)
        slot = (self.line(claim['provider_id']), claim['network'], claim['sequence'])
        held = self.witnessed.get(slot)
        if held is not None and held['claim_id'] != claim['claim_id']:
            raise ValueError('already holds another claim at this sequence')
        check_claim_object(claim)
        good = set()
        for w in outgoing_witnesses:
            if w['witness_id'] in outgoing_committee and all(w[f] == claim[f] for f in WITNESSED_FIELDS):
                verify(w['witness_id'], 'settlement-witness', without(w, 'witness_signature'), w['witness_signature'])
                good.add(w['witness_id'])
        if len(good) < quorum(outgoing_committee):
            raise ValueError('no quorum for this claim')
        # A settled claim settles its ancestors: the monitor takes them as predecessors, whatever it held there.
        chain = list(ancestors) + [claim]
        for older, newer in zip(chain, chain[1:]):
            check_claim_object(older)
            check_link(newer, older, self.successors)
        for older in ancestors:
            a_slot = (self.line(older['provider_id']), older['network'], older['sequence'])
            mine = self.witnessed.get(a_slot)
            if mine is None or mine['claim_id'] != older['claim_id']:
                if mine is not None:
                    self.equivocations.append((mine, older))
                self.followed[a_slot] = older
            self.holds = [h for h in self.holds if (self.line(h['provider_id']), h['network'], h['sequence']) != a_slot]
        check_link(claim, self.predecessor(slot[:2] + (claim['sequence'] - 1,)), self.successors)
        credit = self.chain.deposited(self.line(claim['provider_id']), claim['network'], self.trust) - int(claim['cumulative_base_units'])
        if credit < 0:
            raise ValueError('unfunded')
        self.witnessed[slot] = claim
        return self._witness(claim, credit, at)


def committee_audit(monitors, claim, leaves, seen_at):
    """Every committee monitor audits the claim. Returns (witnesses, refusals)."""
    results = [m.audit(claim, leaves, seen_at) for m in monitors]
    return [r for kind, r in results if kind == 'witnessed'], [r for kind, r in results if kind == 'refused']


def equivocation(a, b):
    """True when two claims prove that a provider signed two claims at one sequence."""
    try:
        check_claim_object(a); check_claim_object(b)
    except ValueError:
        return False
    return (a['provider_id'] == b['provider_id'] and a['network'] == b['network'] and a['sequence'] == b['sequence']
            and a['claim_id'] != b['claim_id'])


def make_proof(claim, leaves, index, witnesses=(), chain=()):
    proof = {'claim': claim, 'leaf': leaves[index], 'leaf_index': index, 'audit_path': audit_path(index, leaves), 'witnesses': list(witnesses)}
    if chain:
        proof['chain'] = list(chain)  # later claims linking `claim` to the witnessed one
    return proof


def proof_settles(receipt, proof, committee, previous_committee=(), changed_at=None, successions=None):
    """Steps 1-4. `committee` is the monitor list of the policy in force at the verifier's clock; `previous_committee`
    is given only during the 30 days after a change. Returns the smallest witnessed credit, or None."""
    try:
        claim, leaf = proof['claim'], proof['leaf']
        if leaf['receipt_hash'] != object_hash(receipt):
            raise ValueError('leaf binding')
        for name in ('schedule_id', 'amount_base_units', 'issued_at'):
            if leaf[name] != receipt[name]:
                raise ValueError('leaf binding')
        if claim['provider_id'] != receipt['provider_id'] or claim['network'] != receipt['network']:
            raise ValueError('claim binding')
        check_claim_object(claim)
        root, total = root_from_path(leaf, proof['leaf_index'], claim['receipt_count'], proof['audit_path'])
        if root != claim['receipts_root'] or total != int(claim['total_base_units']):
            raise ValueError('root')
    except (ValueError, KeyError, TypeError):
        return None
    try:
        witnessed = claim
        for later in proof.get('chain', []):  # a settled claim settles its ancestors
            check_claim_object(later)
            check_link(later, witnessed, successions)  # same key, or a succession the verifier has verified
            witnessed = later
    except (ValueError, KeyError, TypeError):
        return None
    claim = witnessed
    good, credits = set(), {}
    for w in proof.get('witnesses', []):
        try:
            if any(w[f] != claim[f] for f in WITNESSED_FIELDS):
                continue
            if seconds(w['witnessed_at']) < seconds(claim['period_end']):
                continue
            verify(w['witness_id'], 'settlement-witness', without(w, 'witness_signature'), w['witness_signature'])
            good.add(w['witness_id']); credits[w['witness_id']] = int(w['credit_base_units'])
        except (ValueError, KeyError):
            continue
    times = {w['witness_id']: seconds(w['witnessed_at']) for w in proof.get('witnesses', []) if w.get('witness_id') in good}
    current = set(committee)
    if current and len(good & current) >= quorum(current):
        return min(credits[m] for m in good & current)
    # The previous committee counts during the handover only, and only with witnesses made before the change.
    old = {m for m in set(previous_committee) & good if changed_at is not None and times[m] < seconds(changed_at)}
    if previous_committee and len(old) >= quorum(previous_committee):
        return min(credits[m] for m in old)
    return None


def receipt_state(receipt, proof, committee, **kw):
    """settled or not; pending is decided by pending_states."""
    return 'settled' if proof is not None and proof_settles(receipt, proof, committee, **kw) is not None else 'unsettled'


PENDING_LIMIT = 7 * DAY


def new_delinquencies(unsettled_receipts, now, line=lambda p: p, served=None):
    """(provider line, receipt_id) records a verifier must keep until the receipt settles. Only a receipt whose message
    the verifier obtained from that provider's own read routes (`served`; None means all) can be delinquent."""
    t = seconds(now)
    return {(line(r['provider_id']), r['receipt_id']) for r in unsettled_receipts
            if t - seconds(r['issued_at']) >= PENDING_LIMIT and (served is None or r['receipt_id'] in served)}


def pending_states(unsettled_receipts, now, trusted_providers, records=(), line=lambda p: p, served=None):
    """State of each unsettled receipt. `records` are the delinquency records the verifier already keeps; they outlive
    the messages and follow a key succession through `line`."""
    t = seconds(now)
    blocked = {p for p, _ in set(records) | new_delinquencies(unsettled_receipts, now, line, served)}
    states = []
    for r in unsettled_receipts:
        age = t - seconds(r['issued_at'])
        ok = (r['provider_id'] in trusted_providers and 0 <= age < PENDING_LIMIT and line(r['provider_id']) not in blocked
              and (served is None or r['receipt_id'] in served))
        states.append('pending_settlement' if ok else 'unsettled')
    return states


class Vault:
    """The Foundation's vault: stores a message only with a proof that its receipt is settled by the committee."""

    def __init__(self, committee, key=FOUNDATION):
        self.committee, self.key, self.log, self.held = committee, key, FoundationLog(), {}

    def put(self, receipt, proof, stored_at):
        if proof is None or proof_settles(receipt, proof, self.committee) is None:
            raise ValueError('not_ready')
        message_id = receipt['message_id']
        if message_id not in self.held:
            r = {'foundation_id': did(self.key), 'message_id': message_id, 'stored_at': stored_at}
            r['foundation_signature'] = sign(self.key, 'vault-receipt', r)
            self.held[message_id] = self.log.append('vault_receipt', r)
        return self.held[message_id]


# ---- Retention
def retention_declaration(key, retention_seconds, effective_at, payout=None):
    d = {'provider_id': did(key), 'retention_seconds': retention_seconds, 'payout_recipients': payout or {}, 'effective_at': effective_at}
    d['declaration_id'] = content_id('fyrd2', 'retention-declaration-id', d)
    d['provider_signature'] = sign(key, 'retention-declaration', d)
    return d


def retain_until(issued_at, claim, declarations):
    """Seconds since epoch: receipt issued_at plus the retention of the declaration the claim names."""
    d = next((x for x in declarations if x['declaration_id'] == claim['declaration_id'] and x['provider_id'] == claim['provider_id']), None)
    if d is None:
        raise ValueError('unknown declaration')
    if d['declaration_id'] != content_id('fyrd2', 'retention-declaration-id', without(d, 'declaration_id', 'provider_signature')):
        raise ValueError('declaration ID')
    verify(d['provider_id'], 'retention-declaration', without(d, 'provider_signature'), d['provider_signature'])
    if d['retention_seconds'] < YEAR:
        raise ValueError('retention below minimum')
    return seconds(issued_at) + d['retention_seconds']


# ---- Distribution
def distribution_policy(signers=None, **changes):
    p = {'revision': 1, 'vault_share_bp': 5000, 'monitor_share_bp': 500, 'max_retention_years': 10, 'min_reports': 3,
         'monitors': sorted(did(m) for m in MONITORS), 'approved_at': '2026-10-01T00:00:00Z', 'effective_at': '2027-01-01T00:00:00Z'}
    p.update(changes)
    p['policy_id'] = content_id('fydp2', 'distribution-policy-id', p)
    p['release_signatures'] = release_sign('distribution-policy', p, signers)
    return p


def check_policy(policy, trust, previous=None):
    if policy['policy_id'] != content_id('fydp2', 'distribution-policy-id', without(policy, 'policy_id', 'release_signatures')):
        raise ValueError('policy ID')
    if policy['vault_share_bp'] < 2500 or len(set(policy['monitors'])) < 5 or policy['min_reports'] < 3:
        raise ValueError('policy bounds')
    if not 0 <= policy['monitor_share_bp'] <= min(1000, policy['vault_share_bp']):
        raise ValueError('policy bounds')
    committee_only = previous is not None and all(policy[k] == previous[k] for k in ('vault_share_bp', 'monitor_share_bp', 'max_retention_years', 'min_reports'))
    if previous is not None and set(policy['monitors']) != set(previous['monitors']):
        check_committee_change(previous['monitors'], policy['monitors'])
        if seconds(policy['effective_at']) - seconds(previous['effective_at']) < 30 * DAY:
            raise ValueError('committee changes too close')
    if seconds(policy['effective_at']) - seconds(policy['approved_at']) < (14 if committee_only else 60) * DAY:
        raise ValueError('policy notice')
    ids, thr = trust.release_set(policy['approved_at'], policy)
    check_threshold('distribution-policy', without(policy, 'release_signatures'), policy['release_signatures'], ids, thr)


def lower_median(values):
    ordered = sorted(values)
    return ordered[(len(ordered) - 1) // 2]


def monitor_score(reports, active_days=90):
    """reports: (first_day, end_day_exclusive, known score or None) inside one quarter.
    Overlapping reports are invalid. Needed: 60 covered days with a known score, or two-thirds of the days since the
    provider's first settled claim when it started in this quarter."""
    spans = sorted((a, b) for a, b, _ in reports)
    if any(b <= a for a, b in spans) or any(spans[i][1] > spans[i + 1][0] for i in range(len(spans) - 1)):
        return None
    known = [(b - a, s) for a, b, s in reports if s is not None]
    days = sum(d for d, _ in known)
    if days < min(60, -(-2 * active_days // 3)):
        return None
    return sum(d * s for d, s in known) // days


MIN_PAYOUT = {'bitcoin-mainnet': 10000 * 1000, 'ethereum-mainnet': 10 ** 15}
PAYOUT_UNIT = {'bitcoin-mainnet': 1000, 'ethereum-mainnet': 1}


def distribute(policy, network, start, end, settled_claims, declared_seconds, reports, previous=None, recipients=(), payouts=None, report_ids=None, active_days=None, complete_monitors=None, monitor_answers=None, key=FOUNDATION):
    """settled_claims: the claims counted in the quarter (period_end inside it). declared_seconds: provider -> retention_seconds of the
    declarations its claims named. reports: provider -> {monitor_id: [(first_day, end_day, score)]}.
    previous: the previous quarter's statement (for proven_quarters and accrued amounts)."""
    keep = 10000 - policy['vault_share_bp']
    before = {e['provider_id']: e for e in (previous or {}).get('entries', [])}
    fees = {}
    for a in settled_claims:
        if not seconds(start) <= seconds(a['period_end']) < seconds(end):
            raise ValueError('claim outside the quarter')
        fees[a['provider_id']] = fees.get(a['provider_id'], 0) + int(a['total_base_units'])
    entries, distributed = [], 0
    for p in sorted(set(fees) | {q for q, e in before.items() if int(e['accrued_base_units'])}):
        paid_in = fees.get(p, 0)
        scores = [s for s in (monitor_score(r, (active_days or {}).get(p, 90)) for m, r in reports.get(p, {}).items() if m in policy['monitors']) if s is not None]
        quality = lower_median(scores) if len(scores) >= policy['min_reports'] else 0
        proven = before.get(p, {}).get('proven_quarters', 0) + (1 if paid_in >= MIN_PAYOUT[network] and quality >= 5000 else 0)
        declared = min(declared_seconds[p]) // YEAR if declared_seconds.get(p) else 0
        years = min(policy['max_retention_years'], declared, 1 + proven // 4)
        retention_bp = 5000 + 5000 * years // policy['max_retention_years']
        amount = paid_in * keep * quality * retention_bp // 10 ** 12
        owed = int(before.get(p, {}).get('accrued_base_units', 0)) + amount
        pay = owed // PAYOUT_UNIT[network] * PAYOUT_UNIT[network] if p in recipients and owed >= MIN_PAYOUT[network] else 0
        distributed += pay
        entries.append({'provider_id': p, 'settled_fees_base_units': str(paid_in), 'quality_bp': quality,
                        'report_ids': sorted((report_ids or {}).get(p, [])), 'retention_years': years,
                        'proven_quarters': proven, 'amount_base_units': str(amount), 'accrued_base_units': str(owed - pay),
                        'payout': (payouts or {}).get(p) if pay else None})
    received = sum(fees.values())
    seat = received * policy['monitor_share_bp'] // 10000 // len(policy['monitors'])
    complete = set(policy['monitors']) if complete_monitors is None else set(complete_monitors)
    if monitor_answers is not None:  # monitor -> (witnesses published by the cut-off, claims counted during its membership)
        complete = {m for m, (witnessed, total) in monitor_answers.items() if witnessed * 100 >= 95 * total}
    monitor_payments = [{'monitor_id': m, 'amount_base_units': str(seat if m in complete else 0), 'payout': None} for m in sorted(policy['monitors'])]
    s = {'foundation_id': did(key), 'network': network, 'period_start': start, 'period_end': end, 'policy_id': policy['policy_id'],
         'received_base_units': str(received), 'distributed_base_units': str(distributed), 'monitor_payments': monitor_payments, 'entries': entries}
    s['statement_id'] = content_id('fyds2', 'distribution-statement-id', s)
    s['foundation_signature'] = sign(key, 'distribution-statement', s)
    return s


def vault_status(key=FOUNDATION):
    v = {'foundation_id': did(key), 'period_start': '2027-01-01T00:00:00Z', 'period_end': '2027-04-01T00:00:00Z',
         'record_count': 6, 'stored_bytes': 81234,
         'funding': [{'network': 'bitcoin-mainnet', 'received_base_units': '6000', 'spent_base_units': '1000'}]}
    v['foundation_signature'] = sign(key, 'vault-status', v)
    return v


# ---- Key succession
def key_succession(old, new, effective_at):
    core = {'old_id': did(old), 'new_id': did(new), 'effective_at': effective_at}
    return dict(core, succession_id=content_id('fyks2', 'key-succession-id', core),
                old_signature=sign(old, 'key-succession', core), new_signature=sign(new, 'key-succession-accept', core))


def check_succession(s):
    core = {k: s[k] for k in ('old_id', 'new_id', 'effective_at')}
    if s['old_id'] == s['new_id'] or s['succession_id'] != content_id('fyks2', 'key-succession-id', core):
        raise ValueError('succession')
    verify(s['old_id'], 'key-succession', core, s['old_signature'])
    verify(s['new_id'], 'key-succession-accept', core, s['new_signature'])


# ---- Genesis manifest
def genesis_manifest(certificate, schedules, approvals, policy, signers=None):
    g = {'release': '1.0', 'release_key_ids': sorted(did(k) for k in RELEASE_KEYS), 'release_threshold': RELEASE_THRESHOLD,
         'foundation_key_certificates': [certificate], 'fee_schedules': schedules, 'fee_schedule_approvals': approvals,
         'distribution_policy': policy, 'signed_at': '2026-09-01T00:00:00Z'}
    g['release_signatures'] = release_sign('genesis-manifest', g, signers)
    return g


def check_genesis(g):
    ids = set(g['release_key_ids'])
    if not valid_key_set(ids, g['release_threshold']):
        raise ValueError('release key set')
    check_threshold('genesis-manifest', without(g, 'release_signatures'), g['release_signatures'], ids, g['release_threshold'])
    for c in g['foundation_key_certificates']:
        check_certificate(c, ids, g['release_threshold'], genesis=True)
    return ids


def build_world():
    """Everything the example and tests share: the synthetic chain, a five-monitor committee and three settled claims."""
    btc, eth = schedule_1('bitcoin-mainnet'), schedule_1('ethereum-mainnet')
    trust = Trust([key_certificate()])
    chain = Chain()
    monitors = [Monitor(k, trust, chain, [btc, eth]) for k in MONITORS]
    committee = sorted(did(k) for k in MONITORS)
    decl_a = retention_declaration(PROVIDER, 10 * YEAR, '2026-12-01T00:00:00Z', {'bitcoin-mainnet': RECIPIENTS['bitcoin-mainnet']})
    decl_b = retention_declaration(PROVIDER_B, YEAR, '2026-12-01T00:00:00Z', {'bitcoin-mainnet': RECIPIENTS['bitcoin-mainnet']})
    for m in monitors:
        m.register_declaration(decl_a)
        m.register_declaration(decl_b)
    chain.deposit(did(PROVIDER), 'bitcoin-mainnet', 10000)
    chain.deposit(did(PROVIDER_B), 'bitcoin-mainnet', 10000)
    receipts = [make_receipt(btc, t) for t in ['short post', 'x' * 900, 'y' * 3000, 'z' * 70000, 'another short post']]
    claim, leaves = make_claim(PROVIDER, 'bitcoin-mainnet', [leaf_of(r) for r in receipts],
                               '2027-01-05T00:00:00Z', '2027-01-06T00:00:00Z', decl_a['declaration_id'])
    witnesses, refusals = committee_audit(monitors, claim, leaves, '2027-01-06T12:00:00Z')
    assert len(witnesses) == 5 and not refusals
    receipts2 = [make_receipt(btc, 'second period', '2027-01-12T00:00:00Z')]
    claim2, leaves2 = make_claim(PROVIDER, 'bitcoin-mainnet', [leaf_of(r) for r in receipts2],
                                 '2027-01-12T00:00:00Z', '2027-01-13T00:00:00Z', decl_a['declaration_id'], previous=claim)
    witnesses2, refusals = committee_audit(monitors, claim2, leaves2, '2027-01-13T12:00:00Z')
    assert len(witnesses2) == 5 and not refusals
    receipts_b = [make_receipt(btc, 'q' * 5000, key=PROVIDER_B)]
    claim_b, leaves_b = make_claim(PROVIDER_B, 'bitcoin-mainnet', [leaf_of(r) for r in receipts_b],
                                   '2027-01-05T00:00:00Z', '2027-01-06T00:00:00Z', decl_b['declaration_id'])
    witnesses_b, refusals = committee_audit(monitors, claim_b, leaves_b, '2027-01-06T12:00:00Z')
    assert len(witnesses_b) == 5 and not refusals
    return dict(btc=btc, eth=eth, trust=trust, chain=chain, monitors=monitors, committee=committee, decl_a=decl_a, decl_b=decl_b,
                receipts=receipts, claim=claim, leaves=leaves, witnesses=witnesses,
                receipts2=receipts2, claim2=claim2, leaves2=leaves2, witnesses2=witnesses2,
                receipts_b=receipts_b, claim_b=claim_b, leaves_b=leaves_b, witnesses_b=witnesses_b)


def build_example():
    w = build_world()
    policy = distribution_policy()
    m = policy['monitors']
    good = {m[0]: [(0, 31, 9900), (31, 62, 9700)], m[1]: [(0, 90, 9800)], m[2]: [(10, 70, 9600)]}
    fair = {m[0]: [(0, 90, 9000)], m[1]: [(0, 90, 9500)], m[2]: [(0, 90, 8000)], m[3]: [(0, 30, 10000)]}
    statement = distribute(policy, 'bitcoin-mainnet', '2027-01-01T00:00:00Z', '2027-04-01T00:00:00Z',
                           [w['claim'], w['claim2'], w['claim_b']],
                           {did(PROVIDER): [10 * YEAR], did(PROVIDER_B): [YEAR]},
                           {did(PROVIDER): good, did(PROVIDER_B): fair},
                           recipients={did(PROVIDER), did(PROVIDER_B)})
    schedules = [w['btc'], w['eth']]
    approvals = [approve(w['btc']), approve(w['eth'])]
    certificate = w['trust'].certificates[0]
    first = w['receipts'][0]
    index = next(i for i, leaf in enumerate(w['leaves']) if leaf['receipt_hash'] == object_hash(first))
    proof = make_proof(w['claim'], w['leaves'], index, witnesses=w['witnesses'][:4])
    vault = Vault(w['committee'])
    vault_receipt = vault.put(first, proof, '2027-01-07T00:00:00Z')
    late = make_receipt(w['btc'], 'published too late', '2026-11-20T06:00:00Z')
    old_claim, old_leaves = make_claim(PROVIDER_NEXT, 'bitcoin-mainnet', [leaf_of(late)], '2026-11-20T00:00:00Z', '2026-11-21T00:00:00Z', w['decl_a']['declaration_id'])
    kind, refusal = w['monitors'][0].audit(old_claim, old_leaves, '2027-01-13T00:00:00Z')
    assert kind == 'refused'
    return {
        'status': 'SYNTHETIC ONLY: public test keys, imaginary deposits and recipients. The schedule amounts are fee schedule 1; every key, certificate, approval, witness and statement is a test fixture, and this manifest is not the genesis manifest of any network.',
        'genesis_manifest': genesis_manifest(certificate, schedules, approvals, policy),
        'settlement_deposit_commitment_hex': deposit_commitment(did(PROVIDER), 'bitcoin-mainnet'),
        'retention_declarations': [w['decl_a'], w['decl_b']],
        'receipt': first,
        'settlement_claim': w['claim'],
        'settlement_leaves': w['leaves'],
        'settlement_proof': proof,
        'second_claim': w['claim2'],
        'second_claim_witnesses': w['witnesses2'],
        'settlement_refusal_example': refusal,
        'foundation_log_head': log_head(vault.log, '2027-01-20T00:00:00Z'),
        'vault_receipt': vault_receipt,
        'distribution_statement': statement,
        'vault_status': vault_status(),
        'key_succession': key_succession(PROVIDER, PROVIDER_NEXT, '2027-06-01T00:00:00Z'),
    }


if __name__ == '__main__':
    if '--write' in sys.argv:
        EXAMPLE.write_text(json.dumps(build_example(), indent=2) + '\n', encoding='utf-8', newline='\n')
        print('wrote', EXAMPLE)
