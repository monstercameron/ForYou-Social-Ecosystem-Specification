"""Synthetic one-use challenge fencing; not a production auth service."""
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor


class ChallengeStore:
    def __init__(self, limit=2):
        self.limit = limit
        self.lock = threading.Lock()
        self.generation = 0
        self.entries = {}

    def issue(self, nonce, now):
        with self.lock:
            self.entries = {k: v for k, v in self.entries.items() if v[1] > now}
            if len(self.entries) >= self.limit or nonce in self.entries:
                return False
            self.entries[nonce] = (self.generation, now + 60, False)
            return True

    def consume(self, nonce, now):
        with self.lock:
            item = self.entries.get(nonce)
            if item is None or item[0] != self.generation or item[1] <= now or item[2]:
                return False
            self.entries[nonce] = (item[0], item[1], True)
            return True

    def recover_without_consumption_history(self):
        with self.lock:
            self.generation += 1


class ChallengeFencingTests(unittest.TestCase):
    def test_only_one_concurrent_consumer_succeeds(self):
        store = ChallengeStore()
        self.assertTrue(store.issue('a', 0))
        gate = threading.Barrier(8)
        def consume():
            gate.wait()
            return store.consume('a', 1)
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(lambda _: consume(), range(8))), 1)

    def test_recovery_fences_old_unconsumed_challenge(self):
        store = ChallengeStore()
        self.assertTrue(store.issue('old', 0))
        store.recover_without_consumption_history()
        self.assertFalse(store.consume('old', 1))
        self.assertTrue(store.issue('new', 1))
        self.assertTrue(store.consume('new', 2))

    def test_capacity_is_reclaimed_only_after_expiry(self):
        store = ChallengeStore(limit=1)
        self.assertTrue(store.issue('a', 0))
        self.assertTrue(store.consume('a', 1))
        self.assertFalse(store.issue('b', 2))
        self.assertTrue(store.issue('b', 60))
        self.assertFalse(store.consume('a', 60))


if __name__ == '__main__':
    unittest.main()
