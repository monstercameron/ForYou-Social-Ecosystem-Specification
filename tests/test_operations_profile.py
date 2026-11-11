"""Structural and extraction checks for current service schemas."""
import json
from pathlib import PurePosixPath
import unittest
import jsonschema
from test_security_profile import ROOT, PROVIDER, AUTHOR, did, sign, verify

OPS = json.loads((ROOT/'schemas/operations.schema.json').read_text(encoding='utf-8'))
WIRE = json.loads((ROOT/'schemas/launch.schema.json').read_text(encoding='utf-8'))

def structural(kind, value):
    jsonschema.Draft202012Validator(dict(OPS, **{'$ref':'#/$defs/'+kind}),
                                   format_checker=jsonschema.FormatChecker()).validate(value)

def safe_paths(entries):
    seen=set()
    for x in entries:
        path=x['path']; parts=path.split('/')
        if not path or '\\' in path or ':' in path or any(v in ('','.', '..') for v in parts):
            raise ValueError('unsafe path')
        if any(v.endswith(('.', ' ')) or v.split('.')[0].upper() in
               {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]} for v in parts):
            raise ValueError('platform alias')
        key=str(PurePosixPath(path)).casefold()
        if key in seen: raise ValueError('duplicate path')
        seen.add(key)
    for key in seen:
        parts=key.split('/')
        if any('/'.join(parts[:i]) in seen for i in range(1,len(parts))):
            raise ValueError('file/directory ancestor collision')

class OperationsTests(unittest.TestCase):
    def test_schema(self):
        jsonschema.Draft202012Validator.check_schema(OPS)
        jsonschema.Draft202012Validator.check_schema(WIRE)

    def test_provider_specific_evidence_is_private_and_signed(self):
        evidence={'provider_id':did(PROVIDER),'author_id':did(AUTHOR),
                  'evidence_type':'service-record','payload':'example provider record'}
        evidence['provider_signature']=sign(PROVIDER,'provider-service-evidence',evidence)
        structural('ProviderServiceEvidence',evidence)
        structural('ServiceEvidence',{'kind':'provider_evidence','object':evidence})
        altered=dict(evidence,payload='different record')
        with self.assertRaises(Exception):
            verify(did(PROVIDER),'provider-service-evidence',
                   {k:v for k,v in altered.items() if k!='provider_signature'},altered['provider_signature'])

    def test_export_paths(self):
        safe_paths([{'path':'messages/a.json'}])
        for path in ['../secret','/absolute','a//b','a/./b','C:/secret','a\\b','NUL','a.','a:stream']:
            with self.subTest(path=path),self.assertRaises(ValueError): safe_paths([{'path':path}])
        with self.assertRaises(ValueError): safe_paths([{'path':'a.json'},{'path':'A.JSON'}])

    def test_core_export_has_no_preferences_requirement(self):
        x={'profile':'ForYouExportSet-1','snapshot_id':'a'*43,'author_id':did(AUTHOR),
           'created_at':'2026-11-11T00:00:00Z','total_entries':0,'total_bytes':0,'coverage':'complete','parts':[],'source_index_sha256':None,'signature':'a'*86}
        structural('ExportSetManifest',x)
        entry={'path':'data/private/preferences.json','media_type':'application/json','byte_length':100,'sha256':'a'*64,'category':'local_preferences'}
        with self.assertRaises(jsonschema.ValidationError): structural('ExportEntry',entry)

if __name__=='__main__': unittest.main()
