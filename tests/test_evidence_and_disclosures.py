"""Monitor evidence about the Foundation, quality evidence routes and monitor disclosures; a model, not a server."""
import unittest

import jsonschema

import economics_model as em
from test_operations_profile import structural
from test_security_profile import PROVIDER, ROOT, did

NOW = '2027-02-01T00:00:00Z'
CATALOG = (ROOT / 'docs/API-catalog.md').read_text(encoding='utf-8')


class StubLog:
    """A log of a given length whose root depends only on its length."""
    def __init__(self, length, fill):
        self.entries = [None] * length
        self.fill = fill

    def root(self, size):
        return self.fill * 32


def evidence(kind, heads=(), closure=None, transfer=None, monitor=None):
    monitor = em.MONITORS[0] if monitor is None else monitor
    e = {'monitor_id': did(monitor), 'kind': kind, 'heads': list(heads), 'closure': closure, 'transfer': transfer, 'observed_at': NOW}
    e['monitor_signature'] = em.sign(monitor, 'foundation-evidence', e)
    return e


def check_evidence(e):
    """What a reader checks before it relies on one evidence object."""
    structural('FoundationEvidence', e)
    em.verify(e['monitor_id'], 'foundation-evidence', em.without(e, 'monitor_signature'), e['monitor_signature'])
    used = {'log_rewrite': (2, False, False), 'head_after_closure': (1, True, False), 'recipient_funded_deposit': (0, False, True)}[e['kind']]
    if (len(e['heads']), e['closure'] is not None, e['transfer'] is not None) != used:
        raise ValueError('members do not match the kind')
    for head in e['heads']:
        em.verify(head['foundation_id'], 'foundation-log-head', em.without(head, 'foundation_signature'), head['foundation_signature'])
    if e['kind'] == 'log_rewrite' and (e['heads'][0]['foundation_id'] != e['heads'][1]['foundation_id'] or e['heads'][0]['root'] == e['heads'][1]['root']):
        raise ValueError('heads do not conflict')
    if e['kind'] == 'head_after_closure' and e['heads'][0]['size'] <= e['closure']['head']['size']:
        raise ValueError('head is not past the closure')


class FoundationEvidenceTests(unittest.TestCase):
    def test_log_rewrite_carries_two_conflicting_heads(self):
        a = em.log_head(StubLog(4, 'aa'), '2027-01-20T00:00:00Z')
        b = em.log_head(StubLog(4, 'bb'), '2027-01-21T00:00:00Z')
        check_evidence(evidence('log_rewrite', heads=[a, b]))

    def test_two_equal_heads_are_not_a_rewrite(self):
        a = em.log_head(StubLog(4, 'aa'), '2027-01-20T00:00:00Z')
        with self.assertRaises(ValueError):
            check_evidence(evidence('log_rewrite', heads=[a, a]))

    def test_head_after_closure_carries_the_head_and_the_closure(self):
        closure = em.key_closure(em.FOUNDATION, NOW, StubLog(4, 'aa'))
        later = em.log_head(StubLog(9, 'cc'), '2027-01-25T00:00:00Z')
        check_evidence(evidence('head_after_closure', heads=[later], closure=closure))

    def test_a_head_inside_the_closed_log_is_not_evidence(self):
        closure = em.key_closure(em.FOUNDATION, NOW, StubLog(4, 'aa'))
        earlier = em.log_head(StubLog(3, 'cc'), '2027-01-25T00:00:00Z')
        with self.assertRaises(ValueError):
            check_evidence(evidence('head_after_closure', heads=[earlier], closure=closure))

    def test_recipient_funded_deposit_names_the_transfer(self):
        transfer = {'network': 'bitcoin-mainnet', 'transaction': 'ab' * 32 + ':0', 'recipient': 'bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4'}
        check_evidence(evidence('recipient_funded_deposit', transfer=transfer))

    def test_members_a_kind_does_not_use_stay_empty(self):
        a = em.log_head(StubLog(4, 'aa'), '2027-01-20T00:00:00Z')
        transfer = {'network': 'ethereum-mainnet', 'transaction': '0x' + 'ab' * 32, 'recipient': '0x' + '12' * 20}
        with self.assertRaises(ValueError):
            check_evidence(evidence('recipient_funded_deposit', heads=[a], transfer=transfer))

    def test_a_changed_report_fails_its_signature(self):
        transfer = {'network': 'bitcoin-mainnet', 'transaction': 'ab' * 32 + ':0', 'recipient': 'bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4'}
        e = dict(evidence('recipient_funded_deposit', transfer=transfer), observed_at='2027-02-02T00:00:00Z')
        with self.assertRaises(ValueError):
            check_evidence(e)

    def test_closed_shape(self):
        a = em.log_head(StubLog(4, 'aa'), '2027-01-20T00:00:00Z')
        good = evidence('log_rewrite', heads=[a, em.log_head(StubLog(4, 'bb'), '2027-01-21T00:00:00Z')])
        structural('FoundationEvidencePage', {'evidence': [good]})
        for bad in (dict(good, kind='suspicion'), dict(good, heads=[a, a, a]), dict(good, note='x'), {k: v for k, v in good.items() if k != 'transfer'}):
            with self.assertRaises(jsonschema.ValidationError):
                structural('FoundationEvidence', bad)


class MonitorDisclosureTests(unittest.TestCase):
    def disclosure(self, **changes):
        d = {'policy_id': 'fydp2:' + 'ab' * 32, 'monitor_id': did(em.MONITORS[0]), 'selection_criteria': 'Operated by an organization with no shared ownership with any provider.', 'relationships': []}
        d.update(changes)
        return d

    def test_no_relationship_is_an_empty_list(self):
        structural('MonitorDisclosure', self.disclosure())

    def test_relationships_name_the_foundation_or_a_provider_key(self):
        structural('MonitorDisclosure', self.disclosure(relationships=[
            {'party': 'foundation', 'kind': 'funding', 'description': 'The Foundation pays this monitor from the monitor share.'},
            {'party': did(PROVIDER), 'kind': 'ownership', 'description': 'Same parent company.'}]))

    def test_closed_shape(self):
        for bad in (self.disclosure(selection_criteria=''), self.disclosure(selection_criteria='x' * 4097),
                    self.disclosure(relationships=[{'party': 'a friend', 'kind': 'funding', 'description': 'x'}]),
                    self.disclosure(relationships=[{'party': 'foundation', 'kind': 'friendship', 'description': 'x'}]),
                    self.disclosure(relationships=[{'party': 'foundation', 'kind': 'funding', 'description': 'x' * 1025}]),
                    self.disclosure(signature='x')):
            with self.assertRaises(jsonschema.ValidationError):
                structural('MonitorDisclosure', bad)

    def test_the_distribution_page_always_carries_disclosures(self):
        structural('DistributionPage', {'policies': [], 'statements': [], 'disclosures': [self.disclosure()]})
        with self.assertRaises(jsonschema.ValidationError):
            structural('DistributionPage', {'policies': [], 'statements': []})


class CatalogTests(unittest.TestCase):
    def test_monitor_evidence_routes_are_listed(self):
        for route in ('`GET /v1/quality-reports/{report_id}/methodology`', '`GET /v1/quality-reports/{report_id}/observations`', '`GET /v1/foundation-evidence`'):
            self.assertIn(route, CATALOG)


if __name__ == '__main__':
    unittest.main()
