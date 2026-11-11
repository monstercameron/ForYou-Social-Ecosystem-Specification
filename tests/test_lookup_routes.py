"""Synthetic advisory lookup checks; not an HTTP server or completeness proof."""
import copy
import secrets
import unittest
from urllib.parse import quote

from test_security_profile import AUTHOR, PROVIDER, did, intent, mid, sign
from test_version_chains import make_post, resolve, verified


def post_with_refs(text, entries):
    """Make a signed example, so client checks do not rely on index assertions."""
    post = make_post(text)
    post['payload']['refs'] = copy.deepcopy(entries)
    post['message_id'] = mid(intent(post))
    receipt = post['submission_receipt']
    receipt['message_id'] = post['message_id']
    receipt['provider_signature'] = sign(PROVIDER, 'receipt',
                                          {k: v for k, v in receipt.items() if k != 'provider_signature'})
    post['signature'] = sign(AUTHOR, 'message', {k: v for k, v in post.items() if k != 'signature'})
    verified(post)
    return post


class AdvisoryIndex:
    """Tiny cursor model; records and trust have already been checked upstream."""
    def __init__(self, provider, posts):
        self.provider = provider
        self.posts = copy.deepcopy(posts)
        self.cursors = {}

    def page(self, route, target, date, limit, cursor=None):
        binding = (self.provider, route, target, date, limit)
        if cursor is None:
            snapshot = copy.deepcopy(self.posts)
            position = 0
        else:
            if cursor not in self.cursors:
                raise ValueError('invalid cursor')
            original, snapshot, position = self.cursors[cursor]
            if original != binding:
                raise ValueError('invalid cursor')
        def matches(post):
            if date is not None and not post['timestamp'].startswith(date + 'T'):
                return False
            if route == 'references':
                return any(ref['target'] == target for ref in post['payload'].get('refs', []))
            if route == 'versions':
                return post['payload'].get('supersedes') == target
            raise ValueError('invalid route')
        found = sorted((p for p in snapshot if matches(p)), key=lambda p: p['message_id'])
        page = found[position:position + limit]
        next_pos = position + len(page)
        next_cursor = None
        if next_pos < len(found):
            next_cursor = secrets.token_urlsafe(32)
            self.cursors[next_cursor] = (binding, snapshot, next_pos)
        return page, next_cursor


def validate_reference_response(posts, target):
    for post in posts:
        verified(post)
        if not any(ref['target'] == target for ref in post['payload'].get('refs', [])):
            raise ValueError('index returned a non-matching post')


class AdvisoryLookupTests(unittest.TestCase):
    def test_reference_lookup_matches_exact_did_or_post_not_visible_text(self):
        author = did(AUTHOR)
        target = 'fy1:' + 'a' * 64
        declared = post_with_refs('No visible mention here', [{'id': 'r1', 'target': author}])
        declared_post = post_with_refs('Text is not the target', [{'id': 'r2', 'target': target}])
        lookalike = post_with_refs('Mentions ' + target + ' in ordinary text', [])
        index = AdvisoryIndex('provider-a', [declared, declared_post, lookalike])
        self.assertEqual(index.page('references', author, None, 10)[0], [declared])
        self.assertEqual(index.page('references', target, None, 10)[0], [declared_post])
        self.assertNotIn('fy-ref:r1', declared['payload']['text'])  # Declared is not necessarily visible.
        validate_reference_response([declared], author)
        with self.assertRaises(ValueError):
            validate_reference_response([lookalike], target)

    def test_cursor_binds_provider_route_target_and_filters(self):
        target = 'fy1:' + 'a' * 64
        posts = [post_with_refs(str(i), [{'id': 'r', 'target': target}]) for i in range(2)]
        index = AdvisoryIndex('provider-a', posts)
        _, cursor = index.page('references', target, '2026-11-11', 1)
        self.assertIsNotNone(cursor)
        for route, other_target, date, limit in [
            ('versions', target, '2026-11-11', 1),
            ('references', 'fy1:' + 'b' * 64, '2026-11-11', 1),
            ('references', target, '2026-11-10', 1),
            ('references', target, '2026-11-11', 2),
        ]:
            with self.subTest(route=route, target=other_target, date=date, limit=limit):
                with self.assertRaises(ValueError):
                    index.page(route, other_target, date, limit, cursor)
        with self.assertRaises(ValueError):
            AdvisoryIndex('provider-b', posts).page('references', target, '2026-11-11', 1, cursor)
        self.assertEqual(len(index.page('references', target, '2026-11-11', 1, cursor)[0]), 1)

    def test_version_lookup_is_immediate_successors_not_global_latest(self):
        root = make_post('original')
        first = make_post('first edit', parent=root['message_id'], at='2026-11-11T00:00:01Z')
        later = make_post('second edit', parent=first['message_id'], at='2026-11-11T00:00:02Z')
        index = AdvisoryIndex('provider-a', [root, first, later])
        immediate, cursor = index.page('versions', root['message_id'], None, 10)
        self.assertEqual(immediate, [first])
        self.assertIsNone(cursor)  # Exhaustion of this lookup does not prove there is no later version.
        self.assertEqual(resolve(root, immediate)['message_id'], first['message_id'])
        self.assertEqual(resolve(root, immediate + [later])['message_id'], later['message_id'])

    def test_canonical_path_encodes_colons_without_fetching_targets(self):
        self.assertEqual(quote('fy1:' + 'a' * 64, safe='-._~'), 'fy1%3A' + 'a' * 64)
        self.assertTrue(quote(did(AUTHOR), safe='-._~').startswith('did%3Akey%3Az6Mk'))
        # Targets are lookup keys only; they are never reinterpreted as URLs.
        self.assertNotIn('https', quote(did(AUTHOR), safe='-._~'))


if __name__ == '__main__':
    unittest.main()
