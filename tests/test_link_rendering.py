"""Link-policy examples, not a CommonMark parser or networking implementation.

This deliberately limited scanner recognizes only the simple inline-link,
angle-autolink, code-span and fenced-code fixtures below. It cannot establish
correct handling of the full CommonMark grammar, nested syntax or browsers.
"""
import re
import unittest
from urllib.parse import urlsplit

from test_external_media import media_url
from test_security_profile import AUTHOR, did, pub


MESSAGE_ID = re.compile(r'fy1:[0-9a-f]{64}\Z')
REF_ID = re.compile(r'[a-z0-9_-]{1,32}\Z')
INLINE = re.compile(r'(?<![!\\])\[([^\]\n]+)\]\(([^\s()]+)\)')
AUTOLINK = re.compile(r'(?<!\\)<(https://[^<>\s]+)>')
LOOKS_LIKE_URL = re.compile(r'(?i)^(?:https?://|www\.|[a-z0-9-]+(?:\.[a-z0-9-]+)+(?::\d+)?(?:/|$))')


def valid_target(target):
    if not isinstance(target, str):
        return False
    if MESSAGE_ID.fullmatch(target):
        return True
    if not target.startswith('did:key:'):
        return False
    try:
        pub(target)
        return True
    except (ValueError, OverflowError):
        return False


def signed_references(entries):
    """Validate this fixture's closed id/target array before rendering."""
    if len(entries) > 32:
        raise ValueError('reference limit')
    result, targets = {}, set()
    for entry in entries:
        if set(entry) != {'id', 'target'} or not isinstance(entry['id'], str):
            raise ValueError('reference fields')
        ident, target = entry['id'], entry['target']
        if not REF_ID.fullmatch(ident) or ident in result or not valid_target(target) or target in targets:
            raise ValueError('invalid or duplicate reference')
        result[ident] = target
        targets.add(target)
    return result


def classify(label, destination, refs=None):
    """Classify a single already-parsed node; never perform network I/O."""
    if destination.startswith('fy-ref:'):
        ident = destination[7:]
        target = (refs or {}).get(ident) if REF_ID.fullmatch(ident) else None
        if target is None:
            return {'kind': 'text'}
        # The author-supplied label is never presented as verified identity.
        return {'kind': 'internal', 'target': target, 'display_target': target,
                'label_is_verified': False}
    try:
        media_url(destination)
    except (ValueError, UnicodeError):
        return {'kind': 'text'}
    # The full checked destination is always shown at the click confirmation. A URL-like label
    # differing from the actual exact destination is additionally flagged as a mismatch.
    host = urlsplit(destination).hostname
    return {'kind': 'external', 'target': destination, 'host': host, 'show_target': True,
            'label_mismatch': bool(LOOKS_LIKE_URL.match(label) and label != destination),
            'confirm': True, 'noopener': True, 'referrer': None}


def simple_nodes(markdown, refs=None):
    """Fixture scanner only: ignore bare links, images, code and escaped nodes."""
    nodes = []
    fenced = False
    for line in markdown.splitlines():
        if re.match(r'^\s{0,3}```', line):
            fenced = not fenced
            continue
        if fenced:
            continue
        # Preserve offsets while hiding simple backtick code spans.
        text = re.sub(r'`[^`\n]*`', lambda m: ' ' * len(m.group()), line)
        spans = []
        for match in INLINE.finditer(text):
            spans.append(match.span())
            nodes.append(classify(match.group(1), match.group(2), refs))
        for match in AUTOLINK.finditer(text):
            if not any(a <= match.start() < b for a, b in spans):
                nodes.append(classify(match.group(1), match.group(1)))
    return nodes


IMAGE = re.compile(r'(?<!\\)!\[([^\]\n]*)\]\(([^\s()]+)\)')
SLOT_ID = re.compile(r'[a-z0-9_-]{1,32}\Z')


