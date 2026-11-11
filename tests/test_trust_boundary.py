"""Cryptographic/local-policy distinction; not a live federated network."""
import copy
import unittest
import jsonschema
from nacl.signing import SigningKey
from test_security_profile import AUTHOR,PROVIDER,I,R,SCHEMA,did,mid,sign,verify

OTHER=SigningKey(bytes(range(96,128)))


def issue(intent,provider):
    receipt={k:v for k,v in R.items() if k!='provider_signature'}
    receipt.update(provider_id=did(provider),author_id=intent['author_id'],message_id=mid(intent))
    receipt['provider_signature']=sign(provider,'receipt',receipt)
    message=dict(intent,message_id=mid(intent),submission_receipt=receipt)
    message['signature']=sign(AUTHOR,'message',message)
    return message


def classify(message,trusted,accepted=frozenset()):
    try:
        jsonschema.Draft202012Validator(SCHEMA).validate(message)
        intent={k:v for k,v in message.items() if k not in ['message_id','signature','submission_receipt']}
        if mid(intent)!=message['message_id']: return 'invalid'
        receipt=message['submission_receipt']
        if receipt['message_id']!=message['message_id'] or receipt['author_id']!=message['author_id']: return 'invalid'
        verify(receipt['provider_id'],'receipt',{k:v for k,v in receipt.items() if k!='provider_signature'},receipt['provider_signature'])
        verify(message['author_id'],'message',{k:v for k,v in message.items() if k!='signature'},message['signature'])
        if receipt['provider_id'] not in trusted: return 'cryptographically_valid_untrusted'
        if (message['message_id'],receipt['provider_id']) not in accepted: return 'cryptographically_valid_trusted_unaccepted'
        return 'locally_admitted'
    except Exception: return 'invalid'


class TrustBoundaryTests(unittest.TestCase):
    def test_independent_receipts_same_intent_and_local_trust(self):
        a=issue(copy.deepcopy(I),PROVIDER); b=issue(copy.deepcopy(I),OTHER)
        self.assertEqual(a['message_id'],b['message_id'])
        self.assertNotEqual(a['signature'],b['signature'])  # receipt itself is author-signed
        self.assertEqual(classify(a,{did(PROVIDER)}),'cryptographically_valid_trusted_unaccepted')
        self.assertEqual(classify(a,{did(PROVIDER)},{(a['message_id'],did(PROVIDER))}),'locally_admitted')
        self.assertEqual(classify(a,{did(OTHER)}),'cryptographically_valid_untrusted')
        self.assertEqual(classify(b,{did(OTHER)},{(b['message_id'],did(OTHER))}),'locally_admitted')
        bad=copy.deepcopy(a); bad['payload']['text']='tampered'
        self.assertEqual(classify(bad,{did(PROVIDER)}),'invalid')

    def test_offline_provider_exit_retains_identity_but_not_old_trust(self):
        archived=issue(copy.deepcopy(I),PROVIDER)
        fresh=copy.deepcopy(I); fresh['payload']['text']='New provider, same user'
        posted=issue(fresh,OTHER)
        self.assertEqual(archived['author_id'],posted['author_id'])
        self.assertNotEqual(archived['message_id'],posted['message_id'])
        self.assertEqual(classify(archived,{did(OTHER)}),'cryptographically_valid_untrusted')
        self.assertEqual(classify(posted,{did(OTHER)},{(posted['message_id'],did(OTHER))}),'locally_admitted')

if __name__=='__main__': unittest.main()
