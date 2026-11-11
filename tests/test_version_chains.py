"""Signed version-graph examples; a local reference, not a network implementation."""
import copy
import hashlib
import unittest

import jsonschema
from nacl.signing import SigningKey
from test_security_profile import I, M, R, SCHEMA, AUTHOR, PROVIDER, did, intent, mid, sign, verify, b64
from version_fixtures import request, verify_admission

OTHER=SigningKey(bytes(range(96,128)))


def make_post(text, author=AUTHOR, parent=None, reply=None, at='2026-11-11T00:00:00Z', issued=None):
    i=copy.deepcopy(I); i['author_id']=did(author); i['timestamp']=at; i['payload']['text']=text
    if parent is not None: i['payload']['supersedes']=parent
    if reply is not None: i['payload']['reply_to']=reply
    ident=mid(i)
    receipt={k:v for k,v in R.items() if k!='provider_signature'}
    receipt.update(author_id=did(author),message_id=ident,receipt_id=b64(hashlib.sha256(ident.encode()).digest()))
    if issued is not None: receipt.update(authorization_at=issued,issued_at=issued)
    receipt['provider_signature']=sign(PROVIDER,'receipt',receipt)
    message=dict(i,message_id=ident,submission_receipt=receipt)
    message['signature']=sign(author,'message',message)
    return message


def verified(m):
    jsonschema.Draft202012Validator(SCHEMA,format_checker=jsonschema.FormatChecker()).validate(m)
    if mid(intent(m))!=m['message_id']: raise ValueError('id mismatch')
    r=m['submission_receipt']
    if r['provider_id']!=did(PROVIDER) or r['author_id']!=m['author_id'] or r['message_id']!=m['message_id']:
        raise ValueError('receipt binding')
    verify(r['provider_id'],'receipt',{k:v for k,v in r.items() if k!='provider_signature'},r['provider_signature'])
    verify(m['author_id'],'message',{k:v for k,v in m.items() if k!='signature'},m['signature'])


def edge_status(update, parent):
    verified(update)
    target=update['payload'].get('supersedes')
    if target is None: return 'original'
    if target==update['message_id']: return 'invalid'
    if parent is None: return 'unresolved'
    try: verified(parent)
    except (ValueError, jsonschema.ValidationError): return 'unresolved'
    if parent['message_id']!=target: return 'unresolved'
    if parent['author_id']!=update['author_id']: return 'invalid'
    if parent['payload'].get('reply_to')!=update['payload'].get('reply_to'): return 'invalid'
    return 'valid'


def resolve(root, records, max_nodes=100):
    """Pick among known verified leaves only; no claim of global completeness."""
    verified(root)
    if len(records)>max_nodes: raise ValueError('work limit')
    known={root['message_id']:root}
    children={}
    for m in records:
        verified(m)
        if m['message_id'] in known:
            if intent(m)!=intent(known[m['message_id']]): raise ValueError('collision')
            continue  # Different valid receipts for the same signed intent are not a fork.
        known[m['message_id']]=m
    for m in known.values():
        target=m['payload'].get('supersedes')
        if target and target in known and edge_status(m,known[target])=='valid':
            children.setdefault(target,[]).append(m['message_id'])
    stack=[root['message_id']]; seen=set(); leaves=[]
    while stack:
        current=stack.pop()
        if current in seen: raise ValueError('cycle')
        seen.add(current)
        if len(seen)>max_nodes: raise ValueError('work limit')
        next_ids=children.get(current,[])
        if next_ids: stack.extend(next_ids)
        else: leaves.append(known[current])
    return select_leaf(leaves)


def select_leaf(leaves):
    """Root-signed first, then greatest receipt issued_at, then ASCII-smallest ID."""
    root_signed=[m for m in leaves if m.get('signer_id',m['author_id'])==m['author_id'] and 'delegation' not in m]
    pool=root_signed or leaves
    latest=max(m['submission_receipt']['issued_at'] for m in pool)
    return min((m for m in pool if m['submission_receipt']['issued_at']==latest),key=lambda m:m['message_id'])


class AdmissionModel:
    def __init__(self): self.receipts={}; self.debits=0
    def submit(self, req, target=None):
        verify_admission(req); i=req['intent']; ident=mid(i)
        if ident in self.receipts: return self.receipts[ident]
        if i['payload'].get('supersedes')==ident: raise ValueError('self-reference')
        if target is not None:
            try: verified(target); trustworthy=True
            except (ValueError, jsonschema.ValidationError): trustworthy=False
            if trustworthy and target['message_id']==i['payload'].get('supersedes'):
                if target['author_id']!=i['author_id'] or target['payload'].get('reply_to')!=i['payload'].get('reply_to'):
                    raise ValueError('invalid update edge')
        self.debits+=1; self.receipts[ident]='receipt-'+ident
        return self.receipts[ident]


