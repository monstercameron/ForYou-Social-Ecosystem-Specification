"""Synthetic flow invariants; this is not a ledger, wallet, API or chain verifier."""
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass


@dataclass(frozen=True)
class Quote:
    author: str
    message: str
    schedule: str
    amount: int
    expires: int


class FlowModel:
    def __init__(self):
        self.lock = threading.Lock()
        self.invoices = {}
        self.transfers = {}
        self.credits = {}
        self.quotes = {}
        self.receipts = {}
        self.spent = {}
        self.published = set()
        self.frozen = set()

    def invoice(self, invoice, author, expected):
        self.invoices[invoice] = (author, expected)

    def transfer(self, transfer, invoice, amount, confirmed=True, in_time=True):
        with self.lock:
            author, expected = self.invoices[invoice]
            if transfer in self.transfers:
                return self.transfers[transfer]
            if not confirmed:
                return 'pending'
            if not in_time or amount != expected or invoice in self.credits:
                self.transfers[transfer] = 'exception'
                return 'exception'
            self.transfers[transfer] = 'credit'
            self.credits[invoice] = (author, amount)
            return 'credit'

    def resolve_exception(self, transfer, disposition):
        with self.lock:
            if self.transfers.get(transfer) != 'exception':
                raise ValueError('already disposed')
            if disposition not in ('authorized-credit', 'authorized-return'):
                raise ValueError('standing and destination require verification')
            self.transfers[transfer] = disposition

    def balance(self, author):
        funded = sum(amount for owner, amount in self.credits.values() if owner == author)
        return max(0, funded - self.spent.get(author, 0))

    def quote(self, quote_id, quote):
        self.quotes[quote_id] = quote

    def admit(self, author, message, quote_id, now):
        # Caller authentication and signature validation are assumed by this test model.
        with self.lock:
            key = (author, message)
            if key in self.receipts:
                return self.receipts[key]
            quote = self.quotes[quote_id]
            if (quote.author, quote.message) != key:
                raise ValueError('quote bound to different intent')
            if now >= quote.expires:
                raise ValueError('expired quote')
            if author in self.frozen or self.balance(author) < quote.amount:
                raise ValueError('unavailable funds')
            self.spent[author] = self.spent.get(author, 0) + quote.amount
            receipt = (author, message, quote_id, quote.schedule, quote.amount, now)
            self.receipts[key] = receipt
            return receipt

    def finalize(self, author, message, now):
        key = (author, message)
        issued = self.receipts[key][-1]
        if key in self.published:
            return True
        if now >= issued + 30:
            raise ValueError('prepared intent deadline elapsed')
        self.published.add(key)
        return True

    def reorg(self, invoice):
        author, _ = self.credits.pop(invoice)
        self.frozen.add(author)


class FundingFlowTests(unittest.TestCase):
    def funded(self):
        f = FlowModel()
        f.invoice('deposit', 'alice', 100)
        self.assertEqual(f.transfer('tx:0', 'deposit', 100), 'credit')
        return f

    def test_one_deposit_supports_multiple_posts_and_quote_binds_intent(self):
        f = self.funded()
        f.quote('q1', Quote('alice', 'post1', 'old', 10, 10))
        f.quote('q2', Quote('alice', 'post2', 'old', 20, 10))
        with self.assertRaises(ValueError):
            f.admit('alice', 'post2', 'q1', 1)
        self.assertEqual(f.balance('alice'), 100)
        f.admit('alice', 'post1', 'q1', 1)
        f.admit('alice', 'post2', 'q2', 1)
        self.assertEqual(f.balance('alice'), 70)
        self.assertEqual(len(f.receipts), 2)

    def test_schedule_locked_until_quote_expiry(self):
        f = self.funded()
        f.quote('oldquote', Quote('alice', 'one', 'schedule-old', 10, 10))
        f.quote('newquote', Quote('alice', 'two', 'schedule-new', 25, 20))
        self.assertEqual(f.admit('alice', 'one', 'oldquote', 9)[3:5], ('schedule-old', 10))
        with self.assertRaises(ValueError):
            f.admit('alice', 'two', 'newquote', 20)
        self.assertEqual(f.balance('alice'), 90)

    def test_racing_same_message_with_different_quotes_only_debits_once(self):
        f = self.funded()
        for q in ('q1', 'q2'):
            f.quote(q, Quote('alice', 'same', 'schedule', 20, 10))
        gate = threading.Barrier(2)
        def run(q):
            gate.wait()
            return f.admit('alice', 'same', q, 1)
        with ThreadPoolExecutor(max_workers=2) as pool:
            receipts = list(pool.map(run, ('q1', 'q2')))
        self.assertEqual(receipts[0], receipts[1])
        self.assertEqual(f.balance('alice'), 80)
        self.assertEqual(f.admit('alice', 'same', 'q2', 100), receipts[0])

    def test_under_over_duplicate_and_late_transfers_have_one_disposition(self):
        f = self.funded()
        f.invoice('second', 'alice', 50)
        for transfer, amount, in_time in [('under', 49, True), ('over', 51, True), ('late', 50, False)]:
            self.assertEqual(f.transfer(transfer, 'second', amount, in_time=in_time), 'exception')
            self.assertEqual(f.transfer(transfer, 'second', amount), 'exception')
            f.resolve_exception(transfer, 'authorized-return')
            with self.assertRaises(ValueError):
                f.resolve_exception(transfer, 'authorized-credit')
        self.assertEqual(f.transfer('duplicate', 'deposit', 100), 'exception')
        self.assertEqual(f.balance('alice'), 100)

    def test_pending_transfer_never_credits_and_reorg_keeps_receipt(self):
        f = FlowModel()
        f.invoice('deposit', 'alice', 100)
        self.assertEqual(f.transfer('tx:0', 'deposit', 100, confirmed=False), 'pending')
        self.assertEqual(f.balance('alice'), 0)
        self.assertEqual(f.transfer('tx:0', 'deposit', 100), 'credit')
        f.quote('q1', Quote('alice', 'one', 'schedule', 10, 10))
        receipt = f.admit('alice', 'one', 'q1', 1)
        f.reorg('deposit')
        self.assertEqual(f.admit('alice', 'one', 'q1', 100), receipt)
        self.assertEqual(f.balance('alice'), 0)
        f.quote('q2', Quote('alice', 'two', 'schedule', 10, 200))
        with self.assertRaises(ValueError):
            f.admit('alice', 'two', 'q2', 2)

    def test_expiring_prepared_intent_does_not_expire_published_post(self):
        f = self.funded()
        f.quote('q1', Quote('alice', 'prepared', 'schedule', 10, 10))
        f.quote('q2', Quote('alice', 'published', 'schedule', 10, 10))
        r = f.admit('alice', 'prepared', 'q1', 1)
        f.admit('alice', 'published', 'q2', 1)
        f.finalize('alice', 'published', 29)
        with self.assertRaises(ValueError):
            f.finalize('alice', 'prepared', 31)
        self.assertTrue(f.finalize('alice', 'published', 1000))
        self.assertEqual(f.admit('alice', 'prepared', 'q1', 1000), r)
        self.assertEqual(f.balance('alice'), 80)


if __name__ == '__main__':
    unittest.main()
