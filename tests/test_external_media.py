"""Restricted URL and archive reference checks; not a networking implementation."""
import copy
import ipaddress
import re
import unittest
from urllib.parse import urlsplit
import idna
import jsonschema
import rfc8785
from nacl import bindings as sodium
from test_security_profile import I, R, M, AUTHOR, PROVIDER, SCHEMA, did, mid, sign, verify, validate, encryption_vector, b64, un64, pre


def media_url(value):
    if not isinstance(value,str) or not 1<=len(value)<=4096 or any(ord(c)<33 or ord(c)>126 for c in value) or '\\' in value:
        raise ValueError('ASCII URL')
    match=re.fullmatch(r'https://([^/?#]+)([^?#]*)(?:\?([^#]*))?(?:#(.*))?',value)
    if not match: raise ValueError('HTTPS URL')
    authority,path,query,fragment=match.groups()
    if '@' in authority or '%' in authority: raise ValueError('authority')
    if authority.startswith('['):
        hostpart=re.fullmatch(r'\[([^]]+)\](?::([0-9]+))?',authority)
        if not hostpart: raise ValueError('IPv6 authority')
        host,port=hostpart.groups()
        if str(ipaddress.IPv6Address(host))!=host: raise ValueError('canonical IPv6')
    else:
        hostpart=re.fullmatch(r'([^:]+)(?::([0-9]+))?',authority)
        if not hostpart: raise ValueError('authority/port')
        host,port=hostpart.groups()
        if re.fullmatch(r'[0-9.]+',host):
            if str(ipaddress.IPv4Address(host))!=host: raise ValueError('canonical IPv4')
        else:
            if len(host)>253 or host!=host.lower(): raise ValueError('DNS case/length')
            labels=host.split('.')
            if not re.search('[a-z]',labels[-1]) or labels[-1].startswith('0x'): raise ValueError('numeric host')
            for label in labels:
                if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',label): raise ValueError('DNS label')
                if label.startswith('xn--') and idna.alabel(idna.ulabel(label)).decode()!=label: raise ValueError('A-label')
    if port is not None and (port.startswith('0') or not 1<=int(port)<=65535): raise ValueError('port')
    if path and not path.startswith('/'): raise ValueError('path')
    for component,extra in [(path,''),(query or '','?'),(fragment or '','?')]:
        pattern=r"(?:[A-Za-z0-9\-._~!$&'()*+,;=:@/"+re.escape(extra)+r"]|%[0-9A-Fa-f]{2})*"
        if not re.fullmatch(pattern,component): raise ValueError('URL component')
        if any(int(h,16)<32 or int(h,16) in (92,127) for h in re.findall('%([0-9A-Fa-f]{2})',component)):
            raise ValueError('escaped control/backslash')
    # Compare a second parser, without DNS or requests. Real clients must compare their network stack.
    parsed=urlsplit(value)
    if parsed.scheme!='https' or parsed.hostname!=host or (parsed.port or 443)!=int(port or 443): raise ValueError('parser disagreement')
    return value


def prepared_record(text=None):
    intent=copy.deepcopy(I)
    intent['payload']['media_slots']=[{'id':'photo','url':'https://media.example/photo','kind':'image','sha256':'a'*64,'alt_text':'A photo'}]
    if text is not None: intent['payload']['text']=text
    message_id=mid(intent)
    claim={'provider_id':did(PROVIDER),'author_id':intent['author_id'],'quote_id':R['quote_id'],'message_id':message_id}
    request={'provider_id':claim['provider_id'],'quote_id':claim['quote_id'],'intent':intent,
             'authorization':sign(AUTHOR,'admission',claim)}
    receipt={k:v for k,v in R.items() if k!='provider_signature'}
    receipt['message_id']=message_id
    receipt['provider_signature']=sign(PROVIDER,'receipt',receipt)
    return {'request':request,'receipt':receipt}


