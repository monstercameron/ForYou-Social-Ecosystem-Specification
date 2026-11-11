"""Contract/fixture checks, not deployed billing, legal or export services."""
import copy
import hashlib
import json
from pathlib import PurePosixPath
import unittest
import jsonschema
from test_security_profile import ROOT, PROVIDER, AUTHOR, did, sign, verify, pre

OPS = json.loads((ROOT/'schemas/operations.schema.json').read_text(encoding='utf-8'))
WIRE = json.loads((ROOT/'schemas/launch.schema.json').read_text(encoding='utf-8'))

def structural(kind, value):
    jsonschema.Draft202012Validator(dict(OPS, **{'$ref':'#/$defs/'+kind}),
                                   format_checker=jsonschema.FormatChecker()).validate(value)

def offer():
    x={'provider_id':did(PROVIDER),'max_message_bytes':1048576,'max_content_bytes_per_message':33554432,
       'retention_seconds':2592000,'read_bytes_per_message':104857600,'discovery_requests_per_message':100,
       'replica_count':2,'availability_target_basis_points':9900,'export_grace_seconds':2592000,
       'terms_digest':hashlib.sha256(b'Synthetic test terms; not a commercial offer.').hexdigest()}
    x['service_offer_id']='fyso1:'+hashlib.sha256(pre('service-offer-id',x)).hexdigest()
    x['signature']=sign(PROVIDER,'service-offer',x)
    return x

def verify_offer(x):
    structural('ServiceOffer',x)
    core={k:v for k,v in x.items() if k not in ['signature','service_offer_id']}
    if 'fyso1:'+hashlib.sha256(pre('service-offer-id',core)).hexdigest()!=x['service_offer_id']:
        raise ValueError('offer commitment mismatch')
    verify(x['provider_id'],'service-offer',{k:v for k,v in x.items() if k!='signature'},x['signature'])

def safe_paths(entries):
    seen=set()
    for x in entries:
        path=x['path']; parts=path.split('/')
        if not path or '\\' in path or ':' in path or any(v in ('','.', '..') for v in parts):
            raise ValueError('unsafe path')
        # Reject Windows device paths too; path extraction still needs no-follow I/O.
        if any(v.endswith(('.', ' ')) or v.split('.')[0].upper() in
               {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]} for v in parts):
            raise ValueError('platform alias')
        key=str(PurePosixPath(path)).casefold()
        if key in seen: raise ValueError('duplicate path')
        seen.add(key)

def monthly(users=1000,read_factor=1,abuse_factor=1,storage_factor=1,reserve_value=20000):
    # All units below are synthetic reporting-currency units, not crypto prices.
    earned=users*10
    delivered=min(1000*read_factor,2000)  # prepaid public-read cap in GiB
    costs=3000 + 1000*storage_factor + delivered*.1 + 500*abuse_factor
    surplus=earned-costs-1000  # reserve replenishment, not double-counted as runway
    return {'earned_revenue':earned,'delivered_gib':delivered,
            'unserved_gib':max(0,1000*read_factor-delivered),'operating_surplus':surplus,
            'reserve_adequate':reserve_value>=15000}

