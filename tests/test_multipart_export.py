"""Multipart export reference checks; no deployed storage, transport or filesystem implementation."""
import copy
import hashlib
import hmac
import json
import unittest
import jsonschema
import rfc8785
from test_security_profile import AUTHOR,PROVIDER,did,sign,verify,un64,b64,mid,I,encryption_vector,SCHEMA,pre
from test_operations_profile import OPS,structural,safe_paths
from test_external_media import prepared_record,verify_prepared
from nacl import bindings as sodium


def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return rfc8785.dumps(value)
OWNER=did(AUTHOR)
SNAPSHOT=b64(bytes(range(32)))
CREATED='2026-11-11T00:00:00Z'


def make_entry(path,raw,category='public_message'):
    return {'path':path,'media_type':'application/json','byte_length':len(raw),'sha256':sha(raw),'category':category}


def build_parts(entries):
    parts=[]; descriptors=[]; pending=[]; size=0
    def base(number):
        return {'profile':'ForYouExportPart-1','snapshot_id':SNAPSHOT,'author_id':OWNER,'created_at':CREATED,
                'part_number':number,'entries':[]}
    def flush():
        if not pending: return
        part=base(len(parts)); part['entries']=list(pending); raw=canonical(part)
        descriptors.append({'part_number':len(parts),'byte_length':len(raw),'sha256':sha(raw),'entry_count':len(pending)})
        parts.append(raw)
    for entry in entries:
        encoded_entry=canonical(entry)
        if not pending: size=len(canonical(base(len(parts))))
        addition=len(encoded_entry)+(1 if pending else 0)
        if pending and (len(pending)==10000 or size+addition>4194304):
            flush(); pending=[]; size=len(canonical(base(len(parts)))); addition=len(encoded_entry)
        if size+addition>4194304: raise ValueError('entry metadata too large')
        pending.append(entry); size+=addition
    flush()
    return parts,descriptors


def make_set(entries,source_index_sha256=None):
    parts,descriptors=build_parts(entries)
    manifest={'profile':'ForYouExportSet-1','snapshot_id':SNAPSHOT,'author_id':OWNER,'created_at':CREATED,
              'total_entries':len(entries),'total_bytes':sum(x['byte_length'] for x in entries),
              'parts':descriptors,'coverage':'complete','source_index_sha256':source_index_sha256}
    manifest['signature']=sign(AUTHOR,'export-set',manifest)
    return manifest,parts


def check_parts(manifest,parts):
    if len(canonical(manifest))>1048576: raise ValueError('manifest budget')
    if len(parts)!=len(manifest['parts']): raise ValueError('part count')
    entries=[]
    for number,(descriptor,raw) in enumerate(zip(manifest['parts'],parts)):
        if descriptor['part_number']!=number or len(raw)!=descriptor['byte_length'] or sha(raw)!=descriptor['sha256'] or len(raw)>4194304:
            raise ValueError('part binding')
        part=json.loads(raw); structural('ExportPartManifest',part)
        if canonical(part)!=raw: raise ValueError('noncanonical part')
        if any(part[k]!=manifest[k] for k in ['snapshot_id','author_id','created_at']) or part['part_number']!=number:
            raise ValueError('snapshot binding')
        if len(part['entries'])!=descriptor['entry_count']: raise ValueError('entry count')
        entries.extend(part['entries'])
    if len(entries)!=manifest['total_entries'] or sum(x['byte_length'] for x in entries)!=manifest['total_bytes']:
        raise ValueError('totals')
    if any(not e['path'].startswith('data/') or len(e['path'].encode())>1024 for e in entries): raise ValueError('path prefix/length')
    safe_paths(entries)
    return entries


def check_set(manifest,parts):
    structural('ExportSetManifest',manifest)
    verify(manifest['author_id'],'export-set',{k:v for k,v in manifest.items() if k!='signature'},manifest['signature'])
    return check_parts(manifest,parts)


