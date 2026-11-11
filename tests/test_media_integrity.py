"""Synthetic media-integrity reference cases; no HTTP client or media decoder.

The buffering model exercises the intended trust boundary, not production
streaming, resource controls, transport decoding, or image/video safety.
"""
import copy
import hashlib
import json
import socket
import unittest
from pathlib import Path
from unittest.mock import patch

import jsonschema

from test_security_profile import I, mid

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'schemas/launch.schema.json').read_text(encoding='utf-8'))
SLOT = jsonschema.Draft202012Validator(dict(SCHEMA, **{'$ref': '#/$defs/MediaReference'}))
IMAGE = b'synthetic-original-image-bytes'
VIDEO = b'synthetic-complete-video-bytes'


def slot(data, kind='image', url='https://media.example/item'):
    return {'id': 'item', 'url': url, 'kind': kind, 'sha256': hashlib.sha256(data).hexdigest()}


class BufferedDisplay:
    """Display nothing until the entire supplied object matches its signed hash."""
    def __init__(self, expected_hash):
        self.expected_hash = expected_hash
        self.buffer = bytearray()
        self.displayed = []

    def feed(self, data):
        self.buffer.extend(data)

    def finish(self):
        raw = bytes(self.buffer)
        if hashlib.sha256(raw).hexdigest() != self.expected_hash:
            self.buffer.clear()
            return False
        self.displayed.append(raw)
        return True


class MediaIntegrityTests(unittest.TestCase):
    def test_slot_requires_canonical_sha256_and_no_dimension_metadata(self):
        good = slot(IMAGE)
        self.assertTrue(SLOT.is_valid(good))
        for bad_hash in (None, '', 'a' * 63, 'a' * 65, 'A' * 64, 'g' * 64):
            bad = copy.deepcopy(good)
            if bad_hash is None:
                del bad['sha256']
            else:
                bad['sha256'] = bad_hash
            self.assertFalse(SLOT.is_valid(bad), repr(bad_hash))
        for forbidden in ('width', 'height', 'max_bytes'):
            bad = dict(good, **{forbidden: 1})
            self.assertFalse(SLOT.is_valid(bad), forbidden)

    def test_mutable_url_or_transformed_bytes_never_pass_old_hash(self):
        expected = slot(IMAGE)
        for wrong in (IMAGE + b'!', IMAGE[:-1], IMAGE.upper(), b'other image'):
            with self.subTest(data=wrong):
                renderer = BufferedDisplay(expected['sha256'])
                renderer.feed(wrong)
                self.assertFalse(renderer.finish())
                self.assertEqual(renderer.displayed, [])
        renderer = BufferedDisplay(expected['sha256'])
        renderer.feed(IMAGE)
        self.assertTrue(renderer.finish())
        self.assertEqual(renderer.displayed, [IMAGE])

    def test_video_is_not_rendered_until_full_object_verifies(self):
        expected = slot(VIDEO, 'video')
        self.assertTrue(SLOT.is_valid(expected))
        renderer = BufferedDisplay(expected['sha256'])
        renderer.feed(VIDEO[:8])
        self.assertEqual(renderer.displayed, [])
        renderer.feed(VIDEO[8:])
        self.assertEqual(renderer.displayed, [])
        self.assertTrue(renderer.finish())
        self.assertEqual(renderer.displayed, [VIDEO])
        incomplete = BufferedDisplay(expected['sha256'])
        incomplete.feed(VIDEO[:8])
        self.assertFalse(incomplete.finish())
        self.assertEqual(incomplete.displayed, [])

    def test_digest_is_part_of_signed_intent_and_schema_check_does_not_fetch(self):
        first = copy.deepcopy(I)
        first['payload']['media_slots'] = [slot(IMAGE)]
        changed = copy.deepcopy(first)
        changed['payload']['media_slots'][0]['sha256'] = hashlib.sha256(b'changed').hexdigest()
        with patch.object(socket, 'create_connection', side_effect=AssertionError('unexpected network')):
            self.assertTrue(SLOT.is_valid(first['payload']['media_slots'][0]))
            self.assertNotEqual(mid(first), mid(changed))




class MediaFetchPolicyTests(unittest.TestCase):
    """Fixture model of the fetch rules: a signed URL may be syntactically valid and still never be fetched."""

    @staticmethod
    def may_fetch(address):
        import ipaddress
        ip = ipaddress.ip_address(address)
        if ip.version == 6 and ip.ipv4_mapped is not None:
            ip = ip.ipv4_mapped
        return ip.is_global and not ip.is_multicast

    @staticmethod
    def accept_download(declared_size, received_lengths, limit=10 ** 7):
        """Abort once the declared size (or the client's own limit) is exceeded; reject a final length mismatch."""
        total = 0
        for n in received_lengths:
            total += n
            if total > (declared_size if declared_size is not None else limit):
                return 'aborted'
        if declared_size is not None and total != declared_size:
            return 'rejected'
        return 'verify-digest'

    def test_private_and_loopback_destinations_are_never_fetched(self):
        for address in ('127.0.0.1', '10.0.0.5', '192.168.1.1', '172.16.0.1', '169.254.1.1', '0.0.0.0', '224.0.0.1',
                        '::1', 'fe80::1', 'fc00::1', '::ffff:127.0.0.1', '::ffff:10.0.0.1', '100.64.0.1'):
            with self.subTest(address=address):
                self.assertFalse(self.may_fetch(address))
        for address in ('93.184.216.34', '2606:2800:220:1:248:1893:25c8:1946'):
            self.assertTrue(self.may_fetch(address))

    def test_declared_size_bounds_the_download(self):
        self.assertEqual(self.accept_download(1000, [400, 600]), 'verify-digest')
        self.assertEqual(self.accept_download(1000, [400, 601]), 'aborted')
        self.assertEqual(self.accept_download(1000, [400, 500]), 'rejected')
        self.assertEqual(self.accept_download(None, [400, 500]), 'verify-digest')
        self.assertEqual(self.accept_download(None, [10 ** 7, 1]), 'aborted')

    def test_text_and_schema_state_the_rules(self):
        from test_security_profile import ROOT
        text = (ROOT / 'docs/02-protocol.md').read_text(encoding='utf-8')
        for phrase in ('never fetched', 'SVG and any other format that can carry scripts', 'with no extensions', 'no percent escape'):
            self.assertIn(phrase, text)


if __name__ == '__main__':
    unittest.main()
