"""Optional display names profile: example records, name rules and document agreement.

A reference check of the profile's predicates, not a holder or client implementation.
Run `python tests/test_display_names.py --write` to regenerate the example.
"""
import copy
import hashlib
import json
import re
import sys
import unicodedata
import unittest

import jsonschema

from test_security_profile import ROOT, AUTHOR, PROVIDER, did, pre, sign, verify

EXAMPLE = ROOT / 'examples/name-record.example.json'
OPS = json.loads((ROOT / 'schemas/operations.schema.json').read_text(encoding='utf-8'))
DOC = (ROOT / 'docs/12-display-names-profile.md').read_text(encoding='utf-8')
CATALOG = (ROOT / 'docs/API-catalog.md').read_text(encoding='utf-8')
PREFIX = 'fynr2:'
WHITE_SPACE = set('\t\n\v\f\r \x85\xa0     　') | {chr(c) for c in range(0x2000, 0x200b)}
EXCLUDED_CATEGORIES = {'Cc', 'Cf', 'Cn', 'Co', 'Cs', 'Zl', 'Zp'}


def validator(kind):
    return jsonschema.Draft202012Validator(dict(OPS, **{'$ref': '#/$defs/' + kind}),
                                           format_checker=jsonschema.FormatChecker())


def name_id(record):
    body = {k: v for k, v in record.items() if k not in ('name_id', 'author_signature')}
    return PREFIX + hashlib.sha256(pre('name-record-id', body)).hexdigest()


def build_record(key, display_name, issued_at, previous_name_id):
    record = {'author_id': did(key), 'display_name': display_name, 'issued_at': issued_at,
              'previous_name_id': previous_name_id}
    record['name_id'] = name_id(record)
    record['author_signature'] = sign(key, 'name-record', record)
    return {k: record[k] for k in ('name_id', 'author_id', 'display_name', 'issued_at', 'previous_name_id', 'author_signature')}


def build_example():
    first = build_record(AUTHOR, 'Zoë Example', '2026-11-11T00:00:00Z', None)
    withdrawal = build_record(AUTHOR, None, '2026-11-12T00:00:00Z', first['name_id'])
    return {
        'status': 'SYNTHETIC ONLY: public test key. A signed name proves only which key signed it; it is not unique and not an identity claim.',
        'description': 'A display name record of the optional display names profile and a later withdrawal record that replaces it.',
        'record': first,
        'withdrawal': withdrawal,
    }


def check_name(value):
    """The name rules of the profile; raises ValueError. Character data is the running Python's Unicode database."""
    if value is None:
        return
    if not isinstance(value, str) or not 1 <= len(value) <= 64 or len(value.encode('utf-8')) > 256:
        raise ValueError('length')
    if unicodedata.normalize('NFC', value) != value:
        raise ValueError('not NFC')
    if any(unicodedata.category(c) in EXCLUDED_CATEGORIES for c in value):
        raise ValueError('excluded character')
    if value[0] in WHITE_SPACE or value[-1] in WHITE_SPACE or '  ' in value:
        raise ValueError('white space')


def check_record(record, now='2026-11-12T00:00:00Z'):
    """Profile verification steps 1-5; raises on failure."""
    validator('NameRecord').validate(record)
    check_name(record['display_name'])
    if record['name_id'] != name_id(record):
        raise ValueError('name_id')
    verify(record['author_id'], 'name-record', {k: v for k, v in record.items() if k != 'author_signature'},
           record['author_signature'])
    if seconds(record['issued_at']) > seconds(now) + 60:
        raise ValueError('issued_at in the future')


