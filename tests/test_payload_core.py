"""Core post payload boundaries: presentation fields are not protocol state."""
import hashlib
import json
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'schemas/launch.schema.json').read_text(encoding='utf-8'))
VALIDATOR = jsonschema.Draft202012Validator(dict(SCHEMA, **{'$ref': '#/$defs/PostPayload'}))


def slot(index=0, kind='image'):
    return {
        'id': f'media_{index}',
        'url': f'https://media.example/{index}',
        'kind': kind,
        'sha256': hashlib.sha256(f'local synthetic {index}'.encode()).hexdigest(),
    }


def payload(**fields):
    result = {'content_format': 'text/plain', 'text': 'Example text'}
    result.update(fields)
    return result


class CorePayloadTests(unittest.TestCase):
    def valid(self, value):
        self.assertEqual(list(VALIDATOR.iter_errors(value)), [])

    def invalid(self, value):
        self.assertTrue(list(VALIDATOR.iter_errors(value)))

    def test_presentation_fields_are_rejected(self):
        self.valid(payload())
        for field, value in (('layout', 'note'), ('layout', 'article'),
                             ('title', 'A title'), ('lang', 'en'),
                             ('unknown_style', True)):
            with self.subTest(field=field):
                self.invalid(payload(**{field: value}))

    def test_schema_defines_no_presentation_fields(self):
        properties = SCHEMA['$defs']['PostPayload']['properties']
        for field in ('layout', 'title', 'lang'):
            self.assertNotIn(field, properties)

    def test_empty_text_needs_a_slot(self):
        self.invalid(payload(text=''))
        self.invalid(payload(text='', media_slots=[]))
        self.valid(payload(text='', media_slots=[slot()]))
        self.valid(payload(text='', media_slots=[slot(kind='video')]))

    def test_slot_cap(self):
        self.valid(payload(media_slots=[slot(i) for i in range(16)]))
        self.invalid(payload(media_slots=[slot(i) for i in range(17)]))

    def test_docs_do_not_define_layout(self):
        for name in ('docs/01-overview.md', 'docs/02-protocol.md', 'docs/07-clients.md'):
            text = (ROOT / name).read_text(encoding='utf-8')
            with self.subTest(document=name):
                self.assertNotIn('payload.layout', text)
                self.assertNotIn('`layout`', text)


if __name__ == '__main__':
    unittest.main()
