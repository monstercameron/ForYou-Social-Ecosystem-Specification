"""Executable crypto vectors, not a production admission implementation."""
import base64
import copy
import hashlib
import hmac
import json
from pathlib import Path
import unittest

import jsonschema
import rfc8785
from nacl import bindings as sodium
from nacl.signing import SigningKey, VerifyKey

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'schemas/launch.schema.json').read_text())
B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def b64(b):
    return base64.urlsafe_b64encode(b).decode().rstrip('=')

def un64(s):
    b = base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))
    if b64(b) != s:
        raise ValueError('noncanonical base64url')
    return b

def did(key):
    raw = b'\xed\x01' + bytes(key.verify_key)
    n = int.from_bytes(raw, 'big'); out = ''
    while n:
        n, r = divmod(n, 58); out = B58[r] + out
    return 'did:key:z' + out

def pub(identity):
    if not identity.startswith('did:key:z'):
        raise ValueError('DID method')
    n = 0
    for c in identity[9:]:
        n = n * 58 + B58.index(c)
    raw = n.to_bytes((n.bit_length() + 7) // 8, 'big')
    if len(raw) != 34 or raw[:2] != b'\xed\x01' or identity[9:10] == '1':
        raise ValueError('key encoding')
    if not sodium.crypto_core_ed25519_is_valid_point(raw[2:]):
        raise ValueError('invalid point')
    return raw[2:]

def pre(label, obj):
    return ('ForYou/1/' + label + '\n').encode() + rfc8785.dumps(obj)

def sign(key, label, obj):
    return b64(key.sign(pre(label, obj)).signature)

def verify(identity, label, obj, sig):
    raw = un64(sig)
    if len(raw) != 64 or not sodium.crypto_core_ed25519_is_valid_point(raw[:32]):
        raise ValueError('signature encoding')
    VerifyKey(pub(identity)).verify(pre(label, obj), raw)

def intent(m):
    return {k:v for k,v in m.items() if k not in ('message_id','signature','submission_receipt')}

def mid(i):
    return 'fy1:' + hashlib.sha256(pre('intent', i)).hexdigest()

AUTHOR = SigningKey(bytes(range(32)))
PROVIDER = SigningKey(bytes(range(32,64)))
I = {'author_id':did(AUTHOR),'timestamp':'2026-11-11T00:00:00Z',
     'message_type':'post','version':{'major':1,'minor':0},
     'payload':{'content_format':'text/plain','content_summary':'Unicode: café 🌐'}}
R = {'provider_id':did(PROVIDER),'plan_id':'fyp1:'+'a'*64,'receipt_id':'receipt-1',
     'message_id':mid(I),'author_id':did(AUTHOR),'issued_at':'2026-11-11T00:00:01Z','units_charged':1}
R['provider_signature'] = sign(PROVIDER,'receipt',R)
M = dict(I,message_id=mid(I),submission_receipt=R)
M['signature'] = sign(AUTHOR,'message',M)

def validate(m):
    """Core direct-author public path only; stateful checks require a service."""
    jsonschema.Draft202012Validator(SCHEMA,format_checker=jsonschema.FormatChecker()).validate(m)
    if 'signer_id' in m or m['message_type']=='private_state_update':
        raise ValueError('outside this test validator scope')
    if mid(intent(m)) != m['message_id']:
        raise ValueError('id mismatch')
    r=m['submission_receipt']
    if r['provider_id'] != did(PROVIDER) or r['author_id'] != m['author_id'] or r['message_id'] != m['message_id']:
        raise ValueError('receipt binding/trust')
    verify(r['provider_id'],'receipt',{k:v for k,v in r.items() if k!='provider_signature'},r['provider_signature'])
    verify(m['author_id'],'message',{k:v for k,v in m.items() if k!='signature'},m['signature'])

def encryption_vector():
    # Fixed keys/nonces ONLY for reproducible tests, never production.
    recipient_sk=bytes(range(32)); ephemeral_sk=bytes(range(32,64))
    recipient=sodium.crypto_scalarmult_base(recipient_sk)
    ephemeral=sodium.crypto_scalarmult_base(ephemeral_sk)
    c={'author_id':did(AUTHOR),'device_group_id':'test-group','state_kind':'curation.v1',
       'state_sequence':0,'timestamp':I['timestamp'],'version':I['version']}
    a=pre('private-state',c)
    r={'kid':b64(recipient),'recipient_pubkey':b64(recipient),'epk':b64(ephemeral)}
    info=pre('private-wrap',r)
    shared=sodium.crypto_scalarmult(ephemeral_sk,recipient)
    prk=hmac.new(bytes(32),shared,hashlib.sha256).digest()
    wrapping=hmac.new(prk,info+b'\x01',hashlib.sha256).digest()
    key=bytes(range(64,96)); nonce=bytes(range(24)); wn=bytes(range(24,48))
    plain=rfc8785.dumps({'muted_sources':[]})
    cipher=sodium.crypto_aead_xchacha20poly1305_ietf_encrypt(plain,a,nonce,key)
    wrapped=sodium.crypto_aead_xchacha20poly1305_ietf_encrypt(key,a+info,wn,wrapping)
    return dict(context=c,recipient=r,recipient_secret=b64(recipient_sk),ephemeral_secret=b64(ephemeral_sk),
                aad=b64(a),info=b64(info),wrapping_key=b64(wrapping),content_key=b64(key),
                nonce=b64(nonce),wrap_nonce=b64(wn),plaintext=b64(plain),ciphertext=b64(cipher),wrapped_key=b64(wrapped))

class ProfileTests(unittest.TestCase):
    def test_schema(self):
        jsonschema.Draft202012Validator.check_schema(SCHEMA)
    def test_valid(self):
        validate(M)
    def test_substitution(self):
        for field,value in [('author_id',did(PROVIDER)),('timestamp','2026-11-11T00:00:02Z'),
                            ('payload',{'content_format':'text/plain','content_summary':'stolen receipt'}),
                            ('version',{'major':2,'minor':0})]:
            with self.subTest(field=field):
                m=copy.deepcopy(M); m[field]=value
                with self.assertRaises(Exception): validate(m)
    def test_recomputed_id_still_rejects_copied_receipt(self):
        m=copy.deepcopy(M); m['payload']['content_summary']='replacement'; m['message_id']=mid(intent(m))
        m['signature']=sign(AUTHOR,'message',{k:v for k,v in m.items() if k!='signature'})
        with self.assertRaises(Exception): validate(m)
    def test_receipt_tampering(self):
        m=copy.deepcopy(M); m['submission_receipt']['units_charged']=2
        with self.assertRaises(Exception): validate(m)
    def test_unsigned_unknown_field(self):
        m=copy.deepcopy(M); m['unsigned_override']=True
        with self.assertRaises(Exception): validate(m)
    def test_domain_separation(self):
        with self.assertRaises(Exception): verify(did(AUTHOR),'receipt',I,sign(AUTHOR,'message',I))
    def test_noncanonical_encoding(self):
        with self.assertRaises(ValueError): un64(M['signature']+'=')
    def test_no_token_only_or_extension_acceptance(self):
        for t in ['recommend','follow_source','follow_topic','subscribe_thread','alias_registration','poll','advertisement']:
            m=copy.deepcopy(M); m.pop('submission_receipt'); m['message_type']=t
            with self.assertRaises(Exception): validate(m)
    def test_encryption(self):
        v=encryption_vector(); a=un64(v['aad']); info=un64(v['info'])
        # Derive from recipient side, not the ephemeral side used to encrypt.
        shared=sodium.crypto_scalarmult(un64(v['recipient_secret']),un64(v['recipient']['epk']))
        prk=hmac.new(bytes(32),shared,hashlib.sha256).digest()
        wrapping=hmac.new(prk,info+b'\x01',hashlib.sha256).digest()
        key=sodium.crypto_aead_xchacha20poly1305_ietf_decrypt(un64(v['wrapped_key']),a+info,un64(v['wrap_nonce']),wrapping)
        self.assertEqual(sodium.crypto_aead_xchacha20poly1305_ietf_decrypt(un64(v['ciphertext']),a,un64(v['nonce']),key),un64(v['plaintext']))
        for altered in [a+b'x',a.replace(b'curation.v1',b'curation.v2')]:
            with self.assertRaises(Exception): sodium.crypto_aead_xchacha20poly1305_ietf_decrypt(un64(v['ciphertext']),altered,un64(v['nonce']),key)
        with self.assertRaises(Exception): sodium.crypto_scalarmult(bytes(range(32)),bytes(32))

    def test_pinned_encryption_vector(self):
        pinned=json.loads((ROOT/'tests/security-vectors.json').read_text(encoding='utf-8'))
        self.assertEqual(encryption_vector(),pinned['encryption'])

    def test_complete_extensions_and_token_with_receipt_rejected(self):
        for kind,payload in [('poll',{'prompt':'Question','options':['a','b']}),
                             ('advertisement',dict(I['payload'],sponsor_reference='sponsor'))]:
            m=copy.deepcopy(M); m['message_type']=kind; m['payload']=payload
            if kind=='advertisement': m['is_ad']=True
            with self.assertRaises(jsonschema.ValidationError):
                jsonschema.Draft202012Validator(SCHEMA).validate(m)
        m=copy.deepcopy(M)
        m['submission_token']={'provider_id':did(PROVIDER),'plan_id':'p','token_id':'t',
            'author_id':did(AUTHOR),'tier_scope':'recommend','units_limit':1,
            'valid_from':I['timestamp'],'valid_until':'2026-11-12T00:00:00Z','provider_signature':R['provider_signature']}
        with self.assertRaises(jsonschema.ValidationError): jsonschema.Draft202012Validator(SCHEMA).validate(m)

    def test_valid_tier2_shapes_require_receipts(self):
        shapes={'recommend':{'target_message_id':M['message_id']},
            'follow_source':{'target_author_id':did(PROVIDER)},'follow_topic':{'target_topic':'science'},
            'subscribe_thread':{'target_thread_id':M['message_id']},
            'alias_registration':{'alias':'reader','namespace':did(AUTHOR)}}
        for kind,payload in shapes.items():
            with self.subTest(kind=kind):
                m=copy.deepcopy(M); m['message_type']=kind; m['payload']=payload
                jsonschema.Draft202012Validator(SCHEMA).validate(m)
                m.pop('submission_receipt')
                with self.assertRaises(jsonschema.ValidationError): jsonschema.Draft202012Validator(SCHEMA).validate(m)

if __name__=='__main__':
    import sys
    if '--write-vectors' in sys.argv:
        out={'message':M,'intent_preimage_hex':pre('intent',I).hex(),
             'author_public_key':b64(bytes(AUTHOR.verify_key)), 'provider_public_key':b64(bytes(PROVIDER.verify_key)),
             'encryption':encryption_vector()}
        (ROOT/'tests/security-vectors.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    else: unittest.main()
