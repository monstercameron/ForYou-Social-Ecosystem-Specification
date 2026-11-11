"""Synthetic quality evidence checks, not a network monitor or proof of honesty."""
import copy
import hashlib
import unittest
from datetime import datetime, timedelta

import rfc8785
from test_operations_profile import structural
from test_security_profile import AUTHOR, PROVIDER, b64, did, pre, sign, verify


def digest(data):
    return hashlib.sha256(data).hexdigest()


def seal(report):
    result = {k: v for k, v in report.items() if k not in ('report_id', 'monitor_signature')}
    result['report_id'] = 'fyqr2:' + digest(pre('quality-report-id', result))
    result['monitor_signature'] = sign(AUTHOR, 'quality-report', result)
    return result


def fixture():
    start, end = '2026-11-01T00:00:00Z', '2026-11-02T00:00:00Z'
    observations = []
    for kind in ('availability', 'retrieval'):
        for i in range(20):
            observations.append({'kind': kind, 'message_id': 'fy1:' + 'a' * 64 if kind == 'retrieval' else None,
                                 'started_at': start, 'duration_ms': i + 1, 'outcome': 'pass' if i < 18 else 'unavailable',
                                 'http_status': 200 if i < 18 else 503, 'within_limits': True})
    raw = {'provider_id': did(PROVIDER), 'monitor_id': did(AUTHOR), 'period_start': start,
           'period_end': end, 'observations': observations}
    seed = b64(bytes(range(32)))
    report = {'monitor_id': did(AUTHOR), 'provider_id': did(PROVIDER), 'period_start': start,
              'period_end': end, 'created_at': end, 'methodology_digest': digest(b'synthetic methodology'),
              'observations_digest': digest(rfc8785.dumps(raw)), 'sample_frame_digest': digest(b'synthetic sample frame'), 'sample_seed': seed,
              'sample_seed_commitment': digest(pre('quality-sample-seed', {'sample_seed': seed})),
              'sample_coverage': 'complete', 'availability_attempts': 20, 'availability_successes': 18,
              'retrieval_attempts': 20, 'retrieval_passes': 18, 'restore_attempts': 0, 'restore_passes': 0,
              'latency_p50_ms': 9, 'latency_p95_ms': 18, 'latency_p99_ms': 18,
              'replica_operators': 1, 'independent_controllers': 1, 'sponsors': [], 'conflicts': ''}
    return seal(report), raw


