"""Synthetic epoch-binding and control-state examples, not a provider."""
import copy
import unittest

import jsonschema
from test_security_profile import SCHEMA, PROVIDER, did, sign, verify, b64
from version_fixtures import request, verify_admission


class EpochTests(unittest.TestCase):
    def test_current_state_response_is_bound_to_get_challenge(self):
        challenge = b64(bytes(range(32)))
        state = {'provider_id': did(PROVIDER), 'author_id': did(PROVIDER),
                 'state_revision': 0, 'status': 'unregistered', 'epoch': None}
        state['provider_signature'] = sign(PROVIDER, 'authorization-epoch-state', state)
        response = {'challenge': challenge, 'state': state}
        signature = sign(PROVIDER, 'authorization-epoch-state-response', response)
        signed_response = dict(response, provider_signature=signature)
        validator = jsonschema.Draft202012Validator(dict(SCHEMA, **{'$ref': '#/$defs/AuthorizationEpochStateResponse'}))
        self.assertTrue(validator.is_valid(signed_response))
        verify(did(PROVIDER), 'authorization-epoch-state-response', response, signature)
        replay = copy.deepcopy(response)
        replay['challenge'] = b64(bytes(reversed(range(32))))
        with self.assertRaises(Exception):
            verify(did(PROVIDER), 'authorization-epoch-state-response', replay, signature)

    def test_delegation_commits_to_provider_epoch(self):
        valid = request(delegated=True)
        verify_admission(valid)
        altered = copy.deepcopy(valid)
        altered['intent']['delegation']['epoch']['epoch_sequence'] += 1
        with self.assertRaises(Exception):
            verify_admission(altered)

    def test_arbitrary_delegation_id_and_missing_epoch_are_rejected(self):
        validator = jsonschema.Draft202012Validator(dict(SCHEMA, **{'$ref': '#/$defs/Delegation'}))
        d = request(delegated=True)['intent']['delegation']
        self.assertTrue(validator.is_valid(d))
        for field in ('epoch', 'delegation_id'):
            bad = copy.deepcopy(d)
            if field == 'epoch':
                del bad[field]
            else:
                bad[field] = 'arbitrary'
            self.assertFalse(validator.is_valid(bad))


if __name__ == '__main__':
    unittest.main()
