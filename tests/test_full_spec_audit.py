"""Regression examples for normative predicates; not deployed service code."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import unittest
import jsonschema
import rfc8785
from test_security_profile import ROOT, AUTHOR, PROVIDER, I, M, did, sign, verify, encryption_vector
from test_operations_profile import structural

S=json.loads((ROOT/'schemas/launch.schema.json').read_text())
def shape(x): jsonschema.Draft202012Validator(S, format_checker=jsonschema.FormatChecker()).validate(x)

def deadline(start, seconds):
    if type(seconds) is not int or not 0 <= seconds <= 9007199254740991: raise ValueError('unsafe duration')
    try: return start+timedelta(seconds=seconds)
    except OverflowError as exc: raise ValueError('unrepresentable deadline') from exc

def receipt_result(record, authenticated, fresh, revoked, payment_verified):
    # Abstract transition model of lookup ordering, not a concurrent ledger.
    if not authenticated: raise ValueError('unauthorized')
    if record is not None: return record,0
    if not fresh or revoked or not payment_verified: raise ValueError('new issuance forbidden')
    return 'new-receipt',1

def manifest_update(prior_version, prior_digest, version, digest):
    if version<prior_version: raise ValueError('rollback')
    if version==prior_version and digest!=prior_digest: raise ValueError('equivocation')
    return version,digest

def require_approved_challenge(approved, returned):
    for field in ['service_id','author_id','method','resource','body_hash']:
        if approved[field]!=returned[field]: raise ValueError('unapproved signing request')

class FullAuditTests(unittest.TestCase):
    def test_deadline_overflow(self):
        start=datetime(2026,11,11,tzinfo=timezone.utc)
        self.assertEqual(deadline(start,86400).day,12)
        for value in [9007199254740991,-1,True,1.5]:
            with self.assertRaises(ValueError): deadline(start,value)
        with self.assertRaises(ValueError): deadline(datetime(9999,12,31,tzinfo=timezone.utc),86400)
    def test_retry_before_current_issuance_checks(self):
        self.assertEqual(receipt_result('original',True,False,True,0),('original',0))
        with self.assertRaises(ValueError): receipt_result(None,True,False,True,0)
        with self.assertRaises(ValueError): receipt_result('original',False,True,False,100)
    def test_binary_media_contracts_removed(self):
        for name in ['ContentAddress','ContentObject','ContentRetrievalResponse']:
            self.assertNotIn(name,S['$defs'])
        for field,value in [('content_address','ipfs://bafkreiaaaaaa'),('content_manifest',[])]:
            m=copy.deepcopy(M); m[field]=value
            with self.assertRaises(jsonschema.ValidationError): shape(m)
    def test_plaintext_private_fields_rejected(self):
        v=encryption_vector()
        recipient=dict(v['recipient'],wrap_nonce=v['wrap_nonce'],wrapped_key=v['wrapped_key'])
        m={'message_id':M['message_id'],'author_id':did(AUTHOR),'timestamp':I['timestamp'],
           'version':I['version'],'message_type':'archive_record','signature':M['signature'],
           'payload':{'state_kind':'export.prepared-admission.v1','device_group_id':'test-group','state_sequence':0,
                      'supersedes':[],'encryption_scope':'device_group','encryption_scheme':'x25519-xchacha20poly1305',
                      'encrypted_state':{'v':1,'nonce':v['nonce'],'ciphertext':v['ciphertext'],'recipients':[recipient]}}}
        jsonschema.Draft202012Validator(dict(S,**{'$ref':'#/$defs/ArchiveRecord'})).validate(m)
        for field in ['state_summary','plaintext_preferences','compaction_kind']:
            bad=copy.deepcopy(m); bad['payload'][field]='private follow list'
            with self.assertRaises(jsonschema.ValidationError): jsonschema.Draft202012Validator(dict(S,**{'$ref':'#/$defs/ArchiveRecord'})).validate(bad)
        for field,value in [('keywords',['secret']),('content_manifest',[]),('language','en')]:
            bad=copy.deepcopy(m); bad[field]=value
            with self.assertRaises(jsonschema.ValidationError): jsonschema.Draft202012Validator(dict(S,**{'$ref':'#/$defs/ArchiveRecord'})).validate(bad)
    def test_attachment_shape_and_combined_limit(self):
        refs=[{'id':str(i),'url':f'https://media.example/{i}', 'kind':'image' if i%2 else 'video','sha256':'a'*64} for i in range(17)]
        for kind,target in [('post',None),('post','reply_to')]:
            m=copy.deepcopy(M); m['message_type']=kind
            if target: m['payload'][target]=M['message_id']
            if kind=='reply': m['thread_id']=M['message_id']
            for count in [0,1,16]:
                m['payload']['media_slots']=refs[:count]; shape(m)
            m['payload']['media_slots']=refs
            with self.assertRaises(jsonschema.ValidationError): shape(m)
        for ref in [{'id':'x','url':'https://media.example/a'}, 'ipfs://bafkreiaaaaaa',
                    {'id':'x','url':'https://media.example/a','kind':'audio'},
                    {'id':'x','url':'https://media.example/a','kind':'image','bytes':'AAAA'},
                    *[{'id':'x','url':url,'kind':'image'} for url in ['http://media.example/a','data:image/png;base64,AA==',
                      'file:///a','blob:https://media.example/a','https://user:password@media.example/a',
                      'https://media.example\\@internal.example/a']]]:
            m=copy.deepcopy(M); m['payload']['media_slots']=[ref]
            with self.subTest(ref=ref),self.assertRaises(jsonschema.ValidationError): shape(m)

    def test_service_authorization_operation_and_body_binding(self):
        c={'challenge':'a'*43,'service_id':did(PROVIDER),'author_id':did(AUTHOR),'method':'POST',
           'resource':'/v1/fee-quotes','body_hash':hashlib.sha256(b'quote').hexdigest(),
           'expires_at':'2026-11-11T00:01:00Z'}
        structural('ServiceChallenge',c); proof=sign(AUTHOR,'service-auth',c)
        verify(did(AUTHOR),'service-auth',c,proof)
        for field,value in [('resource','/v1/admissions'),('body_hash','0'*64),('service_id',did(AUTHOR))]:
            with self.assertRaises(Exception): verify(did(AUTHOR),'service-auth',dict(c,**{field:value}),proof)
        with self.assertRaises(Exception): verify(did(AUTHOR),'sync-auth',c,proof)
    def test_manifest_rollback_and_equivocation(self):
        self.assertEqual(manifest_update(2,'b',3,'c'),(3,'c'))
        self.assertEqual(manifest_update(2,'b',2,'b'),(2,'b'))
        with self.assertRaises(ValueError): manifest_update(2,'b',1,'a')
        with self.assertRaises(ValueError): manifest_update(2,'b',2,'different')
    def test_final_message_size_includes_receipt(self):
        m=copy.deepcopy(M); m['payload']['text']=''
        remaining=1048576-len(rfc8785.dumps(m))
        m['payload']['text']='x'*remaining
        self.assertEqual(len(rfc8785.dumps(m)),1048576)
        m['submission_receipt']['receipt_id']+='x'
        self.assertGreater(len(rfc8785.dumps(m)),1048576)
        self.assertLess(len(rfc8785.dumps({k:v for k,v in m.items() if k not in ['signature','submission_receipt','message_id']})),1048576)

    def test_challenge_must_match_user_approved_request(self):
        approved={'service_id':did(PROVIDER),'author_id':did(AUTHOR),'method':'POST',
                  'resource':'/v1/fee-quotes','body_hash':'a'*64}
        require_approved_challenge(approved,dict(approved))
        for field,value in [('resource','/v1/admissions'),('body_hash','b'*64),('author_id',did(PROVIDER)),('method','PUT')]:
            with self.assertRaises(ValueError): require_approved_challenge(approved,dict(approved,**{field:value}))

if __name__=='__main__': unittest.main()
