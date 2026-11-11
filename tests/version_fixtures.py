"""Synthetic signed post/update fixtures; no provider implementation."""
import copy
import hashlib

import jsonschema
from nacl.signing import SigningKey
from test_security_profile import SCHEMA,I,R,AUTHOR,PROVIDER,did,sign,verify,mid,b64,pre

DELEGATE = SigningKey(bytes(range(64,96)))


def request(target=None,delegated=False):
    intent=copy.deepcopy(I)
    intent['payload']['text']='An updated post' if target else 'An original post'
    if target is not None:
        intent['payload']['supersedes']=target
    key=AUTHOR
    if delegated:
        epoch={'provider_id':did(PROVIDER),'author_id':did(AUTHOR),'epoch_sequence':1,
               'activated_at':'2026-11-10T22:00:00Z','nonce':b64(bytes(32))}
        epoch['epoch_id']='fye1:'+hashlib.sha256(pre('authorization-epoch-id',epoch)).hexdigest()
        epoch['provider_signature']=sign(PROVIDER,'authorization-epoch',epoch)
        delegation={'author_id':did(AUTHOR),'signer_id':did(DELEGATE),'epoch':epoch,
                    'valid_from':'2026-11-10T23:00:00Z','valid_until':'2026-11-11T01:00:00Z',
                    'provider_id':did(PROVIDER),'scope':['post']}
        delegation['delegation_id']='fyd1:'+hashlib.sha256(pre('delegation-id',delegation)).hexdigest()
        delegation['delegation_signature']=sign(AUTHOR,'delegation',delegation)
        intent.update(signer_id=did(DELEGATE),delegation=delegation); key=DELEGATE
    claim={'provider_id':did(PROVIDER),'author_id':intent['author_id'],'quote_id':R['quote_id'],'message_id':mid(intent)}
    return {'provider_id':claim['provider_id'],'quote_id':claim['quote_id'],'intent':intent,
            'authorization':sign(key,'admission',claim)}


def verify_admission(req):
    jsonschema.Draft202012Validator(dict(SCHEMA,**{'$ref':'#/$defs/AdmissionRequest'})).validate(req)
    intent=req['intent']
    if intent['message_type']!='post' or req['provider_id']!=did(PROVIDER):
        raise ValueError('type/provider')
    signer=intent.get('signer_id',intent['author_id'])
    if signer!=intent['author_id']:
        d=intent['delegation']
        verify(intent['author_id'],'delegation',{k:v for k,v in d.items() if k!='delegation_signature'},d['delegation_signature'])
        epoch=d['epoch']
        verify(req['provider_id'],'authorization-epoch',{k:v for k,v in epoch.items() if k!='provider_signature'},epoch['provider_signature'])
        if epoch['epoch_id']!='fye1:'+hashlib.sha256(pre('authorization-epoch-id',{k:v for k,v in epoch.items() if k not in ('epoch_id','provider_signature')})).hexdigest(): raise ValueError('epoch id')
        if d['delegation_id']!='fyd1:'+hashlib.sha256(pre('delegation-id',{k:v for k,v in d.items() if k not in ('delegation_id','delegation_signature')})).hexdigest(): raise ValueError('delegation id')
        if epoch['author_id']!=d['author_id'] or epoch['provider_id']!=d['provider_id']: raise ValueError('epoch binding')
        if d['author_id']!=intent['author_id'] or d['signer_id']!=signer or d['provider_id']!=req['provider_id'] or 'post' not in d['scope']:
            raise ValueError('delegation binding')
    verify(signer,'admission',{'provider_id':req['provider_id'],'author_id':intent['author_id'],'quote_id':req['quote_id'],'message_id':mid(intent)},req['authorization'])