def check_source_metadata(manifest,local_parts,index_bytes,source_parts):
    local_entries=check_set(manifest,local_parts)
    if manifest['source_index_sha256']!=sha(index_bytes): raise ValueError('source index hash')
    index=json.loads(index_bytes); structural('ExportSetIndex',index)
    if canonical(index)!=index_bytes: raise ValueError('source index canonical form')
    if any(index[k]!=manifest[k] for k in ['snapshot_id','author_id','created_at','coverage']): raise ValueError('source/local identity')
    source_entries=check_parts(index,source_parts)
    source={(x['path'],x['category']):x for x in source_entries}
    local={(x['path'],x['category']):x for x in local_entries}
    if set(source)!=set(local): raise ValueError('source/local members')
    return source,local


def wrap_prepared(plain):
    context={'author_id':OWNER,'device_group_id':'backup:'+b64(bytes(32)),
             'state_kind':'export.prepared-admission.v1','state_sequence':0,'timestamp':CREATED,'version':I['version']}
    v=encryption_vector(plaintext=plain,context=context)
    recipient=dict(v['recipient'],wrap_nonce=v['wrap_nonce'],wrapped_key=v['wrapped_key'])
    payload={k:context[k] for k in ['device_group_id','state_kind','state_sequence']}
    payload.update(supersedes=[],encryption_scope='device_group',encryption_scheme='x25519-xchacha20poly1305',
                   encrypted_state={'v':1,'nonce':v['nonce'],'ciphertext':v['ciphertext'],'recipients':[recipient]})
    obj={'author_id':OWNER,'timestamp':CREATED,'version':I['version'],'message_type':'archive_record','payload':payload}
    obj['message_id']=mid(obj); obj['signature']=sign(AUTHOR,'message',obj)
    jsonschema.Draft202012Validator(dict(SCHEMA,**{'$ref':'#/$defs/ArchiveRecord'})).validate(obj)
    return {'kind':'prepared_admission','object':obj},v


def check_transformation(source_entry,local_entry,wrapped,v):
    if (source_entry['path'],source_entry['category'])!=(local_entry['path'],local_entry['category']): raise ValueError('path/category')
    raw=canonical(wrapped)
    if len(raw)!=local_entry['byte_length'] or sha(raw)!=local_entry['sha256']: raise ValueError('local bytes')
    if wrapped.get('kind')!='prepared_admission': raise ValueError('kind')
    obj=wrapped['object']
    jsonschema.Draft202012Validator(dict(SCHEMA,**{'$ref':'#/$defs/ArchiveRecord'})).validate(obj)
    if obj['author_id']!=OWNER: raise ValueError('wrong owner')
    intent={k:x for k,x in obj.items() if k not in ['message_id','signature','submission_receipt']}
    if mid(intent)!=obj['message_id']: raise ValueError('archive id mismatch')
    verify(obj['author_id'],'message',{k:value for k,value in obj.items() if k!='signature'},obj['signature'])
    payload=obj['payload']
    if not payload['device_group_id'].startswith('backup:') or len(un64(payload['device_group_id'][7:]))!=32: raise ValueError('archive group')
    context={k:obj[k] for k in ['author_id','timestamp','version']}
    context.update({k:payload[k] for k in ['device_group_id','state_kind','state_sequence']})
    encrypted=payload['encrypted_state']; recipient=encrypted['recipients'][0]
    secret=un64(v['recipient_secret'])  # only the independently backed-up owner key is external
    recipient_pub=un64(recipient['recipient_pubkey']); epk=un64(recipient['epk'])
    if sodium.crypto_scalarmult_base(secret)!=recipient_pub or recipient['kid']!=b64(recipient_pub): raise ValueError('recipient binding')
    context_recipient={k:recipient[k] for k in ['kid','recipient_pubkey','epk']}
    info=pre('private-wrap',context_recipient); aad=pre('private-state',context)
    shared=sodium.crypto_scalarmult(secret,epk)
    prk=hmac.new(bytes(32),shared,hashlib.sha256).digest()
    wrapping=hmac.new(prk,info+b'\x01',hashlib.sha256).digest()
    key=sodium.crypto_aead_xchacha20poly1305_ietf_decrypt(un64(recipient['wrapped_key']),aad+info,un64(recipient['wrap_nonce']),wrapping)
    plaintext=sodium.crypto_aead_xchacha20poly1305_ietf_decrypt(un64(encrypted['ciphertext']),aad,un64(encrypted['nonce']),key)
    prepared=json.loads(plaintext); verify_prepared(prepared)
    reconstructed=canonical({'kind':'prepared_admission','object':prepared})
    if len(reconstructed)!=source_entry['byte_length'] or sha(reconstructed)!=source_entry['sha256']: raise ValueError('source bytes')
    return 'unpublished'