def seconds(text):
    from datetime import datetime, timezone
    return int(datetime.strptime(text, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp())


def current(records):
    """Greatest issued_at wins; a tie goes to the ASCII-smallest name_id. Invalid records are ignored."""
    valid = []
    for r in records:
        try:
            check_record(r, now='2030-01-01T00:00:00Z')
        except Exception:
            continue
        valid.append(r)
    if not valid:
        return None
    best = max(seconds(r['issued_at']) for r in valid)
    return min((r for r in valid if seconds(r['issued_at']) == best), key=lambda r: r['name_id'].encode('ascii'))


class ExampleTests(unittest.TestCase):
    def setUp(self):
        self.example = json.loads(EXAMPLE.read_text(encoding='utf-8'))

    def test_example_is_reproducible(self):
        self.assertEqual(self.example, build_example())

    def test_example_validates_and_verifies(self):
        for name in ('record', 'withdrawal'):
            with self.subTest(record=name):
                check_record(self.example[name])
        record, withdrawal = self.example['record'], self.example['withdrawal']
        self.assertIsNone(record['previous_name_id'])
        self.assertEqual(withdrawal['previous_name_id'], record['name_id'])
        self.assertIsNone(withdrawal['display_name'])
        self.assertEqual(current([record, withdrawal]), withdrawal)
        validator('NamesPage').validate({'names': [record], 'next_cursor': None})
        validator('NamesPage').validate({'names': [], 'next_cursor': 'A' * 43})

    def test_tampering_is_rejected(self):
        record = self.example['record']
        for field, value in (('display_name', 'Zoe Example'), ('issued_at', '2026-11-11T00:00:01Z'),
                             ('author_id', did(PROVIDER)), ('previous_name_id', PREFIX + 'a' * 64)):
            with self.subTest(field=field), self.assertRaises(Exception):
                check_record(dict(record, **{field: value}))
        resigned = dict(record, display_name='Other')
        resigned['author_signature'] = sign(AUTHOR, 'name-record', {k: v for k, v in resigned.items() if k != 'author_signature'})
        with self.assertRaises(ValueError):
            check_record(resigned)  # the name_id no longer matches
        # A signature under another label, or by another key, does not verify.
        body = {k: v for k, v in record.items() if k != 'author_signature'}
        for forged in (sign(AUTHOR, 'message', body), sign(PROVIDER, 'name-record', body)):
            with self.assertRaises(Exception):
                check_record(dict(record, author_signature=forged))

    def test_future_issued_at_is_rejected(self):
        early = build_record(AUTHOR, 'Ada', '2026-11-12T00:01:00Z', None)
        check_record(early, now='2026-11-12T00:00:00Z')
        late = build_record(AUTHOR, 'Ada', '2026-11-12T00:01:01Z', None)
        with self.assertRaises(ValueError):
            check_record(late, now='2026-11-12T00:00:00Z')

    def test_schema_is_closed_and_bounded(self):
        record = self.example['record']
        v = validator('NameRecord')
        for bad in (dict(record, extra=1), {k: x for k, x in record.items() if k != 'previous_name_id'},
                    dict(record, name_id='fynr1:' + 'a' * 64), dict(record, display_name=''),
                    dict(record, display_name='a' * 65), dict(record, display_name=' Ada'),
                    dict(record, display_name='Ada\u0007'), dict(record, display_name='Ada  B')):
            self.assertFalse(v.is_valid(bad), bad)
        page = validator('NamesPage')
        self.assertFalse(page.is_valid({'names': [record] * 51, 'next_cursor': None}))
        self.assertFalse(page.is_valid({'names': [], 'next_cursor': None, 'generated_at': '2026-11-11T00:00:00Z'}))
        self.assertFalse(page.is_valid({'names': []}))


class NameRuleTests(unittest.TestCase):
    def test_accepted_names(self):
        for value in ('Ada', 'Zoë', 'Ana María', '李小龙', 'مريم', 'a' * 64,
                      '\U0001f600' * 64, 'Ada Lovelace (test)', None):
            with self.subTest(value=value):
                check_name(value)

    def test_rejected_names(self):
        cases = {
            'control character': 'Ada\u0007',
            'line feed': 'Ada\nB',
            'bidi override': 'Ada‮B',
            'bidi isolate': '⁧Ada',
            'zero-width joiner': 'A‍B',
            'line separator': 'Ada B',
            'private use': 'Ada',
            'unassigned': 'Ada͸',
            'too long': 'a' * 65,
            'empty': '',
            'leading space': ' Ada',
            'trailing space': 'Ada ',
            'leading ideographic space': '　Ada',
            'two spaces': 'Ada  B',
            'not NFC': 'Zoë',
        }
        for reason, value in cases.items():
            with self.subTest(reason=reason), self.assertRaises(ValueError):
                check_name(value)

    def test_nfc_form_is_checked_not_repaired(self):
        decomposed = 'Zoë'
        self.assertEqual(unicodedata.normalize('NFC', decomposed), 'Zoë')
        with self.assertRaises(ValueError):
            check_name(decomposed)
        check_name(unicodedata.normalize('NFC', decomposed))

    def test_byte_limit(self):
        # 64 four-byte scalar values reach the 256-byte limit exactly.
        self.assertEqual(len(('\U0001f600' * 64).encode('utf-8')), 256)
        with self.assertRaises(ValueError):
            check_name('\U0001f600' * 65)


class CurrentRecordTests(unittest.TestCase):
    def test_greater_issued_at_wins(self):
        a = build_record(AUTHOR, 'First', '2026-11-11T00:00:00Z', None)
        b = build_record(AUTHOR, 'Second', '2026-11-13T00:00:00Z', a['name_id'])
        c = build_record(AUTHOR, 'Backdated', '2026-11-10T00:00:00Z', b['name_id'])
        for order in ([a, b, c], [c, b, a], [b, a, c]):
            self.assertEqual(current(order), b)

    def test_tie_goes_to_the_smaller_name_id(self):
        at = '2026-11-11T00:00:00Z'
        records = [build_record(AUTHOR, name, at, None) for name in ('Alpha', 'Beta', 'Gamma')]
        smallest = min(records, key=lambda r: r['name_id'])
        self.assertEqual(current(records), smallest)
        self.assertEqual(current(list(reversed(records))), smallest)

    def test_invalid_records_are_never_selected(self):
        a = build_record(AUTHOR, 'Valid', '2026-11-11T00:00:00Z', None)
        forged = dict(build_record(AUTHOR, 'Forged', '2026-11-20T00:00:00Z', None), display_name='Changed')
        self.assertEqual(current([a, forged]), a)
        self.assertIsNone(current([forged]))


class DocumentAgreementTests(unittest.TestCase):
    def section(self, text, heading):
        return text.split(heading, 1)[1].split('\n## ', 1)[0]

    def test_record_fields_agree(self):
        schema = set(OPS['$defs']['NameRecord']['properties'])
        listed = re.search(r'`NameRecord` is `\{([a-z_,]+)\}`', DOC).group(1).split(',')
        self.assertEqual(set(listed), schema)
        table = set(re.findall(r'^\| `([a-z_]+)` \|', self.section(DOC, '## Name records'), flags=re.M))
        self.assertEqual(table, schema)
        self.assertEqual(set(OPS['$defs']['NameRecord']['required']), schema)
        page = re.search(r'`NamesPage` `\{([a-z_,]+)\}`', DOC).group(1).split(',')
        self.assertEqual(set(page), set(OPS['$defs']['NamesPage']['properties']))
        self.assertIn('at most 50 records', DOC)
        self.assertEqual(OPS['$defs']['NamesPage']['properties']['names']['maxItems'], 50)

    def test_routes_agree(self):
        route = r'`((?:GET|POST|PUT) /v1/names[^`]*)`'
        catalog = set(re.findall(route, self.section(CATALOG, '## Optional display names')))
        document = set(re.findall(route, self.section(DOC, '## Routes')))
        self.assertEqual(catalog, {'POST /v1/names', 'GET /v1/names/{author_id}', 'GET /v1/names?display_name={name}'})
        self.assertEqual(document, catalog)
        self.assertEqual(set(re.findall(route, CATALOG)), catalog)

    def test_statuses_exist(self):
        allowed = set(OPS['$defs']['PublicReadError']['properties']['status']['enum'])
        used = set(re.findall(r'\b\d{3} `([a-z_]+)`', self.section(DOC, '## Routes') + self.section(CATALOG, '## Optional display names')))
        self.assertTrue({'invalid_message', 'stale_state', 'not_ready', 'rate_limited', 'not_found'} <= used)
        self.assertLessEqual(used, allowed)

    def test_prefix_and_labels_agree(self):
        self.assertIn('`%s`' % PREFIX, DOC)
        self.assertIn('`%s`' % PREFIX, (ROOT / 'docs/02-protocol.md').read_text(encoding='utf-8'))
        self.assertIn('`%s`' % PREFIX, (ROOT / 'docs/06-governance.md').read_text(encoding='utf-8'))
        for kind in ('name_id', 'previous_name_id'):
            self.assertTrue(OPS['$defs']['NameRecord']['properties'][kind]['pattern'].startswith('^' + PREFIX))
        for label in ('P("name-record-id"', 'P("name-record"'):
            self.assertIn(label, DOC)

    def test_profile_is_indexed_as_optional(self):
        index = (ROOT / 'docs/README.md').read_text(encoding='utf-8')
        self.assertIn('[display names profile](./12-display-names-profile.md)', index.split('| Optional profile |')[1].split('\n')[0])
        self.assertIn('A provider, replica or client is conformant to core 1.0 without it.', DOC)
        # The core statement that follows and profiles are not protocol state stays, next to the pointer.
        for name, statement in (('README.md', 'are not core protocol state.'),
                                ('docs/01-overview.md', 'are application features outside this core specification.'),
                                ('docs/07-clients.md', 'MUST NOT present them as network state.')):
            line = next(l for l in (ROOT / name).read_text(encoding='utf-8').splitlines() if statement in l)
            self.assertIn('12-display-names-profile.md', line, name)


if __name__ == '__main__':
    if '--write' in sys.argv:
        EXAMPLE.write_text(json.dumps(build_example(), indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    else:
        unittest.main()
