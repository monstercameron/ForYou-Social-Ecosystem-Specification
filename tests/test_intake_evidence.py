"""Synthetic confidential-intake schema and receipt checks; no intake server."""
import copy
import hashlib
import unittest

import jsonschema
import rfc8785
from test_operations_profile import OPS
from test_security_profile import PROVIDER, b64, did, pre, sign, verify


def validator(kind):
    return jsonschema.Draft202012Validator(dict(OPS, **{'$ref': '#/$defs/' + kind}))


class IntakeTests(unittest.TestCase):
    def test_request_key_and_receipt_bind_submission(self):
        key = b64(bytes(range(32)))
        operator = did(PROVIDER)
        request_id = b64(hashlib.sha256(pre('intake-id', {'operator_id': operator, 'recovery_key': key})).digest())
        form = {'operator_id': operator, 'form_id': 'base', 'form_version': '1', 'kind': 'notice',
                'fields': [], 'instructions': 'Example only'}
        self.assertTrue(validator('IntakeForm').is_valid(form))
        body = {'operator_id': operator, 'request_id': request_id, 'accept_until': '2026-11-11T00:10:00Z',
                'kind': 'notice', 'form_id': 'base', 'form_version': '1',
                'form_digest': hashlib.sha256(rfc8785.dumps(form)).hexdigest(), 'locators': [],
                'statement': 'Example report', 'evidence_refs': [], 'regional_fields': {}}
        self.assertTrue(validator('IntakeRequest').is_valid(body))
        receipt = {'operator_id': operator, 'request_id': request_id,
                   'request_digest': hashlib.sha256(rfc8785.dumps(body)).hexdigest(),
                   'received_at': '2026-11-11T00:00:00Z', 'status': 'received'}
        receipt['signature'] = sign(PROVIDER, 'intake-receipt', receipt)
        self.assertTrue(validator('IntakeReceipt').is_valid(receipt))
        verify(operator, 'intake-receipt', {k: v for k, v in receipt.items() if k != 'signature'}, receipt['signature'])
        altered = dict(receipt, request_digest='0' * 64)
        with self.assertRaises(Exception):
            verify(operator, 'intake-receipt', {k: v for k, v in altered.items() if k != 'signature'}, altered['signature'])
        self.assertNotIn(key, str(body))
        self.assertNotIn(key, str(receipt))

    def test_kind_specific_fields_and_unknown_fields_rejected(self):
        body = {'operator_id': did(PROVIDER), 'request_id': b64(bytes(32)),
                'accept_until': '2026-11-11T00:10:00Z', 'kind': 'appeal', 'form_id': 'base',
                'form_version': '1', 'form_digest': 'a' * 64, 'locators': [], 'statement': '', 'evidence_refs': [], 'regional_fields': {}}
        check = validator('IntakeRequest')
        self.assertFalse(check.is_valid(body))
        body['decision_reference'] = 'decision'
        self.assertTrue(check.is_valid(body))
        extra = copy.deepcopy(body); extra['credential'] = 'not allowed'
        self.assertFalse(check.is_valid(extra))
        extra = copy.deepcopy(body); extra['requested_right'] = 'access'
        self.assertFalse(check.is_valid(extra))


if __name__ == '__main__':
    unittest.main()
