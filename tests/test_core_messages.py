"""Core message/comment contracts; no social-app implementation."""
import copy
import hashlib
import json
import unittest
import jsonschema
from test_security_profile import ROOT, I, M, R, SCHEMA, AUTHOR, PROVIDER, did, mid, sign, validate, b64


def post(text,parent=None):
    intent=copy.deepcopy(I); intent['payload']['text']=text
    if parent is not None: intent['payload']['reply_to']=parent
    receipt={k:v for k,v in R.items() if k!='provider_signature'}
    receipt['message_id']=mid(intent)
    receipt['receipt_id']=b64(hashlib.sha256(receipt['message_id'].encode()).digest())  # deterministic synthetic ID
    receipt['provider_signature']=sign(PROVIDER,'receipt',receipt)
    message=dict(intent,message_id=mid(intent),submission_receipt=receipt)
    message['signature']=sign(AUTHOR,'message',message)
    return message


class CoreMessageTests(unittest.TestCase):
    def test_comments_are_paid_posts_with_signed_parent(self):
        comment=post('A comment',M['message_id']); validate(comment)
        nested=post('Nested comment',comment['message_id']); validate(nested)
        self.assertEqual(comment['message_type'],'post')
        self.assertEqual(nested['payload']['reply_to'],comment['message_id'])
        mutated=copy.deepcopy(comment); mutated['payload']['reply_to']=nested['message_id']
        with self.assertRaisesRegex(ValueError,'id mismatch'): validate(mutated)
        del comment['submission_receipt']
        with self.assertRaises(jsonschema.ValidationError): validate(comment)

    def test_public_thread_example_has_distinct_signed_receipts(self):
        data=json.loads((ROOT/'examples/post-comment-thread.json').read_text(encoding='utf-8'))
        records=data['messages']
        for message in records: validate(message)
        self.assertEqual(records[1]['payload']['reply_to'],records[0]['message_id'])
        self.assertEqual(records[2]['payload']['reply_to'],records[1]['message_id'])
        self.assertEqual(len({m['submission_receipt']['receipt_id'] for m in records}),len(records))

    def test_unknown_parent_is_an_unresolved_reference(self):
        comment=post('Parent currently unavailable','fy1:'+'b'*64)
        validate(comment)  # validity does not assert parent existence or authorship
        for value in ['https://attacker.example/parent','not-a-message-id']:
            bad=copy.deepcopy(comment); bad['payload']['reply_to']=value
            with self.assertRaises(jsonschema.ValidationError): validate(bad)
        for field,value in [('thread_id',M['message_id']),('likes',100),('favorites',[])]:
            bad=copy.deepcopy(comment); bad['payload'][field]=value
            with self.assertRaises(jsonschema.ValidationError): validate(bad)

    def test_public_page_is_bounded_and_has_no_app_state(self):
        schema=dict(SCHEMA,**{'$ref':'#/$defs/DiscoveryPage'})
        page={'generated_at':I['timestamp'],'expires_at':'2026-11-11T00:15:00Z','messages':[M,post('Comment',M['message_id'])],'next_cursor':None}
        jsonschema.Draft202012Validator(schema).validate(page)
        page['messages']=[M]*101
        with self.assertRaises(jsonschema.ValidationError): jsonschema.Draft202012Validator(schema).validate(page)
        page['messages']=[dict(M,message_type='archive_record')]
        with self.assertRaises(jsonschema.ValidationError): jsonschema.Draft202012Validator(schema).validate(page)

    def test_removed_credit_plan_is_not_part_of_v2(self):
        self.assertNotIn('LaunchPlan', SCHEMA['$defs'])
        self.assertEqual(M['message_type'], 'post')

if __name__=='__main__': unittest.main()
