"""Bounded retrieval reference model. Not a production HTTP/database service."""
import copy
from datetime import date,datetime,timedelta,timezone
import json
import re
import secrets
from urllib.parse import quote,unquote
import jsonschema
from test_security_profile import SCHEMA,b64,un64,pub


class Failure(ValueError):
    def __init__(self,code): self.code=code; super().__init__(code)


def stamp(value):
    if not isinstance(value,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z',value): raise Failure('invalid_query')
    try: return datetime.fromisoformat(value[:-1]+'+00:00')
    except ValueError as exc: raise Failure('invalid_query') from exc


def iso(dt): return f'{dt.year:04d}-{dt.month:02d}-{dt.day:02d}T{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}Z'


def normalize(endpoint,raw):
    reply_match=re.fullmatch(r'/v1/replies/fy1%3A([0-9a-f]{64})',endpoint)
    if (endpoint not in ['/v1/messages','/v1/author-messages'] and not reply_match) or not raw.isascii() or len(raw)>16384: raise Failure('invalid_query')
    decoded={}
    for component in raw.split('&') if raw else []:
        if '=' not in component: raise Failure('invalid_query')
        key,value=component.split('=',1)
        if key in decoded or key not in ['date','from','until','limit','cursor','author_id']: raise Failure('invalid_query')
        try: plain=unquote(value,encoding='utf-8',errors='strict')
        except UnicodeError as exc: raise Failure('invalid_query') from exc
        if (not plain and key!='cursor') or quote(plain,safe='-._~')!=value: raise Failure('invalid_query')
        decoded[key]=plain
    if 'limit' in decoded:
        if not re.fullmatch(r'[1-9][0-9]{0,2}',decoded['limit']): raise Failure('invalid_query')
        decoded['limit']=int(decoded['limit'])
    token=decoded.pop('cursor',None)
    name='AuthorMessageListQuery' if endpoint=='/v1/author-messages' else 'MessageListQuery'
    try: jsonschema.Draft202012Validator(dict(SCHEMA,**{'$ref':'#/$defs/'+name}),format_checker=jsonschema.FormatChecker()).validate(decoded)
    except jsonschema.ValidationError as exc: raise Failure('invalid_query') from exc
    lower,upper=decoded.get('from'),decoded.get('until')
    if 'date' in decoded:
        try:
            day=date.fromisoformat(decoded['date']); end=day+timedelta(days=1)
        except ValueError as exc: raise Failure('invalid_query') from exc
        except OverflowError as exc: raise Failure('invalid_query') from exc
        lower=day.isoformat()+'T00:00:00Z'; upper=end.isoformat()+'T00:00:00Z'
    if lower: stamp(lower)
    if upper: stamp(upper)
    if lower and upper and lower>=upper: raise Failure('invalid_query')
    if 'author_id' in decoded:
        try: pub(decoded['author_id'])
        except (ValueError,OverflowError) as exc: raise Failure('invalid_query') from exc
    if token is not None:
        try:
            if not re.fullmatch(r'[A-Za-z0-9_-]{43}',token): raise ValueError('shape')
            if len(un64(token))!=32: raise ValueError('length')
        except Exception as exc: raise Failure('invalid_cursor') from exc
    return {'endpoint':endpoint,'from':lower,'until':upper,'author_id':decoded.get('author_id'),'reply_to':'fy1:'+reply_match.group(1) if reply_match else None,'limit':decoded.get('limit',50)},token


def matches(query,record):
    return ((query['from'] is None or record['timestamp']>=query['from']) and
            (query['until'] is None or record['timestamp']<query['until']) and
            (query['author_id'] is None or record['author_id']==query['author_id']) and
            (query['reply_to'] is None or record['payload'].get('reply_to')==query['reply_to']))


def order(record):
    dt=stamp(record['timestamp'])
    seconds=dt.toordinal()*86400+dt.hour*3600+dt.minute*60+dt.second
    return -seconds,record['message_id']


def encoded(value): return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8')


class Provider:
    def __init__(self,records):
        self.records=records; self.handles={}; self.cache={}; self.next_snapshot=0
        self.hidden=set(); self.generation=0; self.last_suppression={}
        self.remaining_bytes=10**9; self.remaining_requests=10**6
        self.served_bytes=0; self.served_requests=0

    def restrict(self,message_id):
        self.generation+=1; self.hidden.add(message_id)
        self.last_suppression[message_id]=self.generation

    def restore(self,message_id):
        self.hidden.discard(message_id)

    def handle(self,snapshot,position):
        key=(snapshot['id'],position)
        if key not in self.cache:
            token=b64(secrets.token_bytes(32))
            while token in self.handles: token=b64(secrets.token_bytes(32))
            self.handles[token]=(snapshot,position); self.cache[key]=token
        return self.cache[key]

    def page(self,endpoint,raw,now='2026-11-11T00:00:00Z',scan_budget=1000,byte_budget=2097152):
        query,token=normalize(endpoint,raw); current=stamp(now)
        if token:
            if token not in self.handles: raise Failure('invalid_cursor')
            snapshot,position=self.handles[token]
            if snapshot['query']!=query or current>=stamp(snapshot['expires_at']): raise Failure('invalid_cursor')
        else:
            snapshot=None; position=None
        if self.remaining_requests<=0 or self.remaining_bytes<=0: raise Failure('quota')
        if snapshot is None:
            # Inputs are assumed finalized and cryptographically validated upstream; model tests use synthetic records.
            records={}
            for record in self.records:
                if record['message_id'] not in self.hidden and matches(query,record): records.setdefault(record['message_id'],copy.deepcopy(record))
            self.next_snapshot+=1
            snapshot={'id':self.next_snapshot,'query':query,'generated_at':now,'expires_at':iso(current+timedelta(minutes=15)),
                      'records':sorted(records.values(),key=order),'suppressed':set(),'generation':self.generation}
        start=position; result=[]; scanned=0
        for record in snapshot['records']:
            key=order(record)
            if position is not None and key<=position: continue
            if scanned>=scan_budget or len(result)>=query['limit']: break
            scanned+=1
            if record['message_id'] in self.hidden or self.last_suppression.get(record['message_id'],0)>snapshot['generation']: snapshot['suppressed'].add(record['message_id'])
            if record['message_id'] in snapshot['suppressed']:
                position=key; continue
            trial={'generated_at':snapshot['generated_at'],'expires_at':snapshot['expires_at'],
                   'messages':result+[record],'next_cursor':'A'*43}
            if len(encoded(trial))>byte_budget:
                if not result: raise Failure('unavailable')
                break  # preserve the candidate for the next page
            result.append(record); position=key
        more=any(position is None or order(r)>position for r in snapshot['records'])
        if more and position==start: raise Failure('work_limit')
        next_cursor=self.handle(snapshot,position) if more else None
        page={'generated_at':snapshot['generated_at'],'expires_at':snapshot['expires_at'],'messages':result,'next_cursor':next_cursor}
        size=len(encoded(page))
        if size>byte_budget: raise Failure('unavailable')
        if size>self.remaining_bytes: raise Failure('quota')
        self.remaining_bytes-=size; self.remaining_requests-=1; self.served_bytes+=size; self.served_requests+=1
        return page


def validate_page(page,query,expected_times=None,now='2026-11-11T00:00:00Z'):
    schema=dict(SCHEMA,**{'$ref':'#/$defs/DiscoveryPage'})
    try: jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).validate(page)
    except jsonschema.ValidationError as exc: raise Failure('invalid_page') from exc
    start,end=stamp(page['generated_at']),stamp(page['expires_at'])
    if not 900<=(end-start).total_seconds()<=3600: raise Failure('invalid_page')
    if stamp(now)>=end or start>stamp(now)+timedelta(seconds=60): raise Failure('invalid_page')
    times=(page['generated_at'],page['expires_at'])
    if expected_times is not None and times!=expected_times: raise Failure('invalid_page')
    records=page['messages']
    if len(records)>query['limit'] or len(encoded(page))>2097152 or any(len(encoded(r))>1048576 for r in records): raise Failure('invalid_page')
    if any(not matches(query,r) for r in records) or records!=sorted(records,key=order): raise Failure('invalid_page')
    if len({r['message_id'] for r in records})!=len(records): raise Failure('invalid_page')
    if page['next_cursor']:
        try:
            if len(un64(page['next_cursor']))!=32: raise ValueError('length')
        except Exception as exc: raise Failure('invalid_page') from exc
    return times
