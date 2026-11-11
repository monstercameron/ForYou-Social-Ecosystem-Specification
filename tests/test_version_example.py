"""Verify the published synthetic post version example and its signatures."""
import json
import unittest
from pathlib import Path

from test_security_profile import validate


class VersionExampleTests(unittest.TestCase):
    def test_signed_fork_history_and_reply(self):
        root = Path(__file__).resolve().parents[1]
        example = json.loads((root / 'examples/post-version-chain.json').read_text(encoding='utf-8'))
        messages = example['messages']
        by_id = {message['message_id']: message for message in messages}
        self.assertEqual(len(by_id), len(messages))
        self.assertEqual(len({m['submission_receipt']['receipt_id'] for m in messages}), len(messages))
        for message in messages:
            validate(message)
            self.assertEqual(message['message_type'], 'post')
            self.assertIn(message['submission_receipt']['network'], ('bitcoin-mainnet','ethereum-mainnet'))
            parent = message['payload'].get('supersedes')
            if parent:
                self.assertIn(parent, by_id)
                self.assertEqual(by_id[parent]['author_id'], message['author_id'])
        versions = [m for m in messages if 'reply_to' not in m['payload']]
        replaced = {m['payload']['supersedes'] for m in versions if 'supersedes' in m['payload']}
        leaves = [m for m in versions if m['message_id'] not in replaced]
        chosen = min(m['message_id'] for m in leaves)
        self.assertEqual(chosen, example['expected']['known_head'])
        reply = next(m for m in messages if 'reply_to' in m['payload'])
        self.assertEqual(reply['payload']['reply_to'], example['expected']['reply_target'])
        self.assertNotEqual(reply['payload']['reply_to'], chosen)


if __name__ == '__main__':
    unittest.main()