class OperationsTests(unittest.TestCase):
    def test_schema(self):
        jsonschema.Draft202012Validator.check_schema(OPS)
        jsonschema.Draft202012Validator.check_schema(WIRE)
    def test_offer_binding(self):
        x=offer(); verify_offer(x)
        for key,value in [('retention_seconds',1),('terms_digest','0'*64),('replica_count',1)]:
            y=copy.deepcopy(x); y[key]=value
            with self.assertRaises(Exception): verify_offer(y)
    def test_offer_grace_bounds(self):
        x=offer(); x['export_grace_seconds']=1
        with self.assertRaises(jsonschema.ValidationError): structural('ServiceOffer',x)
    def test_plan_commits_offer(self):
        self.assertIn('service_offer_id',WIRE['$defs']['LaunchPlan']['required'])
        a={'provider_id':did(PROVIDER),'service_offer_id':offer()['service_offer_id']}
        b=dict(a,service_offer_id='fyso1:'+'f'*64)
        self.assertNotEqual(hashlib.sha256(pre('plan-id',a)).digest(),hashlib.sha256(pre('plan-id',b)).digest())
    def test_renewal_price_binding(self):
        q={'quote_id':'a'*43,'provider_id':did(PROVIDER),'author_id':did(AUTHOR),'plan_id':'fyp1:'+'a'*64,
           'service_offer_id':offer()['service_offer_id'],'target_message_id':'fy1:'+'b'*64,
           'added_seconds':86400,'units_charge':1,'expires_at':'2026-11-12T00:00:00Z'}
        q['signature']=sign(PROVIDER,'renewal-quote',q); structural('RenewalQuote',q)
        unsigned={k:v for k,v in q.items() if k!='signature'}
        claim={'provider_id':q['provider_id'],'author_id':q['author_id'],'quote_hash':hashlib.sha256(pre('renewal-quote',unsigned)).hexdigest()}
        authorization=sign(AUTHOR,'renewal-order',claim)
        verify(did(AUTHOR),'renewal-order',claim,authorization)
        unsigned['units_charge']=2
        changed=dict(claim,quote_hash=hashlib.sha256(pre('renewal-quote',unsigned)).hexdigest())
        with self.assertRaises(Exception): verify(did(AUTHOR),'renewal-order',changed,authorization)
    def test_export_paths(self):
        safe_paths([{'path':'messages/a.json'}])
        for path in ['../secret','/absolute','a//b','a/./b','C:/secret','a\\b','NUL','a.','a:stream']:
            with self.subTest(path=path),self.assertRaises(ValueError): safe_paths([{'path':path}])
        with self.assertRaises(ValueError): safe_paths([{'path':'a.json'},{'path':'A.JSON'}])
    def test_preferences_not_silent_loss(self):
        x={'profile':'ForYouPreferences-1','followed_author_ids':[did(AUTHOR)],'muted_author_ids':[],
           'blocked_author_ids':[],'bookmarked_message_ids':[],'ranking_preferences':{}}
        structural('Preferences',x)
        del x['followed_author_ids']
        with self.assertRaises(jsonschema.ValidationError): structural('Preferences',x)
    def test_stress_model(self):
        self.assertGreater(monthly()['operating_surplus'],0)
        self.assertEqual(monthly(read_factor=10)['delivered_gib'],2000)
        self.assertEqual(monthly(read_factor=10)['unserved_gib'],8000)
        self.assertLess(monthly(users=500,storage_factor=2,abuse_factor=5)['operating_surplus'],0)
        self.assertFalse(monthly(reserve_value=10000)['reserve_adequate'])

    def test_full_export_requires_one_preferences_snapshot(self):
        x={'profile':'ForYouExport-1','author_id':did(AUTHOR),'created_at':'2026-11-11T00:00:00Z',
           'entries':[],'signature':'a'*86}
        with self.assertRaises(jsonschema.ValidationError): structural('ExportManifest',x)
        e={'path':'private/preferences.json','media_type':'application/json','byte_length':100,
           'sha256':'a'*64,'category':'local_preferences'}
        x['entries']=[e]; structural('ExportManifest',x)
        x['entries'].append(dict(e,path='private/other.json'))
        with self.assertRaises(jsonschema.ValidationError): structural('ExportManifest',x)

    def test_author_page_can_hold_maximum_message(self):
        # UTF-8 byte budget including response envelope and a maximal cursor.
        msg={'payload':'x'*(1048576-14)}
        raw=json.dumps(msg,separators=(',',':')).encode()
        self.assertEqual(len(raw),1048576)
        response={'generated_at':'2026-11-11T00:00:00Z','messages':[msg],'next_cursor':'x'*4096}
        self.assertLess(len(json.dumps(response,separators=(',',':')).encode()),2097152)

if __name__=='__main__': unittest.main()