def validate(report, raw):
    """Partial test model: it cannot establish sampling completeness or truth."""
    structural('QualityReport', report)
    structural('QualityObservationSet', raw)
    without_sig = {k: v for k, v in report.items() if k != 'monitor_signature'}
    verify(report['monitor_id'], 'quality-report', without_sig, report['monitor_signature'])
    body = {k: v for k, v in report.items() if k not in ('report_id', 'monitor_signature')}
    if report['report_id'] != 'fyqr2:' + digest(pre('quality-report-id', body)):
        raise ValueError('report id')
    if report['sample_seed_commitment'] != digest(pre('quality-sample-seed', {'sample_seed': report['sample_seed']})):
        raise ValueError('seed commitment')
    if report['observations_digest'] != digest(rfc8785.dumps(raw)):
        raise ValueError('observations digest')
    if any(report[k] != raw[k] for k in ('provider_id', 'monitor_id', 'period_start', 'period_end')):
        raise ValueError('evidence binding')
    parse = lambda t: datetime.fromisoformat(t.replace('Z', '+00:00'))
    start, end, created = map(parse, (report['period_start'], report['period_end'], report['created_at']))
    if not (start < end <= created and end - start <= timedelta(days=31)):
        raise ValueError('period')
    operators, controllers = report['replica_operators'], report['independent_controllers']
    if (operators is None) != (controllers is None) or (operators is not None and controllers > operators):
        raise ValueError('controllers')
    for obs in raw['observations']:
        if not start <= parse(obs['started_at']) < end:
            raise ValueError('observation time')
        status, outcome, kind = obs['http_status'], obs['outcome'], obs['kind']
        if kind != 'restore':
            if outcome == 'pass' and status != 200:
                raise ValueError('HTTP pass')
            if status == 429 and outcome != 'rate_limited':
                raise ValueError('HTTP 429')
            if status == 503 and outcome != 'unavailable':
                raise ValueError('HTTP 503')
            if status is None and outcome != 'unavailable':
                raise ValueError('timeout')
        if kind == 'retrieval' and outcome == 'pass' and obs['message_id'] is None:
            raise ValueError('unverifiable retrieval')
    for kind, attempts, passes in (('availability', 'availability_attempts', 'availability_successes'),
                                   ('retrieval', 'retrieval_attempts', 'retrieval_passes'),
                                   ('restore', 'restore_attempts', 'restore_passes')):
        eligible = [o for o in raw['observations'] if o['kind'] == kind and o['within_limits']
                    and o['outcome'] in ('pass', 'fail', 'rate_limited', 'unavailable')]
        if report[attempts] != len(eligible) or report[passes] != sum(o['outcome'] == 'pass' for o in eligible):
            raise ValueError('counts')
    durations = sorted(o['duration_ms'] for o in raw['observations'] if o['kind'] == 'availability'
                       and o['within_limits'] and o['outcome'] == 'pass')
    expected = [durations[(p * len(durations) + 99) // 100 - 1] if durations else None for p in (50, 95, 99)]
    if [report['latency_p50_ms'], report['latency_p95_ms'], report['latency_p99_ms']] != expected:
        raise ValueError('latency')


def score(report):
    a, r = report['availability_attempts'], report['retrieval_attempts']
    if report['sample_coverage'] != 'complete' or min(a, r) < 20:
        return None
    return ((10000 * report['availability_successes'] // a) + (10000 * report['retrieval_passes'] // r)) // 2


class QualityTests(unittest.TestCase):
    def test_signed_report_and_identity(self):
        report, raw = fixture()
        validate(report, raw)
        with self.assertRaises(Exception):
            verify(report['provider_id'], 'quality-report', {k: v for k, v in report.items() if k != 'monitor_signature'}, report['monitor_signature'])
        altered = dict(report, availability_successes=19)
        with self.assertRaises(Exception):
            validate(altered, raw)

    def test_signed_but_inconsistent_evidence(self):
        report, raw = fixture()
        for changes in ({'availability_successes': 21}, {'latency_p95_ms': 17},
                        {'independent_controllers': 2}, {'period_end': '2026-12-31T00:00:00Z'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate(seal(dict(report, **changes)), raw)
        omitted = copy.deepcopy(raw)
        omitted['observations'].pop()
        with self.assertRaises(ValueError):
            validate(report, omitted)
        with self.assertRaises(ValueError):
            validate(seal(dict(report, observations_digest=digest(rfc8785.dumps(omitted)))), omitted)

    def test_interval_and_evidence_binding(self):
        report, raw = fixture()
        for timestamp in ('2026-10-31T23:59:59Z', '2026-11-02T00:00:00Z'):
            altered = copy.deepcopy(raw)
            altered['observations'][0]['started_at'] = timestamp
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                validate(seal(dict(report, observations_digest=digest(rfc8785.dumps(altered)))), altered)
        with self.assertRaises(ValueError):
            validate(seal(dict(report, created_at='2026-11-01T00:00:00Z')), raw)

    def test_reference_score_coverage_and_no_volume_reward(self):
        report, _ = fixture()
        self.assertEqual(score(report), 9000)
        self.assertEqual(score(report), score(report))
        scaled = dict(report, availability_attempts=40, availability_successes=36,
                      retrieval_attempts=40, retrieval_passes=36)
        self.assertEqual(score(scaled), score(report))
        for coverage in ('incomplete', 'unknown'):
            self.assertIsNone(score(dict(report, sample_coverage=coverage)))
        self.assertIsNone(score(dict(report, retrieval_attempts=19)))
        self.assertTrue(0 <= score(report) <= 10000)
        # Complete is a signed assertion about the plan, not independently proven coverage.
        self.assertEqual(report['sample_coverage'], 'complete')

    def test_incoherent_http_results_and_unknown_replication(self):
        report, raw = fixture()
        for status, outcome in ((500, 'pass'), (204, 'pass'), (429, 'pass'), (429, 'fail'),
                                (503, 'pass'), (None, 'pass')):
            modified = copy.deepcopy(raw)
            modified['observations'][0].update(http_status=status, outcome=outcome)
            signed = seal(dict(report, observations_digest=digest(rfc8785.dumps(modified))))
            with self.subTest(status=status, outcome=outcome), self.assertRaises(ValueError):
                validate(signed, modified)
        unknown = seal(dict(report, replica_operators=None, independent_controllers=None))
        validate(unknown, raw)
        zero = seal(dict(report, replica_operators=0, independent_controllers=0))
        validate(zero, raw)
        self.assertNotEqual(unknown['report_id'], zero['report_id'])
        with self.assertRaises(ValueError):
            validate(seal(dict(report, replica_operators=None, independent_controllers=0)), raw)


if __name__ == '__main__':
    unittest.main()