class ExportTransport:
    """Model only: caller has separately verified one-use root service-auth."""
    def __init__(self,data,owner=OWNER): self.data=data; self.owner=owner; self.restricted=False; self.invalid=False
    def restrict(self): self.restricted=True; self.invalid=True
    def restore(self): self.restricted=False  # old job remains invalid
    def chunk(self,owner,offset):
        if owner!=self.owner: raise ValueError('not_found')
        if self.invalid: raise ValueError('export_invalidated')
        if not isinstance(offset,int) or offset<0 or offset>len(self.data): raise ValueError('range')
        return self.data[offset:offset+262144]


class MultipartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Metadata represents 10,001 distinct records, with no disk extraction or service claim.
        cls.entries=[make_entry('data/%05d.json'%i,b'x') for i in range(10001)]
        cls.manifest,cls.parts=make_set(cls.entries)

    def test_more_than_ten_thousand_entries(self):
        self.assertEqual([x['entry_count'] for x in self.manifest['parts']],[10000,1])
        self.assertEqual(len(check_set(self.manifest,self.parts)),10001)

    def test_missing_duplicate_reordered_and_substituted_parts(self):
        for parts in [self.parts[:1],self.parts+[self.parts[0]],list(reversed(self.parts)),[self.parts[0],self.parts[0]]]:
            with self.subTest(count=len(parts)),self.assertRaises(ValueError): check_set(self.manifest,parts)
        bad=copy.deepcopy(self.manifest); bad['total_entries']-=1
        with self.assertRaises(Exception): check_set(bad,self.parts)  # signed root cannot be altered

    def test_owner_signed_but_invalid_structure_and_path_collisions(self):
        for entries in [[make_entry('data/a.json',b'x'),make_entry('data/A.json',b'y')],
                        [make_entry('../escape',b'x')], [make_entry('data/NUL',b'x')]]:
            manifest,parts=make_set(entries)
            with self.assertRaises(ValueError): check_set(manifest,parts)
        m,parts=make_set([make_entry('data/a.json',b'x')]); m['parts'][0]['part_number']=1
        m['signature']=sign(AUTHOR,'export-set',{k:v for k,v in m.items() if k!='signature'})
        with self.assertRaises(ValueError): check_set(m,parts)

    def test_prepared_wrapping_preserves_source_bytes(self):
        record=prepared_record(); source={'kind':'prepared_admission','object':record}
        source_entry=make_entry('data/prepared.json',canonical(source),'service_evidence')
        wrapped,v=wrap_prepared(record); local_entry=make_entry('data/prepared.json',canonical(wrapped),'service_evidence')
        self.assertEqual(check_transformation(source_entry,local_entry,wrapped,v),'unpublished')
        bad=copy.deepcopy(source_entry); bad['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'source bytes'): check_transformation(bad,local_entry,wrapped,v)
        bad=copy.deepcopy(local_entry); bad['path']='data/other.json'
        with self.assertRaisesRegex(ValueError,'path/category'): check_transformation(source_entry,bad,wrapped,v)

    def test_adaptive_long_paths_and_part_size_limit(self):
        segment='p'*220
        entries=[make_entry('data/'+segment+'/'+segment+'/'+segment+'/'+segment+'/x%05d.json'%i,b'x') for i in range(5000)]
        manifest,parts=make_set(entries)
        self.assertGreater(len(parts),1)
        self.assertTrue(all(len(x)<=4194304 for x in parts))
        self.assertEqual(len(check_set(manifest,parts)),len(entries))
        self.assertGreater(len(self.parts[0]),1048576)  # valid larger private part assembled in bounded chunks
        over={'profile':'ForYouExportPart-1','snapshot_id':SNAPSHOT,'author_id':OWNER,'created_at':CREATED,
              'part_number':0,'entries':entries}
        raw=canonical(over); self.assertGreater(len(raw),4194304)
        descriptor={'part_number':0,'byte_length':len(raw),'sha256':sha(raw),'entry_count':len(entries)}
        m={'profile':'ForYouExportSet-1','snapshot_id':SNAPSHOT,'author_id':OWNER,'created_at':CREATED,
           'total_entries':len(entries),'total_bytes':len(entries),'coverage':'complete','parts':[descriptor],
           'source_index_sha256':None}
        m['signature']=sign(AUTHOR,'export-set',m)
        with self.assertRaises(Exception): check_set(m,[raw])

    def test_cross_part_file_directory_collision(self):
        entries=self.entries[:9999]+[make_entry('data/shared',b'x'),make_entry('data/shared/child',b'x')]
        m,parts=make_set(entries); self.assertEqual(len(parts),2)
        with self.assertRaisesRegex(ValueError,'ancestor'): check_set(m,parts)

    def test_prepared_requires_expected_owner_id_and_canonical_source(self):
        record=prepared_record(); source={'kind':'prepared_admission','object':record}
        wrapped,v=wrap_prepared(record); source_entry=make_entry('data/prepared.json',canonical(source),'service_evidence')
        local=make_entry(source_entry['path'],canonical(wrapped),'service_evidence')
        pretty=json.dumps(source,indent=2).encode()
        with self.assertRaisesRegex(ValueError,'source bytes'): check_transformation(make_entry(source_entry['path'],pretty,'service_evidence'),local,wrapped,v)
        wrong=copy.deepcopy(wrapped); obj=wrong['object']; obj['author_id']=did(PROVIDER)
        obj['message_id']=mid({k:x for k,x in obj.items() if k not in ['message_id','signature']})
        obj['signature']=sign(PROVIDER,'message',{k:x for k,x in obj.items() if k!='signature'})
        with self.assertRaisesRegex(ValueError,'wrong owner'): check_transformation(source_entry,make_entry(source_entry['path'],canonical(wrong),'service_evidence'),wrong,v)
        wrong=copy.deepcopy(wrapped); obj=wrong['object']; obj['message_id']='fy1:'+'0'*64
        obj['signature']=sign(AUTHOR,'message',{k:x for k,x in obj.items() if k!='signature'})
        with self.assertRaisesRegex(ValueError,'archive id mismatch'): check_transformation(source_entry,make_entry(source_entry['path'],canonical(wrong),'service_evidence'),wrong,v)

    def test_provider_source_and_owner_transformed_set_bindings(self):
        record=prepared_record(); source_obj={'kind':'prepared_admission','object':record}
        path='data/prepared.json'; source_entry=make_entry(path,canonical(source_obj),'service_evidence')
        source_parts,source_descriptors=build_parts([source_entry])
        index={'profile':'ForYouExportSet-1','snapshot_id':SNAPSHOT,'author_id':OWNER,'created_at':CREATED,
               'total_entries':1,'total_bytes':source_entry['byte_length'],'coverage':'complete','parts':source_descriptors}
        index_bytes=canonical(index); wrapped,v=wrap_prepared(record)
        local_entry=make_entry(path,canonical(wrapped),'service_evidence')
        manifest,local_parts=make_set([local_entry],source_index_sha256=sha(index_bytes))
        source,local=check_source_metadata(manifest,local_parts,index_bytes,source_parts)
        self.assertEqual(check_transformation(source[(path,'service_evidence')],local[(path,'service_evidence')],wrapped,v),'unpublished')
        with self.assertRaisesRegex(ValueError,'part count'): check_source_metadata(manifest,local_parts,index_bytes,[])
        with self.assertRaisesRegex(ValueError,'source index hash'): check_source_metadata(manifest,local_parts,index_bytes+b' ',source_parts)
        changed=copy.deepcopy(index); changed['coverage']='unknown'; changed_bytes=canonical(changed)
        manifest,local_parts=make_set([local_entry],source_index_sha256=sha(changed_bytes))
        with self.assertRaisesRegex(ValueError,'source/local identity'): check_source_metadata(manifest,local_parts,changed_bytes,source_parts)
        renamed=make_entry('data/other.json',canonical(wrapped),'service_evidence')
        manifest,local_parts=make_set([renamed],source_index_sha256=sha(index_bytes))
        with self.assertRaisesRegex(ValueError,'source/local members'): check_source_metadata(manifest,local_parts,index_bytes,source_parts)

    def test_signed_archive_encryption_field_mutations_fail(self):
        record=prepared_record(); source={'kind':'prepared_admission','object':record}
        wrapped,v=wrap_prepared(record); source_entry=make_entry('data/prepared.json',canonical(source),'service_evidence')
        for field in ['nonce','ciphertext','wrap_nonce','wrapped_key','epk','recipient_pubkey','kid']:
            altered=copy.deepcopy(wrapped); obj=altered['object']; encrypted=obj['payload']['encrypted_state']
            parent=encrypted if field in ['nonce','ciphertext'] else encrypted['recipients'][0]
            raw=bytearray(un64(parent[field])); raw[0]^=1; parent[field]=b64(bytes(raw))
            obj['message_id']=mid({k:x for k,x in obj.items() if k not in ['message_id','signature']})
            obj['signature']=sign(AUTHOR,'message',{k:x for k,x in obj.items() if k!='signature'})
            entry=make_entry(source_entry['path'],canonical(altered),'service_evidence')
            with self.subTest(field=field),self.assertRaises(Exception): check_transformation(source_entry,entry,altered,v)

    def test_coverage_and_term_escaping(self):
        for status in ['complete','incomplete','unknown']:
            m,parts=make_set([]); m['coverage']=status
            m['signature']=sign(AUTHOR,'export-set',{k:v for k,v in m.items() if k!='signature'})
            self.assertEqual(check_set(m,parts),[])
            self.assertEqual(m['coverage']=='complete',status=='complete')
        terms='\x01'*(500000)
        self.assertLessEqual(len(terms.encode()),1048576)
        self.assertGreater(len(canonical({'kind':'terms','object':terms})),2097152)
        # Such terms must be rejected before invoice/sale; no unsafe truncation.

    def test_chunk_zero_before_eof_is_rejected(self):
        def accept(offset,total,blob,declared):
            if declared!=len(blob) or offset<0 or offset>total: raise ValueError('chunk bounds')
            if offset<total and not 1<=len(blob)<=min(262144,total-offset): raise ValueError('no progress')
            if offset==total and blob: raise ValueError('past EOF')
            return offset+len(blob)
        with self.assertRaisesRegex(ValueError,'no progress'): accept(0,5,b'',0)
        with self.assertRaisesRegex(ValueError,'chunk bounds'): accept(0,5,b'123',4)
        self.assertEqual(accept(0,5,b'123',3),3)
        self.assertEqual(accept(5,5,b'',0),5)

    def test_chunk_resume_owner_scope_and_invalidation(self):
        source=b'x'*300000; job=ExportTransport(source)
        first=job.chunk(OWNER,0); second=job.chunk(OWNER,len(first))
        self.assertEqual(first+second,source); self.assertEqual(job.chunk(OWNER,len(source)),b'')
        with self.assertRaisesRegex(ValueError,'not_found'): job.chunk(did(PROVIDER),0)
        with self.assertRaisesRegex(ValueError,'range'): job.chunk(OWNER,len(source)+1)
        job.restrict()
        with self.assertRaisesRegex(ValueError,'export_invalidated'): job.chunk(OWNER,len(first))
        job.restore()
        with self.assertRaisesRegex(ValueError,'export_invalidated'): job.chunk(OWNER,0)

    def test_service_evidence_wrapper_categories_and_types(self):
        for kind in ['fee_schedule','fee_quote','receipt','prepared_admission','provider_evidence','deposit_invoice','deposit_credit','balance_status']:
            structural('ServiceEvidence',{'kind':kind,'object':{}})
        structural('ServiceEvidence',{'kind':'terms','object':'Exact terms'})
        for bad in [{'kind':'terms','object':{}},{'kind':'fee_quote','object':'string'},
                    {'kind':'private_notes','object':{}},{'kind':'receipt','object':{},'extra':True}]:
            with self.subTest(bad=bad),self.assertRaises(jsonschema.ValidationError): structural('ServiceEvidence',bad)

if __name__=='__main__': unittest.main()
