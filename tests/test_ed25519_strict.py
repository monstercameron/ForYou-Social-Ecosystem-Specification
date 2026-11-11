"""Independent arithmetic checks for the ForYou strict Ed25519 profile.

Synthetic deterministic values only. This deliberately slow, non-constant-time
reference is for tests, never key handling or production verification. The
existing Node/OpenSSL check covers a valid fixture; it is not claimed to enforce
this profile's subgroup checks or the adversarial cases below.
"""
import base64
import hashlib
import json
import unittest
from pathlib import Path

from nacl.signing import SigningKey
import rfc8785


def un64(value):
    raw = base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))
    if base64.urlsafe_b64encode(raw).decode().rstrip('=') != value:
        raise ValueError('noncanonical base64url')
    return raw

P = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493
D = (-121665 * pow(121666, -1, P)) % P
SQRT_M1 = pow(2, (P - 1) // 4, P)
IDENTITY = (0, 1, 1, 0)


def decode(data):
    if len(data) != 32:
        raise ValueError('point length')
    value = int.from_bytes(data, 'little')
    sign = value >> 255
    y = value & ((1 << 255) - 1)
    if y >= P:
        raise ValueError('noncanonical y')
    y2 = y * y % P
    x2 = (y2 - 1) * pow(D * y2 + 1, -1, P) % P
    x = pow(x2, (P + 3) // 8, P)
    if x * x % P != x2:
        x = x * SQRT_M1 % P
    if x * x % P != x2 or (x == 0 and sign):
        raise ValueError('point recovery')
    if (x & 1) != sign:
        x = P - x
    return x, y, 1, x * y % P


def add(a, b):
    x1, y1, z1, t1 = a
    x2, y2, z2, t2 = b
    aa = (y1 - x1) * (y2 - x2) % P
    bb = (y1 + x1) * (y2 + x2) % P
    cc = 2 * D * t1 * t2 % P
    dd = 2 * z1 * z2 % P
    e, f, g, h = (bb-aa) % P, (dd-cc) % P, (dd+cc) % P, (bb+aa) % P
    return e*f % P, g*h % P, f*g % P, e*h % P


def multiply(n, point):
    result = IDENTITY
    while n:
        if n & 1:
            result = add(result, point)
        point = add(point, point)
        n >>= 1
    return result


def encode(point):
    x, y, z, _ = point
    zi = pow(z, -1, P)
    x, y = x * zi % P, y * zi % P
    return (y | ((x & 1) << 255)).to_bytes(32, 'little')


IDENTITY_BYTES = bytes([1]) + bytes(31)
BASE = decode(bytes.fromhex('58' + '66' * 31))
ORDER_TWO = decode((P - 1).to_bytes(32, 'little'))


def strict_point(data):
    point = decode(data)
    if encode(point) != data or encode(point) == IDENTITY_BYTES or encode(multiply(L, point)) != IDENTITY_BYTES:
        raise ValueError('not non-identity prime-subgroup point')
    return point


def strict_verify(public_key, message, signature):
    if len(signature) != 64:
        raise ValueError('signature length')
    r_bytes, s_bytes = signature[:32], signature[32:]
    a, r = strict_point(public_key), strict_point(r_bytes)
    s = int.from_bytes(s_bytes, 'little')
    if s >= L:
        raise ValueError('noncanonical S')
    k = int.from_bytes(hashlib.sha512(r_bytes + public_key + message).digest(), 'little') % L
    if encode(multiply(s, BASE)) != encode(add(r, multiply(k, a))):
        raise ValueError('verification equation')


class StrictEd25519Tests(unittest.TestCase):
    def test_published_cross_language_strict_vectors(self):
        vectors = json.loads((Path(__file__).parent / 'strict-ed25519-vectors.json').read_text(encoding='utf-8'))
        for case in vectors['cases']:
            with self.subTest(case=case['name']):
                try:
                    strict_verify(bytes.fromhex(case['public_key_hex']), bytes.fromhex(case['message_hex']),
                                  bytes.fromhex(case['signature_hex']))
                    accepted = True
                except ValueError:
                    accepted = False
                self.assertEqual(accepted, case['valid'])

    def test_published_transport_and_receipt_fixture(self):
        fixture = json.loads((Path(__file__).parent / 'security-vectors.json').read_text(encoding='utf-8'))
        message = fixture['message']
        receipt = message['submission_receipt']
        for label, obj, key, field in [
            ('message', message, fixture['author_public_key'], 'signature'),
            ('receipt', receipt, fixture['provider_public_key'], 'provider_signature'),
        ]:
            signed = {k: v for k, v in obj.items() if k != field}
            msg = ('ForYou/1/' + label + '\n').encode() + rfc8785.dumps(signed)
            strict_verify(un64(key), msg, un64(obj[field]))

    def test_standard_signature_and_message_tamper(self):
        key = SigningKey(bytes(range(32)))
        message = b'ForYou/1/message\n{"synthetic":true}'
        sig = key.sign(message).signature
        strict_verify(bytes(key.verify_key), message, sig)
        with self.assertRaises(ValueError):
            strict_verify(bytes(key.verify_key), message + b'!', sig)

    def test_noncanonical_s_and_length(self):
        key = SigningKey(bytes(range(32)))
        sig = key.sign(b'm').signature
        s = int.from_bytes(sig[32:], 'little')
        with self.assertRaises(ValueError):
            strict_verify(bytes(key.verify_key), b'm', sig[:32] + (s + L).to_bytes(32, 'little'))
        with self.assertRaises(ValueError):
            strict_verify(bytes(key.verify_key), b'm', sig[:-1])

    def test_noncanonical_y_and_zero_x_sign(self):
        for malformed in [P.to_bytes(32, 'little'), (1 | (1 << 255)).to_bytes(32, 'little')]:
            with self.subTest(point=malformed.hex()), self.assertRaises(ValueError):
                strict_point(malformed)

    def test_identity_and_order_two_are_rejected_for_both_a_and_r(self):
        key = SigningKey(bytes(range(32)))
        sig = key.sign(b'm').signature
        for bad in [IDENTITY_BYTES, encode(ORDER_TWO)]:
            for public, signature in [(bad, sig), (bytes(key.verify_key), bad + sig[32:])]:
                with self.subTest(point=bad.hex(), public=public.hex()), self.assertRaises(ValueError):
                    strict_verify(public, b'm', signature)

    def test_mixed_order_points_are_not_prime_subgroup(self):
        mixed = encode(add(BASE, ORDER_TWO))
        self.assertNotEqual(encode(multiply(L, decode(mixed))), IDENTITY_BYTES)
        key = SigningKey(bytes(range(32)))
        sig = key.sign(b'm').signature
        for public, signature in [(mixed, sig), (bytes(key.verify_key), mixed + sig[32:])]:
            with self.subTest(public=public.hex()), self.assertRaises(ValueError):
                strict_verify(public, b'm', signature)

    def test_existing_protocol_helpers_enforce_subgroup(self):
        # Import lazily: the helper imports this module for arithmetic.
        from test_security_profile import B58, AUTHOR, b64, did, pub, sign, verify
        mixed = encode(add(BASE, ORDER_TWO))
        n = int.from_bytes(b'\xed\x01' + mixed, 'big')
        encoded = ''
        while n:
            n, digit = divmod(n, 58)
            encoded = B58[digit] + encoded
        with self.assertRaises(ValueError):
            pub('did:key:z' + encoded)
        proof = un64(sign(AUTHOR, 'message', {'test': True}))
        with self.assertRaises(ValueError):
            verify(did(AUTHOR), 'message', {'test': True}, b64(mixed + proof[32:]))

    def test_cofactored_equation_alone_accepts_mixed_order_key(self):
        # Construct A = B + order-two torsion and R = [r]B with secret scalar 1.
        # Cofactor 8 eliminates the torsion. This is not an acceptable ForYou key.
        a = add(BASE, ORDER_TWO)
        a_bytes = encode(a)
        r = 7
        r_bytes = encode(multiply(r, BASE))
        message = b'ForYou mixed-order regression'
        k = int.from_bytes(hashlib.sha512(r_bytes + a_bytes + message).digest(), 'little') % L
        s = (r + k) % L
        lhs = multiply(8, multiply(s, BASE))
        rhs = multiply(8, add(decode(r_bytes), multiply(k, a)))
        self.assertEqual(encode(lhs), encode(rhs))
        with self.assertRaises(ValueError):
            strict_verify(a_bytes, message, r_bytes + s.to_bytes(32, 'little'))


if __name__ == '__main__':
    unittest.main()
