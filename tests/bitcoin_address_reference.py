"""Bounded Bitcoin address/script checks for test fixtures, not a wallet implementation."""
import hashlib

B58='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
BECH='qpzry9x8gf2tvdw0s3jn54khce6mua7l'
GEN=(0x3b6a57b2,0x26508e6d,0x1ea119fa,0x3d4233dd,0x2a1462b3)


def bitcoin_script(address):
    if not isinstance(address,str) or not 1<=len(address)<=128 or not address.isascii(): raise ValueError('address')
    if address.lower().startswith('bc1'):
        if address!=address.lower() or len(address)>90: raise ValueError('canonical segwit case/length')
        data=address[3:]
        if len(data)<7 or any(c not in BECH for c in data): raise ValueError('segwit alphabet')
        values=[BECH.index(c) for c in data]
        checksum=1
        for number in [ord('b')>>5,ord('c')>>5,0,ord('b')&31,ord('c')&31]+values:
            top=checksum>>25; checksum=((checksum&0x1ffffff)<<5)^number
            for i,g in enumerate(GEN):
                if (top>>i)&1: checksum^=g
        version=values[0]
        if version not in (0,1) or checksum!=(1 if version==0 else 0x2bc830a3): raise ValueError('witness version/checksum')
        acc=0; bits=0; program=bytearray()
        for number in values[1:-6]:
            acc=(acc<<5)|number; bits+=5
            while bits>=8:
                bits-=8; program.append((acc>>bits)&255)
        if bits>=5 or (acc<<(8-bits))&255: raise ValueError('noncanonical padding')
        if len(program) not in ((20,32) if version==0 else (32,)): raise ValueError('program length')
        return bytes([0 if version==0 else 0x51,len(program)])+bytes(program)
    n=0
    for c in address:
        if c not in B58: raise ValueError('base58 character')
        n=n*58+B58.index(c)
    value=n.to_bytes((n.bit_length()+7)//8,'big') if n else b''
    raw=b'\x00'*(len(address)-len(address.lstrip('1')))+value
    if len(raw)!=25 or raw[0] not in (0,5): raise ValueError('base58 length/network')
    if hashlib.sha256(hashlib.sha256(raw[:-4]).digest()).digest()[:4]!=raw[-4:]: raise ValueError('base58 checksum')
    return (b'\x76\xa9\x14'+raw[1:21]+b'\x88\xac') if raw[0]==0 else (b'\xa9\x14'+raw[1:21]+b'\x87')