def media_plan(markdown, slot_ids):
    """Fixture scanner: which declared slots are placed inline, as placeholders, or trail the text."""
    inline, placeholders, remote = [], [], []
    fenced = False
    for line in markdown.splitlines():
        if re.match(r'^\s{0,3}```', line):
            fenced = not fenced
            continue
        if fenced:
            continue
        text = re.sub(r'`[^`\n]*`', lambda m: ' ' * len(m.group()), line)
        for match in IMAGE.finditer(text):
            destination = match.group(2)
            if not destination.startswith('fy-media:'):
                remote.append(destination)  # inert: never fetched
            elif SLOT_ID.fullmatch(destination[9:]) and destination[9:] in slot_ids:
                if destination[9:] not in inline:
                    inline.append(destination[9:])
            else:
                placeholders.append(destination[9:])
    trailing = [s for s in slot_ids if s not in inline]
    return {'inline': inline, 'placeholders': placeholders, 'trailing': trailing, 'fetch': [], 'inert_remote': remote}


def render_literal(text):
    """Raw HTML is shown as text: escape it, never emit it as markup."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def resolve_internal(node, approved_providers, query, activated=False):
    """Ask only an approved provider; query returns independently verified data.

    This illustrates dispatch and requires the caller to provide verification;
    it performs no network activity, discovery, fetch or DNS lookup itself.
    """
    if node.get('kind') != 'internal':
        raise ValueError('not internal')
    if not activated:
        return None
    for provider in approved_providers:
        result = query(provider, node['target'])
        if result is not None and result.get('verified') and result.get('id') == node['target']:
            return result
    return None


class LinkPolicyTests(unittest.TestCase):
    def test_unsafe_schemes_and_malformed_urls_remain_text(self):
        for target in ('http://example.com/x', 'javascript:alert', 'data:text/html,x',
                       'file:///etc/passwd', 'blob:https://example.com/x', 'mailto:a@example.com',
                       'https://user@example.com/x', 'https://example.com/\\x',
                       'https://example.com/%0a', 'https://example.com/' + 'a' * 4096):
            with self.subTest(target=target[:80]):
                self.assertEqual(classify('click', target), {'kind': 'text'})

    def test_homograph_and_visible_url_spoofing(self):
        self.assertEqual(classify('link', 'https://bücher.example/'), {'kind': 'text'})
        puny = classify('https://example.com/', 'https://xn--bcher-kva.example/')
        self.assertEqual(puny['host'], 'xn--bcher-kva.example')
        self.assertTrue(puny['show_target'])
        self.assertTrue(puny['confirm'])
        self.assertTrue(puny['noopener'])
        self.assertIsNone(puny['referrer'])

    def test_links_are_explicit_and_code_is_inert(self):
        text = ('https://bare.example/\n[x](https://good.example/path)\n'
                '<https://auto.example/>\n`[x](https://code.example/)`\n'
                '\\[x](https://escaped.example/)\n![x](https://image.example/)\n'
                '[x](https://title.example/ "title")\n```\n[x](https://fenced.example/)\n```')
        nodes = simple_nodes(text)
        self.assertEqual([n['host'] for n in nodes], ['good.example', 'auto.example'])

    def test_internal_links_use_only_approved_provider_and_verify_id(self):
        target = 'fy1:' + 'a' * 64
        refs = signed_references([{'id':'p1','target':target}, {'id':'alice','target':did(AUTHOR)}])
        node = classify('post', 'fy-ref:p1', refs)
        self.assertEqual(node['target'], target)
        self.assertEqual(node['display_target'], target)
        self.assertFalse(node['label_is_verified'])
        author = classify('@alice', 'fy-ref:alice', refs)
        self.assertEqual(author['display_target'], did(AUTHOR))
        self.assertFalse(author['label_is_verified'])
        self.assertEqual(classify('old', 'fy:' + target, refs), {'kind': 'text'})
        self.assertEqual(classify('missing', 'fy-ref:missing', refs), {'kind': 'text'})
        self.assertEqual(classify('suffix', 'fy-ref:p1?x=1', refs), {'kind': 'text'})
        self.assertEqual(classify('media', 'fy-media:one'), {'kind': 'text'})
        called = []
        def query(provider, wanted):
            called.append(provider)
            return {'id': wanted, 'verified': provider == 'approved-b'}
        self.assertIsNone(resolve_internal(node, ['approved-a', 'approved-b'], query))
        self.assertEqual(called, [])
        result = resolve_internal(node, ['approved-a', 'approved-b'], query, activated=True)
        self.assertEqual(called, ['approved-a', 'approved-b'])
        self.assertEqual(result['id'], target)
        self.assertIsNone(resolve_internal(node, [], query, activated=True))
        self.assertIsNone(resolve_internal(node, ['approved-a'], lambda p, t: {'id': 'wrong', 'verified': True}, activated=True))

    def test_signed_reference_ids_and_targets_are_unique_and_closed(self):
        target = 'fy1:' + 'b' * 64
        invalid = [
            [{'id':'p','target':target}, {'id':'p','target':did(AUTHOR)}],
            [{'id':'p','target':target}, {'id':'q','target':target}],
            [{'id':'UPPER','target':target}],
            [{'id':'p','target':'https://unapproved.example'}],
            [{'id':'p','target':target,'url':'https://unapproved.example'}],
        ]
        for entries in invalid:
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                signed_references(entries)

    def test_raw_html_is_literal_and_creates_no_links_or_media(self):
        cases = ['<script>alert(1)</script>', '<a href="https://evil.example/">x</a>',
                 '<img src="https://evil.example/p.png" onerror="x()">', '<iframe src="https://evil.example/"></iframe>',
                 '<a href="javascript:alert(1)">x</a>', '<svg onload="x()"></svg>', '<img src="fy-media:a">']
        for html in cases:
            with self.subTest(html=html):
                self.assertEqual(simple_nodes(html), [])
                plan = media_plan(html, ['a'])
                self.assertEqual((plan['inline'], plan['fetch']), ([], []))
                shown = render_literal(html)
                self.assertNotIn('<', shown)
                self.assertNotIn('>', shown)

    def test_media_slots_bind_only_through_fy_media_images(self):
        slots = ['cover', 'clip', 'extra']
        text = ('![c](fy-media:cover) ![again](fy-media:cover)\n![m](fy-media:missing)\n'
                '![r](https://remote.example/a.png)\n`![code](fy-media:clip)`\n```\n![f](fy-media:clip)\n```\n'
                '[link](fy-media:clip) \\![esc](fy-media:extra) ![bad](fy-media:Cover)')
        plan = media_plan(text, slots)
        self.assertEqual(plan['inline'], ['cover'])
        self.assertEqual(plan['placeholders'], ['missing', 'Cover'])
        self.assertEqual(set(plan['trailing']), {'clip', 'extra'})  # still declared and eligible; arrangement is a local choice
        self.assertEqual(plan['inert_remote'], ['https://remote.example/a.png'])
        self.assertEqual(plan['fetch'], [])  # rendering never fetches; consent comes first
        self.assertEqual(set(media_plan('no images', slots)['trailing']), set(slots))
        # Only a title-free inline image binds a slot: titled, reference-style and escaped forms do not.
        for inert in ('![c](fy-media:cover "title")', '![c][r]\n\n[r]: fy-media:cover', '![c](fy-media:cover?x=1)', '![c](fy-media:cover#f)', '![c](fy-media:%63over)', '<fy-media:cover>'):
            with self.subTest(inert=inert):
                self.assertEqual(media_plan(inert, slots)['inline'], [])

    def test_published_refs_example_verifies(self):
        import json
        from test_fee_slots import check_quote
        from test_security_profile import ROOT, validate
        x = json.loads((ROOT / 'examples/post-with-refs.json').read_text(encoding='utf-8'))
        message = x['message']
        validate(message)
        check_quote(x['schedule'], x['quote'], message)
        refs = signed_references(message['payload']['refs'])
        nodes = simple_nodes(message['payload']['text'], refs)
        internal = [n for n in nodes if n['kind'] == 'internal']
        self.assertEqual({n['target'] for n in internal}, set(refs.values()))
        self.assertTrue(any(n['kind'] == 'text' for n in nodes))  # the undeclared reference stays inert

    def test_reference_must_be_title_free_inline_link(self):
        refs = signed_references([{'id':'p1','target':'fy1:' + 'c' * 64}])
        text = ('fy-ref:p1\n`[p](fy-ref:p1)`\n\\[p](fy-ref:p1)\n'
                '![p](fy-ref:p1)\n[p](fy-ref:p1 "title")\n[p](fy-ref:p1)')
        nodes = simple_nodes(text, refs)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]['target'], refs['p1'])


if __name__ == '__main__':
    unittest.main()
