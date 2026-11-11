"""Adversarial boundary/keyset examples against a reference model, not a live provider."""
import copy
from datetime import timedelta
import unittest
from urllib.parse import quote,urlencode
from test_security_profile import M,AUTHOR,PROVIDER,did,b64
from retrieval_model import Failure,Provider,normalize,matches,order,encoded,stamp,validate_page


def query(**values): return urlencode(values,quote_via=quote,safe='-._~')


def record(n,at='2026-11-10T12:00:00Z',author=None):
    # Synthetic metadata ordering cases. Existing crypto suite separately checks proofs.
    value=copy.deepcopy(M); value['message_id']='fy1:'+format(n,'064x'); value['timestamp']=at
    value['author_id']=author or did(AUTHOR)
    return value


def collect(provider,raw,**options):
    pages=[]; token=None
    for _ in range(100):
        page=provider.page('/v1/messages',raw+('&' if raw else '')+query(cursor=token) if token else raw,**options)
        pages.append(page)
        token=page['next_cursor']
        if token is None: return pages
    raise AssertionError('nontermination')


class RetrievalTests(unittest.TestCase):
    def test_optional_replies_filter_and_cursor_bind_parent(self):
        parent='fy1:'+'a'*64; other='fy1:'+'b'*64
        child=record(1); child['payload']['reply_to']=parent
        child2=record(2); child2['payload']['reply_to']=parent
        unrelated=record(3); unrelated['payload']['reply_to']=other
        p=Provider([child,child2,unrelated])
        route='/v1/replies/fy1%3A'+'a'*64
        first=p.page(route,'limit=1')
        self.assertEqual(first['messages'][0]['message_id'],child['message_id'])
        with self.assertRaises(Failure): p.page('/v1/replies/fy1%3A'+'b'*64,query(limit=1,cursor=first['next_cursor']))
        with self.assertRaises(Failure): p.page('/v1/messages',query(limit=1,cursor=first['next_cursor']))
        for invalid in ('/v1/replies/'+parent,'/v1/replies/fy1%3a'+'a'*64):
            with self.assertRaises(Failure): p.page(invalid,'limit=1')
        second=p.page(route,query(limit=1,cursor=first['next_cursor']))
        self.assertEqual(second['messages'][0]['message_id'],child2['message_id'])
        self.assertIsNone(second['next_cursor'])

    def test_removed_quota_mode_is_rejected(self):
        with self.assertRaises(Failure): normalize('/v1/messages','quota_mode=skip')

    def test_single_date_and_explicit_range_are_equivalent(self):
        day,_=normalize('/v1/messages','date=2024-02-29')
        explicit,_=normalize('/v1/messages',query(**{'from':'2024-02-29T00:00:00Z','until':'2024-03-01T00:00:00Z','limit':50}))
        self.assertEqual(day,explicit)
        for at,expected in [('2024-02-28T23:59:59Z',False),('2024-02-29T00:00:00Z',True),('2024-02-29T23:59:59Z',True),('2024-03-01T00:00:00Z',False)]:
            self.assertEqual(matches(day,record(1,at)),expected)
        self.assertIsNone(normalize('/v1/messages','')[0]['from'])
        last,_=normalize('/v1/messages',query(**{'from':'9999-12-31T00:00:00Z'}))
        self.assertTrue(matches(last,record(1,'9999-12-31T23:59:59Z')))

    def test_invalid_calendar_intervals_and_http_aliases(self):
        bad=['date=2026-02-29','date=2024-02-30','date=0000-01-01','date=9999-12-31',
             'date=2026-11-10&from=2026-11-10T00%3A00%3A00Z','limit=01','limit=101','limit=0',
             'date=2026-11-10&date=2026-11-11','%64ate=2026-11-10','date=','date=2026-11-10&',
             'from=2026-11-10T00:00:00Z','cursor=%FF','date=2026%2d11%2d10','limit=+1',
             'date=2026%252D11%252D10','timezone=UTC']
        for value in ['2026-11-10','2026-11-10T00:00:00+00:00','2026-11-10T00:00:00.1Z','2026-11-10T23:59:60Z']:
            bad.append(query(**{'from':value}))
        for lower,upper in [('2026-11-11T00:00:00Z','2026-11-10T00:00:00Z'),('2026-11-10T00:00:00Z','2026-11-10T00:00:00Z')]:
            bad.append(query(**{'from':lower,'until':upper}))
        for raw in bad:
            with self.subTest(raw=raw),self.assertRaises(Failure): normalize('/v1/messages',raw)
        with self.assertRaises(Failure): normalize('/v1/messages','a'*16385)

    def test_explicit_utc_bounds_can_cover_non_24_hour_days(self):
        for lower,upper,hours in [('2024-03-10T05:00:00Z','2024-03-11T04:00:00Z',23),('2024-11-03T04:00:00Z','2024-11-04T05:00:00Z',25)]:
            q,_=normalize('/v1/messages',query(**{'from':lower,'until':upper}))
            self.assertEqual(stamp(q['until'])-stamp(q['from']),timedelta(hours=hours))

    def test_author_and_range_intersection(self):
        provider=Provider([record(1),record(2,author=did(PROVIDER)),record(3,'2026-11-11T00:00:00Z')])
        page=provider.page('/v1/author-messages',query(author_id=did(AUTHOR),date='2026-11-10'))
        self.assertEqual([m['message_id'] for m in page['messages']],[record(1)['message_id']])
        for endpoint,raw in [('/v1/messages',query(author_id=did(AUTHOR))),('/v1/author-messages','')]:
            with self.assertRaises(Failure): normalize(endpoint,raw)

    def test_equal_timestamps_and_duplicates_have_no_gaps(self):
        records=[record(i) for i in range(35,0,-1)]
        provider=Provider(records+[copy.deepcopy(records[3])])
        pages=collect(provider,query(date='2026-11-10',limit=3))
        ids=[m['message_id'] for p in pages for m in p['messages']]
        self.assertEqual(ids,[record(i)['message_id'] for i in range(1,36)])
        self.assertEqual(len(ids),len(set(ids)))

    def test_cursor_binds_filters_route_provider_and_limit(self):
        p=Provider([record(1),record(2),record(3)])
        first=p.page('/v1/messages','date=2026-11-10&limit=1'); token=first['next_cursor']
        good=query(**{'from':'2026-11-10T00:00:00Z','until':'2026-11-11T00:00:00Z','limit':1,'cursor':token})
        self.assertEqual(p.page('/v1/messages',good)['messages'][0]['message_id'],record(2)['message_id'])
        for endpoint,raw in [('/v1/messages',query(date='2026-11-11',limit=1,cursor=token)),('/v1/messages',query(date='2026-11-10',limit=2,cursor=token)),('/v1/messages',query(limit=1,cursor=token)),('/v1/author-messages',query(author_id=did(AUTHOR),date='2026-11-10',limit=1,cursor=token)),('/v1/messages',query(date='2026-11-10',limit=1,cursor=token[:-1]+('A' if token[-1]!='A' else 'Q')))]:
            with self.subTest(raw=raw),self.assertRaises(Failure): p.page(endpoint,raw)
        with self.assertRaises(Failure): Provider(p.records).page('/v1/messages',good)
        with self.assertRaises(Failure): normalize('/v1/messages',query(cursor='A'*42+'B'))

    def test_late_arrival_is_seen_only_after_restart(self):
        p=Provider([record(2),record(4)])
        first=p.page('/v1/messages','date=2026-11-10&limit=1')
        p.records.extend([record(1),record(3),record(5)])
        second=p.page('/v1/messages',query(date='2026-11-10',limit=1,cursor=first['next_cursor']))
        self.assertEqual([m['message_id'] for m in second['messages']],[record(4)['message_id']])
        self.assertIsNone(second['next_cursor'])
        refreshed=collect(p,'date=2026-11-10&limit=2')
        self.assertEqual([m['message_id'] for x in refreshed for m in x['messages']],[record(i)['message_id'] for i in range(1,6)])

    def test_empty_progress_suppression_and_restoration(self):
        p=Provider([record(i) for i in range(1,5)])
        first=p.page('/v1/messages','limit=1'); token=first['next_cursor']
        p.restrict(record(2)['message_id']); p.restrict(record(3)['message_id'])
        empty=p.page('/v1/messages',query(limit=1,cursor=token),scan_budget=1)
        self.assertEqual(empty['messages'],[]); self.assertIsNotNone(empty['next_cursor'])
        self.assertNotEqual(token,empty['next_cursor'])
        p.restore(record(2)['message_id'])
        replay=p.page('/v1/messages',query(limit=1,cursor=token),scan_budget=1)
        self.assertEqual(replay['messages'],[])  # already suppressed from this snapshot
        tail=p.page('/v1/messages',query(limit=1,cursor=empty['next_cursor']))
        self.assertEqual([m['message_id'] for m in tail['messages']],[record(4)['message_id']])
        self.assertIsNone(tail['next_cursor'])
        with self.assertRaises(Failure): p.page('/v1/messages','limit=1',scan_budget=0)

    def test_restriction_and_restore_before_first_scan(self):
        p=Provider([record(1),record(2),record(3)])
        first=p.page('/v1/messages','limit=1')
        p.restrict(record(2)['message_id']); p.restore(record(2)['message_id'])
        second=p.page('/v1/messages',query(limit=1,cursor=first['next_cursor']))
        self.assertEqual(second['messages'][0]['message_id'],record(3)['message_id'])
        self.assertEqual([r['message_id'] for r in p.page('/v1/messages','')['messages']],[record(i)['message_id'] for i in range(1,4)])

    def test_cursor_error_precedence(self):
        for value in ['', 'short','A'*42+'B','A'*43+'=', '!'*43]:
            with self.subTest(value=value),self.assertRaises(Failure) as caught: normalize('/v1/messages',query(cursor=value))
            self.assertEqual(caught.exception.code,'invalid_cursor')
        for raw in ['cursor=%FF','cursor=a&cursor=b','date=2026-02-30&cursor=short']:
            with self.subTest(raw=raw),self.assertRaises(Failure) as caught: normalize('/v1/messages',raw)
            self.assertEqual(caught.exception.code,'invalid_query')

    def test_quota_replay_and_fixed_expiry(self):
        p=Provider([record(1),record(2),record(3)]); first=p.page('/v1/messages','limit=1')
        raw=query(limit=1,cursor=first['next_cursor']); before=p.served_bytes
        second=p.page('/v1/messages',raw); again=p.page('/v1/messages',raw)
        self.assertEqual(second,again); self.assertEqual(p.served_bytes-before,2*len(encoded(second)))
        p.remaining_bytes=1
        with self.assertRaisesRegex(Failure,'quota'): p.page('/v1/messages',raw)
        p.remaining_bytes=10**6
        self.assertEqual(p.page('/v1/messages',raw),second)
        with self.assertRaisesRegex(Failure,'invalid_cursor'): p.page('/v1/messages',raw,now=first['expires_at'])

    def test_byte_deferred_maximum_messages_are_not_skipped(self):
        rows=[record(1),record(2),record(3)]
        for row in rows:
            row['payload']['text']=''
            row['payload']['text']='x'*(1048576-len(encoded(row)))
            self.assertEqual(len(encoded(row)),1048576)
        pages=collect(Provider(rows),'limit=100')
        self.assertEqual([len(x['messages']) for x in pages],[1,1,1])
        self.assertEqual([x['messages'][0]['message_id'] for x in pages],[r['message_id'] for r in rows])
        self.assertTrue(all(len(encoded(x))<=2097152 for x in pages))

    def test_client_rejects_page_invariant_changes(self):
        p=Provider([record(1),record(2)]); raw='date=2026-11-10&limit=1'; first=p.page('/v1/messages',raw)
        q,_=normalize('/v1/messages',raw); times=validate_page(first,q)
        second=p.page('/v1/messages',raw+'&'+query(cursor=first['next_cursor']))
        validate_page(second,q,times)
        with self.assertRaises(Failure): validate_page(second,q,times,now=second['expires_at'])
        with self.assertRaises(Failure): validate_page(second,q,times,now='2026-11-10T23:58:00Z')
        for field,value in [('generated_at','2026-11-11T00:00:01Z'),('expires_at','2026-11-11T00:14:00Z'),('expires_at','2026-11-11T01:01:00Z'),('messages',[record(1),record(2)])]:
            bad=copy.deepcopy(second); bad[field]=value
            with self.subTest(field=field),self.assertRaises(Failure): validate_page(bad,q,times)
        bad=copy.deepcopy(second); bad['messages'][0]['timestamp']='2026-11-11T00:00:00Z'
        with self.assertRaises(Failure): validate_page(bad,q,times)

    def test_restrictions_on_signed_references_hide_whole_record(self):
        parent=record(1); reply=record(2); reply['payload']['reply_to']=parent['message_id']
        p=Provider([parent,reply]); p.restrict(parent['message_id'])
        self.assertEqual(p.page('/v1/messages','')['messages'],[reply])  # public reference may still contain the known ID
        p.restrict(reply['message_id'])  # restriction covers reference itself
        self.assertEqual(p.page('/v1/messages','')['messages'],[])
        self.assertEqual(reply['payload']['reply_to'],parent['message_id'])  # never edit signed bytes

if __name__=='__main__': unittest.main()