def verify_prepared(record):
    jsonschema.Draft202012Validator(dict(SCHEMA,**{'$ref':'#/$defs/PreparedAdmissionRecord'})).validate(record)
    request,receipt=record['request'],record['receipt']; intent=request['intent']; message_id=mid(intent)
    if intent['author_id']!=did(AUTHOR) or request['provider_id']!=did(PROVIDER): raise ValueError('owner/provider')
    for field,value in [('message_id',message_id),('provider_id',request['provider_id']),('quote_id',request['quote_id']),('author_id',intent['author_id'])]:
        if receipt[field]!=value: raise ValueError('binding')
    verify(intent['author_id'],'admission',{'provider_id':request['provider_id'],'author_id':intent['author_id'],'quote_id':request['quote_id'],'message_id':message_id},request['authorization'])
    verify(receipt['provider_id'],'receipt',{k:v for k,v in receipt.items() if k!='provider_signature'},receipt['provider_signature'])
    # Validate public shape without treating a placeholder as a final signature or publishing it.
    proposed=dict(intent,message_id=message_id,submission_receipt=receipt,signature='a'*86)
    jsonschema.Draft202012Validator(SCHEMA,format_checker=jsonschema.FormatChecker()).validate(proposed)
    for ref in intent['payload'].get('media_slots',[]): media_url(ref['url'])
    return 'unpublished'


