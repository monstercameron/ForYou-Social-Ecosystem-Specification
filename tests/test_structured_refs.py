"""Structured-reference conformance examples; not a CommonMark renderer or server."""
import copy
import re
import unittest
from unittest.mock import Mock

import jsonschema
import rfc8785

from test_security_profile import AUTHOR, I, SCHEMA, did, mid, pub, sign, verify


ID = re.compile(r'[a-z0-9_-]{1,32}\Z')
MESSAGE = re.compile(r'fy1:[0-9a-f]{64}\Z')
VALIDATOR = jsonschema.Draft202012Validator(dict(SCHEMA, **{'$ref': '#/$defs/PostPayload'}))


def validate_refs(payload, fetch):
    """Small semantic reference: validate signed refs without accessing targets."""
    VALIDATOR.validate(payload)
    ids, targets = set(), set()
    for entry in payload.get('refs', []):
        identifier, target = entry['id'], entry['target']
        if not ID.fullmatch(identifier) or identifier in ids or target in targets:
            raise ValueError('duplicate or invalid reference')
        if not MESSAGE.fullmatch(target):
            try:
                pub(target)  # Includes canonical did:key codec and strict public-key checks.
            except (ValueError, OverflowError, IndexError) as exc:
                raise ValueError('invalid target') from exc
        ids.add(identifier)
        targets.add(target)
    # `fetch` is intentionally not used by admission validation.
    return {entry['id']: entry['target'] for entry in payload.get('refs', [])}


def resolve_parsed_ref(identifier, label, references, local_petnames):
    """Input is already parsed; no parsing, notification, or network access here."""
    if not ID.fullmatch(identifier) or identifier not in references:
        return {'kind': 'text', 'label': label}
    target = references[identifier]
    return {'kind': 'reference', 'label': label, 'target': target,
            'identity_display': local_petnames.get(target, target)}


class StructuredReferencesTests(unittest.TestCase):
    def payload(self, refs):
        return {'content_format': 'text/markdown', 'text': 'hello', 'refs': refs}

    def test_valid_canonical_targets_and_no_admission_fetch(self):
        target = did(AUTHOR)
        fetch = Mock(side_effect=AssertionError('admission must not fetch'))
        refs = [{'id': 'alice', 'target': target}, {'id': 'post_1', 'target': 'fy1:' + 'a' * 64}]
        self.assertEqual(validate_refs(self.payload(refs), fetch), {'alice': target, 'post_1': 'fy1:' + 'a' * 64})
        fetch.assert_not_called()

    def test_32_reference_limit_and_duplicate_semantics(self):
        refs = [{'id': 'r' + str(i), 'target': 'fy1:' + format(i, '064x')} for i in range(32)]
        self.assertEqual(len(validate_refs(self.payload(refs), Mock())), 32)
        with self.assertRaises(jsonschema.ValidationError):
            validate_refs(self.payload(refs + [{'id': 'r32', 'target': 'fy1:' + 'f' * 64}]), Mock())
        same_id = [refs[0], dict(refs[1], id=refs[0]['id'])]
        same_target = [refs[0], dict(refs[1], target=refs[0]['target'])]
        for invalid in (same_id, same_target):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_refs(self.payload(invalid), Mock())

    def test_invalid_id_and_noncanonical_did_rejected(self):
        for entry in ({'id': 'Bad!', 'target': 'fy1:' + 'a' * 64},
                      {'id': 'x', 'target': did(AUTHOR) + '#fragment'},
                      {'id': 'x', 'target': 'did:key:z6Mk1'},
                      {'id': 'x', 'target': 'fy1:' + 'A' * 64}):
            with self.subTest(entry=entry), self.assertRaises((ValueError, jsonschema.ValidationError)):
                validate_refs(self.payload([entry]), Mock())

    def test_missing_ref_inert_and_untrusted_label_cannot_hide_target(self):
        target = did(AUTHOR)
        references = {'a': target}
        self.assertEqual(resolve_parsed_ref('missing', '@bank', references, {})['kind'], 'text')
        shown = resolve_parsed_ref('a', '@bank', references, {})
        self.assertEqual(shown['target'], target)
        self.assertEqual(shown['identity_display'], target)
        self.assertEqual(resolve_parsed_ref('a', '@bank', references, {target: 'My contact'})['identity_display'], 'My contact')

    def test_references_are_in_signed_intent_and_billable_bytes(self):
        base = copy.deepcopy(I)
        base['payload']['content_format'] = 'text/markdown'
        base['payload']['text'] = '[@alice](fy-ref:r1)'
        with_ref = copy.deepcopy(base)
        with_ref['payload']['refs'] = [{'id': 'r1', 'target': did(AUTHOR)}]
        self.assertGreater(len(rfc8785.dumps(with_ref)), len(rfc8785.dumps(base)))
        self.assertNotEqual(mid(base), mid(with_ref))
        signature = sign(AUTHOR, 'admission', {'message_id': mid(with_ref)})
        verify(did(AUTHOR), 'admission', {'message_id': mid(with_ref)}, signature)
        altered = copy.deepcopy(with_ref)
        altered['payload']['refs'][0]['target'] = 'fy1:' + 'b' * 64
        with self.assertRaises(Exception):
            verify(did(AUTHOR), 'admission', {'message_id': mid(altered)}, signature)


if __name__ == '__main__':
    unittest.main()