class VersionChainTests(unittest.TestCase):
    def test_post_only_schema_and_signed_supersedes(self):
        root=make_post('first'); update=make_post('edit',parent=root['message_id'])
        verified(root); verified(update)
        self.assertEqual(edge_status(update,root),'valid')
        altered=copy.deepcopy(update); altered['payload']['supersedes']='fy1:'+'a'*64
        with self.assertRaises(ValueError): verified(altered)
        bad=copy.deepcopy(root); bad['message_type']='withdraw'
        with self.assertRaises(jsonschema.ValidationError): verified(bad)
        bad=copy.deepcopy(update); bad['payload']['supersedes']='https://example.org'
        with self.assertRaises(jsonschema.ValidationError): verified(bad)

    def test_unknown_and_cross_author_target_never_merge(self):
        other=make_post('other',author=OTHER)
        update=make_post('unresolved',parent=other['message_id'])
        self.assertEqual(edge_status(update,None),'unresolved')
        self.assertEqual(edge_status(update,other),'invalid')
        self.assertEqual(resolve(other,[update])['message_id'],other['message_id'])
        model=AdmissionModel(); req=request(other['message_id'])
        with self.assertRaises(ValueError): model.submit(req,other)
        self.assertEqual(model.debits,0)
        first=model.submit(req,None)
        self.assertEqual(model.submit(req,other),first)  # already committed: no retroactive debit/erasure
        self.assertEqual(model.debits,1)

    def test_unverified_target_cannot_poison_update_attribution(self):
        root=make_post('root'); update=make_post('edit',parent=root['message_id'])
        tampered=copy.deepcopy(root); tampered['author_id']=did(OTHER)
        self.assertEqual(edge_status(update,tampered),'unresolved')
        model=AdmissionModel(); model.submit(request(root['message_id']),tampered)
        self.assertEqual(model.debits,1)

    def test_reply_target_cannot_change_across_update(self):
        parent=make_post('comment',reply=M['message_id'])
        valid=make_post('edited comment',parent=parent['message_id'],reply=M['message_id'])
        bad=make_post('moved comment',parent=parent['message_id'])
        self.assertEqual(edge_status(valid,parent),'valid')
        self.assertEqual(edge_status(bad,parent),'invalid')
        req=request(parent['message_id'])  # request does not preserve the parent's reply_to
        model=AdmissionModel()
        with self.assertRaises(ValueError): model.submit(req,parent)
        self.assertEqual(model.debits,0)

    def test_fork_prefers_root_signed_then_latest_receipt_then_smallest_id(self):
        root=make_post('root')
        early=make_post('early',parent=root['message_id'],issued='2026-11-11T00:01:00Z')
        late=make_post('late',parent=root['message_id'],issued='2026-11-11T00:02:00Z')
        self.assertEqual(resolve(root,[early,late])['message_id'],late['message_id'])
        self.assertEqual(resolve(root,[late,early])['message_id'],late['message_id'])
        # The author-supplied timestamp does not decide; the provider-signed receipt time does.
        backdated=make_post('backdated',parent=root['message_id'],at='2026-11-10T00:00:00Z',issued='2026-11-11T00:03:00Z')
        self.assertEqual(resolve(root,[early,late,backdated])['message_id'],backdated['message_id'])
        # A delegate-signed leaf never beats a root-signed leaf, however late or however small its ID.
        delegated=copy.deepcopy(late); delegated['signer_id']=did(OTHER); delegated['delegation']={'synthetic':True}
        delegated['submission_receipt']=dict(delegated['submission_receipt'],issued_at='2026-11-11T09:00:00Z')
        self.assertIs(select_leaf([early,delegated]),early)
        self.assertIs(select_leaf([delegated]),delegated)
        # Grinding a small message ID cannot beat a later receipt.
        ground=min((make_post(f'grind-{n}',parent=root['message_id'],issued='2026-11-11T00:01:00Z') for n in range(20)),key=lambda m:m['message_id'])
        self.assertEqual(resolve(root,[ground,late])['message_id'],late['message_id'])

    def test_fork_tie_uses_ascii_smallest_id_not_author_timestamp(self):
        root=make_post('root')
        a=make_post('a',parent=root['message_id'],at='2026-11-11T00:00:02Z')
        b=make_post('b',parent=root['message_id'],at='2026-11-11T00:00:02Z')
        self.assertEqual(resolve(root,[b,a])['message_id'],min(a['message_id'],b['message_id']))
        child=make_post('child',parent=a['message_id'],at='2026-11-11T00:00:03Z')
        self.assertEqual(resolve(root,[b,a,child])['message_id'],min(b['message_id'],child['message_id']))
        # Give the smaller ID an earlier timestamp and the larger ID a later one.
        variants=[make_post(f'candidate-{n}',parent=root['message_id'],at=('2026-11-11T00:00:01Z' if n % 2 else '2026-11-11T00:00:59Z')) for n in range(20)]
        earlier=[m for m in variants if m['timestamp'].endswith('01Z')]
        later=[m for m in variants if m['timestamp'].endswith('59Z')]
        old=min(earlier,key=lambda m:m['message_id']); new=max(later,key=lambda m:m['message_id'])
        self.assertLess(old['message_id'],new['message_id'])
        self.assertEqual(resolve(root,[new,old])['message_id'],old['message_id'])
        self.assertEqual(resolve(root,[b])['message_id'],b['message_id'])  # local view only
        with self.assertRaises(ValueError): resolve(root,[a,b,child],max_nodes=2)

    def test_update_is_post_scope_and_one_debit_per_distinct_intent(self):
        root=make_post('root'); a=request(root['message_id'],delegated=True)
        verify_admission(a); self.assertEqual(a['intent']['delegation']['scope'],['post'])
        model=AdmissionModel(); first=model.submit(a,root)
        self.assertEqual(model.submit(a,root),first); self.assertEqual(model.debits,1)
        b=request(root['message_id']); self.assertNotEqual(model.submit(b,root),first)
        self.assertEqual(model.debits,2)


if __name__=='__main__': unittest.main()