class ExternalMediaTests(unittest.TestCase):
    def test_url_semantics_without_format_checker(self):
        good=['https://media.example/a?x=1#t=2','https://media.example:65535/a',
              'https://192.0.2.1/a','https://[2001:db8::1]:443/a','https://xn--bcher-kva.example/a%20b']
        bad=['https://example.com:999999/a','https://example.com:abc/a','https://example.com:0/a',
             'https://example.com:/a','https://example.com:0443/a','https://127.1/a','https://2130706433/a',
             'https://0177.0.0.1/a','https://0x7f000001/a','https://example.com./a','https://EXAMPLE.com/a',
             'https://user:pass@example.com/a','https://%65xample.com/a','https://[::1%25zone]/a',
             'https://example.com/%zz','https://example.com/%0d','https://example.com/%5C',
             'https://example.com/a\\b','https://example.com/a\n','https://example.com/é',
             'https://xn--a.example/a','https://example.com/<svg>']
        for value in good:
            with self.subTest(value=value): self.assertEqual(media_url(value),value)
        for value in bad:
            with self.subTest(value=value),self.assertRaises((ValueError,idna.IDNAError)): media_url(value)
        # Syntactic validity never grants permission to fetch a private destination.
        self.assertEqual(media_url('https://127.0.0.1/a'),'https://127.0.0.1/a')

    def test_post_rejects_unapproved_media_storage_fields(self):
        m=copy.deepcopy(M)
        for field,value in [('content_address','ipfs://old'),('content_manifest',[])]:
            bad=copy.deepcopy(m); bad['payload'][field]=value
            with self.assertRaises(jsonschema.ValidationError): jsonschema.Draft202012Validator(SCHEMA).validate(bad)

    def test_actual_admission_receipt_message_media_binding(self):
        record=prepared_record(); self.assertEqual(verify_prepared(record),'unpublished')
        intent=record['request']['intent']; receipt=record['receipt']
        m=dict(intent,message_id=mid(intent),submission_receipt=receipt)
        m['signature']=sign(AUTHOR,'message',m); validate(m)
        for field,value in [('url','https://media.example/other'),('kind','video'),('alt_text','Changed')]:
            changed=copy.deepcopy(m); changed['payload']['media_slots'][0][field]=value
            with self.assertRaisesRegex(ValueError,'id mismatch'): validate(changed)
            changed['message_id']=mid({k:v for k,v in changed.items() if k not in ('message_id','signature','submission_receipt')})
            with self.assertRaisesRegex(ValueError,'receipt binding'): validate(changed)
            with self.assertRaises(Exception): verify(did(AUTHOR),'message',{k:v for k,v in changed.items() if k!='signature'},m['signature'])
            bad=copy.deepcopy(record); bad['request']['intent']['payload']['media_slots'][0][field]=value
            with self.assertRaises(ValueError): verify_prepared(bad)
            claim={'provider_id':did(PROVIDER),'author_id':did(AUTHOR),'quote_id':R['quote_id'],'message_id':changed['message_id']}
            with self.assertRaises(Exception): verify(did(AUTHOR),'admission',claim,record['request']['authorization'])

    def test_maximum_prepared_export_encrypted_roundtrip(self):
        def final_message(record):
            intent=record['request']['intent']
            m=dict(intent,message_id=mid(intent),submission_receipt=record['receipt'])
            m['signature']=sign(AUTHOR,'message',m)
            return m
        empty=prepared_record(text='')
        overhead=max(len(rfc8785.dumps(empty['request'])),len(rfc8785.dumps(final_message(empty))))
        record=prepared_record(text='x'*(1048576-overhead))
        self.assertLessEqual(len(rfc8785.dumps(record['request'])),1048576)
        self.assertLessEqual(len(rfc8785.dumps(record['receipt'])),8192)
        self.assertEqual(len(rfc8785.dumps(final_message(record))),1048576)
        self.assertEqual(verify_prepared(record),'unpublished')
        context={'author_id':did(AUTHOR),'device_group_id':'backup:'+b64(bytes(32)),
                 'state_kind':'export.prepared-admission.v1','state_sequence':0,
                 'timestamp':I['timestamp'],'version':I['version']}
        v=encryption_vector(plaintext=record,context=context)
        recipient=dict(v['recipient'],wrap_nonce=v['wrap_nonce'],wrapped_key=v['wrapped_key'])
        payload={k:context[k] for k in ['device_group_id','state_kind','state_sequence']}
        payload.update(supersedes=[],encryption_scope='device_group',encryption_scheme='x25519-xchacha20poly1305',
                       encrypted_state={'v':1,'nonce':v['nonce'],'ciphertext':v['ciphertext'],'recipients':[recipient]})
        obj={'author_id':did(AUTHOR),'timestamp':I['timestamp'],'version':I['version'],
             'message_type':'archive_record','payload':payload}
        obj['message_id']=mid(obj); obj['signature']=sign(AUTHOR,'message',obj)
        jsonschema.Draft202012Validator(dict(SCHEMA,**{'$ref':'#/$defs/ArchiveRecord'})).validate(obj)
        verify(did(AUTHOR),'message',{k:x for k,x in obj.items() if k!='signature'},obj['signature'])
        file={'kind':'prepared_admission','object':obj}
        self.assertGreater(len(rfc8785.dumps(obj)),1048576)  # public transport MUST reject this archive
        self.assertLess(len(rfc8785.dumps(file)),2097152)
        key=sodium.crypto_aead_xchacha20poly1305_ietf_decrypt(un64(v['wrapped_key']),un64(v['aad'])+un64(v['info']),un64(v['wrap_nonce']),un64(v['wrapping_key']))
        plain=sodium.crypto_aead_xchacha20poly1305_ietf_decrypt(un64(v['ciphertext']),un64(v['aad']),un64(v['nonce']),key)
        self.assertEqual(plain,rfc8785.dumps(record))
        self.assertLessEqual(len(plain),1048576+8192+64)

    def test_prepared_export_remains_unpublished_and_bound(self):
        record=prepared_record(); self.assertEqual(verify_prepared(record),'unpublished')
        with self.assertRaises(jsonschema.ValidationError): jsonschema.Draft202012Validator(SCHEMA).validate(record)
        for section,field,value in [('request','quote_id','fyfq2:'+'b'*64),('receipt','author_id',did(PROVIDER)),('request','authorization','a'*86)]:
            bad=copy.deepcopy(record); bad[section][field]=value
            with self.assertRaises(Exception): verify_prepared(bad)

if __name__=='__main__': unittest.main()
