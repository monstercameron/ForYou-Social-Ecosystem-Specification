// Slow, non-constant-time public-data conformance reference; never use for secret keys.
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

const p = (1n << 255n) - 19n;
const l = (1n << 252n) + 27742317777372353535851937790883648493n;
const mod = x => ((x % p) + p) % p;
function power(x, n) { let r = 1n; x = mod(x); while (n) { if (n & 1n) r = mod(r*x); x = mod(x*x); n >>= 1n; } return r; }
const inv = x => { if (mod(x) === 0n) throw Error('inverse'); return power(x, p-2n); };
const d = mod(-121665n * inv(121666n)), rootM1 = power(2n, (p-1n)/4n);
const ident = [0n,1n,1n,0n];
function little(bytes) { let n = 0n; for (let i=bytes.length-1;i>=0;i--) n=(n<<8n)+BigInt(bytes[i]); return n; }
function bytesLE(n, length) { const out=Buffer.alloc(length); for (let i=0;i<length;i++) { out[i]=Number(n&255n); n>>=8n; } if (n) throw Error('overflow'); return out; }
function decode(bytes) {
  if (bytes.length!==32) throw Error('length');
  const n=little(bytes), sign=n>>255n, y=n&((1n<<255n)-1n);
  if (y>=p) throw Error('noncanonical y');
  const yy=mod(y*y), xx=mod((yy-1n)*inv(d*yy+1n));
  let x=power(xx,(p+3n)/8n);
  if (mod(x*x)!==xx) x=mod(x*rootM1);
  if (mod(x*x)!==xx || (x===0n && sign===1n)) throw Error('recovery');
  if ((x&1n)!==sign) x=p-x;
  return [x,y,1n,mod(x*y)];
}
function add(a,b) {
  const [x1,y1,z1,t1]=a,[x2,y2,z2,t2]=b;
  const aa=mod((y1-x1)*(y2-x2)), bb=mod((y1+x1)*(y2+x2));
  const cc=mod(2n*d*t1*t2), dd=mod(2n*z1*z2);
  const e=mod(bb-aa), f=mod(dd-cc), g=mod(dd+cc), h=mod(bb+aa);
  return [mod(e*f),mod(g*h),mod(f*g),mod(e*h)];
}
function mul(n,q) { let r=ident; while(n) { if(n&1n) r=add(r,q); q=add(q,q); n>>=1n; } return r; }
function encode(q) { const [x,y,z]=q, zi=inv(z), xx=mod(x*zi), yy=mod(y*zi); return bytesLE(yy|((xx&1n)<<255n),32); }
const identity=Buffer.concat([Buffer.from([1]),Buffer.alloc(31)]);
const base=decode(Buffer.from('58'+'66'.repeat(31),'hex'));
function point(b) { const q=decode(b); if(!encode(q).equals(b)||b.equals(identity)||!encode(mul(l,q)).equals(identity)) throw Error('subgroup'); return q; }
function verify(aBytes,m,sig) {
  if(aBytes.length!==32||sig.length!==64) throw Error('length');
  const rb=sig.subarray(0,32), a=point(aBytes), r=point(rb), s=little(sig.subarray(32));
  if(s>=l) throw Error('scalar');
  const k=little(createHash('sha512').update(rb).update(aBytes).update(m).digest())%l;
  if(!encode(mul(s,base)).equals(encode(add(r,mul(k,a))))) throw Error('equation');
}
const vectors=JSON.parse(readFileSync(new URL('./strict-ed25519-vectors.json',import.meta.url),'utf8'));
for(const test of vectors.cases) {
  let accepted=true;
  try { verify(Buffer.from(test.public_key_hex,'hex'),Buffer.from(test.message_hex,'hex'),Buffer.from(test.signature_hex,'hex')); }
  catch { accepted=false; }
  if(accepted!==test.valid) throw Error(`Unexpected result: ${test.name}`);
}
console.log(`Strict Ed25519 JavaScript reference passed ${vectors.cases.length} vectors`);
