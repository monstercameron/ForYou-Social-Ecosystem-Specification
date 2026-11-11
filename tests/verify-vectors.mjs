// Independent Node/OpenSSL Ed25519 and ID verification for the published vector.
// JCS here covers this fixture's data types, not a general-purpose JCS library.
import fs from 'node:fs';
import {createPublicKey, verify, createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const v = JSON.parse(fs.readFileSync(new URL('./security-vectors.json', import.meta.url)));
function jcs(x) {
  if (Array.isArray(x)) return '['+x.map(jcs).join(',')+']';
  if (x && typeof x === 'object') return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+jcs(x[k])).join(',')+'}';
  return JSON.stringify(x);
}
const pre=(label,x)=>Buffer.from('ForYou/1/'+label+'\n'+jcs(x));
const omit=(x,keys)=>Object.fromEntries(Object.entries(x).filter(([k])=>!keys.includes(k)));
const key=s=>createPublicKey({key:Buffer.concat([Buffer.from('302a300506032b6570032100','hex'),Buffer.from(s,'base64url')]),format:'der',type:'spki'});
const m=v.message, r=m.submission_receipt;
const i=omit(m,['message_id','signature','submission_receipt']);
assert.equal(pre('intent',i).toString('hex'),v.intent_preimage_hex);
assert.equal('fy1:'+createHash('sha256').update(pre('intent',i)).digest('hex'),m.message_id);
assert(verify(null,pre('message',omit(m,['signature'])),key(v.author_public_key),Buffer.from(m.signature,'base64url')));
assert(verify(null,pre('receipt',omit(r,['provider_signature'])),key(v.provider_public_key),Buffer.from(r.provider_signature,'base64url')));
assert(!verify(null,pre('receipt',omit(m,['signature'])),key(v.author_public_key),Buffer.from(m.signature,'base64url')));
console.log('Independent Node/OpenSSL vector checks passed (ID, JCS fixture, two signatures, wrong domain).');
