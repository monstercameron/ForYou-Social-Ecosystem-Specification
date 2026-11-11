"""Keep the consolidated documentation and schema dependency graph coherent."""
import json
import re
import unittest
from pathlib import Path
import jsonschema
from test_security_profile import ROOT, I, M

class ConsolidationTests(unittest.TestCase):
    def test_one_document_set(self):
        expected={'README.md','01-overview.md','02-protocol.md','03-economics.md',
                  '04-compliance.md','05-portability.md','06-governance.md','07-clients.md'}
        self.assertEqual({p.name for p in (ROOT/'docs').glob('*.md')},expected)
        stale=r'(?i)\b(?:document|profile)\s*(?:1[0-9]|2[0-9]|30)\b|23-launch-security|28-governance-and-pilot'
        for f in (ROOT/'docs').glob('*.md'):
            self.assertIsNone(re.search(stale,f.read_text(encoding='utf-8')),str(f))

    def test_internal_document_links(self):
        for f in [ROOT/'README.md',*(ROOT/'docs').glob('*.md'),*(ROOT/'reviews').glob('*.md'),ROOT/'tests/README.md']:
            for link in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
                if link.startswith(('http:','https:')): continue
                target,_,anchor=link.partition('#')
                destination=(f.parent/target).resolve() if target else f
                self.assertTrue(destination.is_file(),(str(f),link))
                if anchor and destination.suffix=='.md':
                    headings=re.findall(r'^#+ (.+)$',destination.read_text(encoding='utf-8'),re.M)
                    slugs={re.sub(r'[^\w\- ]','',h.lower()).replace(' ','-') for h in headings}
                    self.assertIn(anchor,slugs,(str(f),link))

    def test_schema_references_and_removed_contracts(self):
        for path in (ROOT/'schemas').glob('*.json'):
            schema=json.loads(path.read_text())
            jsonschema.Draft202012Validator.check_schema(schema)
            def walk(value):
                if isinstance(value,dict):
                    for k,v in value.items():
                        if k=='$ref' and v.startswith('#/'):
                            node=schema
                            for part in v[2:].split('/'): node=node[part]
                        walk(v)
                elif isinstance(value,list):
                    for v in value: walk(v)
            walk(schema)
        launch=json.loads((ROOT/'schemas/launch.schema.json').read_text())
        for name in ['Payment','SubmissionToken','PollMessage','AdvertisementMessage','ProviderPlanSchedule','WorkClaimReport']:
            self.assertNotIn(name,launch['$defs'])
        self.assertIn('MessageAcceptance',launch['$defs'])

    def test_inline_candidate_ranking_shape(self):
        schema=json.loads((ROOT/'schemas/launch.schema.json').read_text())
        schema['$ref']='#/$defs/CandidateContent'
        candidate={'candidate_id':M['message_id'],'author_id':I['author_id'],
                   'timestamp':I['timestamp'],'content_type':'post','is_ad':False}
        jsonschema.Draft202012Validator(schema).validate(candidate)

if __name__=='__main__': unittest.main()
