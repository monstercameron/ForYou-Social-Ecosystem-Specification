"""Reference authorization/recovery predicates, not a deployed service or legal certification.

Checkpoint authenticity, durable independent storage, transport, concurrent chunk
serialization and staff identity verification are implementation obligations.
These fixtures assume a checkpoint supplied through that independently trusted path.
"""
import copy
import hashlib
import json
import unittest


class Denied(ValueError):
    pass


def case_view(case, principal, requested_fields):
    if principal not in case['parties'] and principal not in case['assigned_reviewers']:
        raise Denied('case inaccessible')
    # Flattened field paths make nested fields independently grantable.
    return {name: copy.deepcopy(case['fields'][name]) for name in requested_fields
            if name in case['fields'] and principal in case['grants'].get(name, set())}


def export_chunk(job, principal, current_generation, disclose=True, hold=False,
                 public_available=True):
    # Preservation and public availability are deliberately separate from owner disclosure.
    if principal != job['owner'] or job['invalidated']:
        raise Denied('export inaccessible')
    if job['generation'] != current_generation or not disclose:
        job['invalidated'] = True
        raise Denied('fresh export required')
    return job['bytes']


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def checkpoint(events, operator='provider-a', generation=1):
    chain = digest({'operator': operator, 'generation': generation})
    for sequence, event in enumerate(events, 1):
        chain = digest({'previous': chain, 'sequence': sequence, 'event': event})
    return {'operator': operator, 'generation': generation, 'sequence': len(events), 'digest': chain}


def recover(events, trusted_checkpoint, operator='provider-a', generation=1):
    if trusted_checkpoint is None or checkpoint(events, operator, generation) != trusted_checkpoint:
        raise Denied('recovery unavailable')
    deleted, restricted, revoked = set(), set(), set()
    for action, scope, identifier in events:
        key = (scope, identifier)
        if action == 'delete':
            deleted.add(key)
        elif action == 'restrict':
            restricted.add(key)
        elif action == 'lift':
            restricted.discard(key)  # Does not resurrect deleted data or revoked authority.
        elif action == 'revoke':
            revoked.add(key)
        else:
            raise Denied('unknown control')
    return deleted, restricted, revoked


class ComplianceControlsTests(unittest.TestCase):
    def setUp(self):
        self.case = {
            'parties': {'reporter', 'publisher'}, 'assigned_reviewers': {'reviewer'},
            'fields': {'submission.text': 'claim', 'reporter.contact': 'private',
                       'publisher.identity_document': 'private identity evidence',
                       'decision.reason_for_publisher': 'authorized reason',
                       'security.note': 'restricted investigation'},
            'grants': {'submission.text': {'reporter', 'reviewer'},
                       'reporter.contact': {'reporter', 'reviewer'},
                       'publisher.identity_document': {'publisher'},
                       'decision.reason_for_publisher': {'publisher', 'reviewer'}}}

    def test_parties_cannot_enumerate_each_others_confidential_fields(self):
        requested = list(self.case['fields']) + ['new_private_field']
        publisher = case_view(self.case, 'publisher', requested)
        reporter = case_view(self.case, 'reporter', requested)
        self.assertNotIn('reporter.contact', publisher)
        self.assertNotIn('submission.text', publisher)
        self.assertNotIn('publisher.identity_document', reporter)
        self.assertEqual(publisher['decision.reason_for_publisher'], 'authorized reason')
        self.assertNotIn('security.note', case_view(self.case, 'reviewer', requested))
        with self.assertRaises(Denied):
            case_view(self.case, 'unassigned-staff', requested)

    def test_revoking_a_field_grant_applies_to_repeat_download(self):
        self.assertIn('reporter.contact', case_view(self.case, 'reviewer', ['reporter.contact']))
        self.case['grants']['reporter.contact'].remove('reviewer')
        self.assertEqual(case_view(self.case, 'reviewer', ['reporter.contact']), {})

    def test_hold_and_public_restriction_do_not_implicitly_deny_owner_export(self):
        job = {'owner': 'alice', 'generation': 7, 'invalidated': False, 'bytes': b'owner data'}
        self.assertEqual(export_chunk(job, 'alice', 7, hold=True, public_available=False), b'owner data')
        with self.assertRaises(Denied):
            export_chunk(job, 'bob', 7)

    def test_restriction_between_chunks_invalidates_resume_and_lift_does_not_revive_it(self):
        job = {'owner': 'alice', 'generation': 7, 'invalidated': False, 'bytes': b'owner data'}
        export_chunk(job, 'alice', 7)
        with self.assertRaises(Denied):
            export_chunk(job, 'alice', 8, disclose=False)
        with self.assertRaises(Denied):
            export_chunk(job, 'alice', 9, disclose=True)
        replacement = dict(job, generation=9, invalidated=False)
        self.assertEqual(export_chunk(replacement, 'alice', 9), b'owner data')

    def test_old_backup_cannot_reopen_after_acknowledged_delete_and_revocation(self):
        events = [('delete', 'alice', 'post-1'), ('revoke', 'alice', 'delegate-1')]
        trusted = checkpoint(events)
        with self.assertRaises(Denied):
            recover(events[:1], trusted)
        deleted, _, revoked = recover(events, trusted)
        self.assertIn(('alice', 'post-1'), deleted)
        self.assertIn(('alice', 'delegate-1'), revoked)
        self.assertNotIn(('bob', 'post-1'), deleted)

    def test_lost_conflicting_reordered_or_wrong_operator_checkpoint_blocks_recovery(self):
        events = [('restrict', 'alice', 'post-1'), ('lift', 'alice', 'post-1')]
        trusted = checkpoint(events)
        for bad_events, bad_checkpoint, operator, generation in [
                (events, None, 'provider-a', 1),
                (list(reversed(events)), trusted, 'provider-a', 1),
                (events, trusted, 'provider-b', 1),
                (events, trusted, 'provider-a', 2),
                (events + [('delete', 'alice', 'post-2')], trusted, 'provider-a', 1)]:
            with self.subTest(events=bad_events, operator=operator, generation=generation):
                with self.assertRaises(Denied):
                    recover(bad_events, bad_checkpoint, operator, generation)

    def test_restriction_lift_cannot_erase_deletion_or_delegate_revocation(self):
        events = [('delete', 'alice', 'post-1'), ('restrict', 'alice', 'post-1'),
                  ('revoke', 'alice', 'delegate-1'), ('lift', 'alice', 'post-1'),
                  ('lift', 'alice', 'delegate-1')]
        deleted, restricted, revoked = recover(events, checkpoint(events))
        self.assertFalse(restricted)
        self.assertIn(('alice', 'post-1'), deleted)
        self.assertIn(('alice', 'delegate-1'), revoked)


if __name__ == '__main__':
    unittest.main()
