"""Draft v2 fee and media checks with synthetic values, not a live payment verifier."""
import copy
import hashlib
import json
import unittest
import jsonschema
import rfc8785
from test_security_profile import ROOT, SCHEMA, pre, verify, intent, validate
from test_operations_profile import structural


def check_quote(schedule, quote, message):
    structural('FeeSchedule', schedule)
    structural('FeeQuote', quote)
    core={k:v for k,v in schedule.items() if k!='schedule_id'}
    if schedule['schedule_id']!='fyfs2:'+hashlib.sha256(pre('fee-schedule-id',core)).hexdigest(): raise ValueError('schedule ID')
    core={k:v for k,v in quote.items() if k not in ('quote_id','provider_signature')}
    if quote['quote_id']!='fyfq2:'+hashlib.sha256(pre('fee-quote-id',core)).hexdigest(): raise ValueError('quote ID')
    verify(quote['provider_id'],'fee-quote',{k:v for k,v in quote.items() if k!='provider_signature'},quote['provider_signature'])
    n=len(rfc8785.dumps(intent(message)))
    price=int(schedule['base_fee_base_units'])+int(schedule['per_kib_fee_base_units'])*((n+1023)//1024)
    if quote['billable_bytes']!=n or int(quote['amount_base_units'])!=price: raise ValueError('fee')
    if quote['schedule_id']!=schedule['schedule_id'] or quote['message_id']!=message['message_id']: raise ValueError('binding')
    if quote['author_id']!=message['author_id'] or quote['network']!=schedule['network']: raise ValueError('binding')
    receipt=message['submission_receipt']
    for name in ('provider_id','author_id','message_id','quote_id','schedule_id','network','amount_base_units'):
        if receipt[name]!=quote[name]: raise ValueError('receipt binding')


def check_slots(message):
    slots=message['payload'].get('media_slots',[])
    ids=[slot['id'] for slot in slots]
    if len(ids)!=len(set(ids)): raise ValueError('duplicate slot ID')


class FeeSlotTests(unittest.TestCase):
    def test_signed_synthetic_quote_and_slot_bindings(self):
        x=json.loads((ROOT/'examples/post-with-media-slots.json').read_text(encoding='utf-8'))
        m=x['message']
        validate(m); check_slots(m); check_quote(x['schedule'],x['quotes'][0],m)
        changed=copy.deepcopy(x['quotes'][0]); changed['amount_base_units']='3'
        with self.assertRaises(ValueError): check_quote(x['schedule'],changed,m)
        changed=copy.deepcopy(m); duplicate=copy.deepcopy(changed['payload']['media_slots'][0])
        duplicate['url']='https://media.example/different'; changed['payload']['media_slots'].append(duplicate)
        self.assertTrue(jsonschema.Draft202012Validator(SCHEMA).is_valid(changed))
        with self.assertRaises(ValueError): check_slots(changed)

    def test_fee_ceil_and_schema_bounds(self):
        for n,units in [(1,1),(1023,1),(1024,1),(1025,2),(2048,2)]:
            self.assertEqual((n+1023)//1024,units)
        x=json.loads((ROOT/'examples/post-with-media-slots.json').read_text(encoding='utf-8'))
        m=copy.deepcopy(x['message']); m['payload']['media_slots'][0]['id']='Invalid space'
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(SCHEMA).validate(m)

    def test_fee_schema_rejects_protocol_defined_split(self):
        x=json.loads((ROOT/'examples/fee-schedule.example.json').read_text(encoding='utf-8'))
        schedule=copy.deepcopy(x['schedule'])
        changed=copy.deepcopy(schedule); changed['split']=[{'role':'replica','basis_points':2000}]
        with self.assertRaises(jsonschema.ValidationError): structural('FeeSchedule',changed)

if __name__=='__main__': unittest.main()
