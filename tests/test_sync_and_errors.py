"""Incremental sync page and public error body checks; a model, not a server."""
import json
import unittest

import jsonschema

from test_operations_profile import structural
from test_security_profile import M, PROVIDER, ROOT, SCHEMA, did

PAGE = jsonschema.Draft202012Validator(dict(SCHEMA, **{'$ref': '#/$defs/ChangesPage'}),
                                       format_checker=jsonschema.FormatChecker())


def page(items, next_after, more=False):
    return {'provider_id': did(PROVIDER), 'items': items, 'next_after': next_after, 'more': more}


def check_page(value, after):
    """Client-side checks for one GET /v1/changes response."""
    PAGE.validate(value)
    sequences = [item['sequence'] for item in value['items']]
    if sequences != sorted(set(sequences)) or any(s <= after for s in sequences):
        raise ValueError('sequence order')
    if value['next_after'] < after or (sequences and value['next_after'] < sequences[-1]):
        raise ValueError('next_after')
    if not value['more'] and not sequences and value['next_after'] != after:
        pass  # skipped (restricted or expired) sequences may advance next_after with no items
    return value['next_after']


class ChangesTests(unittest.TestCase):
    def test_page_shape_and_order(self):
        items = [{'sequence': 5, 'message': M}, {'sequence': 9, 'message': M}]
        self.assertEqual(check_page(page(items, 9), 4), 9)
        self.assertEqual(check_page(page([], 0), 0), 0)
        self.assertEqual(check_page(page([], 40, more=True), 12), 40)  # a gap is not proof of removal
        for bad_items, next_after, after in (
                ([{'sequence': 9, 'message': M}, {'sequence': 5, 'message': M}], 9, 4),  # out of order
                ([{'sequence': 5, 'message': M}, {'sequence': 5, 'message': M}], 5, 4),  # repeated
                ([{'sequence': 4, 'message': M}], 4, 4),  # not after the cursor
                ([{'sequence': 5, 'message': M}], 4, 4),  # next_after behind the last item
                ([], 3, 4)):  # cursor moved backwards
            with self.assertRaises(ValueError):
                check_page(page(bad_items, next_after), after)

    def test_page_is_closed_and_bounded(self):
        with self.assertRaises(jsonschema.ValidationError):
            PAGE.validate(dict(page([], 0), cursor='x'))
        with self.assertRaises(jsonschema.ValidationError):
            PAGE.validate(page([{'sequence': 0, 'message': M}], 0))
        with self.assertRaises(jsonschema.ValidationError):
            PAGE.validate(page([{'sequence': n + 1, 'message': M} for n in range(101)], 101))
        with self.assertRaises(jsonschema.ValidationError):
            PAGE.validate(page([{'sequence': 1, 'message': dict(M, message_type='archive_record')}], 1))


class ErrorBodyTests(unittest.TestCase):
    def test_catalog_error_names_match_the_schema(self):
        import re
        catalog = (ROOT / 'docs/API-catalog.md').read_text(encoding='utf-8')
        section = catalog.split('## Status and error interpretation')[1]
        named = set(re.findall(r'`([a-z_]+)`', section)) - {'retry_after_seconds', 'status'}
        ops = json.loads((ROOT / 'schemas/operations.schema.json').read_text(encoding='utf-8'))
        allowed = set(ops['$defs']['PublicReadError']['properties']['status']['enum'])
        self.assertTrue(named, 'no error names found')
        self.assertLessEqual(named, allowed)

    def test_error_body_shape(self):
        structural('PublicReadError', {'status': 'retention_expired'})
        structural('PublicReadError', {'status': 'rate_limited', 'retry_after_seconds': 30})
        for bad in ({'status': 'deleted'}, {'status': 'not_found', 'detail': 'x'}, {'status': 'rate_limited', 'retry_after_seconds': 0}):
            with self.assertRaises(jsonschema.ValidationError):
                structural('PublicReadError', bad)


if __name__ == '__main__':
    unittest.main()
