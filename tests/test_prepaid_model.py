"""Synthetic concurrent prepaid-balance model, not a production ledger or chain verifier."""
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor


class Ledger:
    def __init__(self):
        self.lock=threading.Lock()
        self.observations={}
        self.deposits={}
        self.receipts={}
        self.spent={}
        self.provider_allocation={}
        self.frozen=set()

    def observe(self, transfer, author, network, amount, confirmed):
        """Test harness supplies independent chain verdict; no verifier is implemented."""
        with self.lock:
            binding=(author,network,amount)
            prior=self.observations.get(transfer)
            if prior is not None and prior!=binding: raise ValueError('transfer already bound')
            self.observations[transfer]=binding
            if not confirmed: return False
            if transfer in self.deposits: return False
            self.deposits[transfer]=binding
            return True

    def available(self, author, network):
        funded=sum(amount for a,n,amount in self.deposits.values() if (a,n)==(author,network))
        return max(0,funded-self.spent.get((author,network),0))

    def admit(self, author, network, message_id, quote_id, cost):
        with self.lock:
            key=(author,message_id)
            old=self.receipts.get(key)
            if old is not None:
                return old  # Existing author/message result precedes new quote checks.
            if (author,network) in self.frozen or self.available(author,network)<cost:
                raise ValueError('unavailable funds')
            self.spent[(author,network)]=self.spent.get((author,network),0)+cost
            self.provider_allocation[network]=self.provider_allocation.get(network,0)+cost
            receipt={'author':author,'network':network,'message_id':message_id,'quote_id':quote_id,'cost':cost}
            self.receipts[key]=receipt
            return receipt

    def reorg(self, transfer):
        with self.lock:
            author,network,_=self.deposits.pop(transfer)
            self.frozen.add((author,network))

    def reconcile(self, author, network):
        with self.lock:
            funded=sum(amount for a,n,amount in self.deposits.values() if (a,n)==(author,network))
            if funded < self.spent.get((author,network),0): raise ValueError('unfunded liability')
            self.frozen.discard((author,network))


class PrepaidLedgerTests(unittest.TestCase):
    def test_pending_is_not_spendable_and_duplicate_deposit_never_recredits(self):
        ledger=Ledger(); self.assertFalse(ledger.observe('tx1:0','alice','btc',100,False))
        with self.assertRaises(ValueError): ledger.admit('alice','btc','m1','q1',1)
        self.assertTrue(ledger.observe('tx1:0','alice','btc',100,True))
        self.assertFalse(ledger.observe('tx1:0','alice','btc',100,True))
        with self.assertRaises(ValueError): ledger.observe('tx1:0','bob','btc',100,True)
        self.assertEqual(ledger.available('alice','btc'),100)

    def test_concurrent_debits_cannot_overspend(self):
        ledger=Ledger(); ledger.observe('tx1:0','alice','btc',100,True)
        gate=threading.Barrier(2)
        def attempt(i):
            gate.wait()
            try: ledger.admit('alice','btc',f'm{i}',f'q{i}',75); return True
            except ValueError: return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(attempt,range(2))),1)
        self.assertEqual(ledger.available('alice','btc'),25)
        self.assertEqual(ledger.provider_allocation['btc'],75)
        self.assertEqual(ledger.available('alice','btc')+ledger.provider_allocation['btc'],100)

    def test_simultaneous_identical_retries_share_original_debit(self):
        ledger=Ledger(); ledger.observe('tx1:0','alice','btc',100,True)
        gate=threading.Barrier(8)
        def attempt(_):
            gate.wait()
            return ledger.admit('alice','btc','same-message','same-quote',75)
        with ThreadPoolExecutor(max_workers=8) as pool:
            receipts=list(pool.map(attempt,range(8)))
        self.assertTrue(all(receipt==receipts[0] for receipt in receipts))
        self.assertEqual(ledger.available('alice','btc'),25)
        self.assertEqual(len(ledger.receipts),1)
        self.assertEqual(ledger.provider_allocation['btc'],75)

    def test_exact_retry_is_free_after_reorg_but_new_debit_fails(self):
        ledger=Ledger(); ledger.observe('tx1:0','alice','btc',100,True)
        first=ledger.admit('alice','btc','m1','q1',75)
        ledger.reorg('tx1:0')
        self.assertEqual(ledger.admit('alice','btc','m1','q1',75),first)
        with self.assertRaises(ValueError): ledger.admit('alice','btc','m2','q2',1)
        self.assertEqual(ledger.admit('alice','btc','m1','q-changed',75),first)
        self.assertEqual(ledger.available('alice','btc'),0)
        self.assertEqual(ledger.spent[('alice','btc')],75)
        with self.assertRaises(ValueError): ledger.reconcile('alice','btc')
        self.assertTrue(ledger.observe('tx1:0','alice','btc',100,True))
        ledger.reconcile('alice','btc')
        self.assertEqual(ledger.admit('alice','btc','m1','q1',75),first)
        self.assertEqual(ledger.available('alice','btc'),25)

    def test_assets_never_cross_credit(self):
        ledger=Ledger(); ledger.observe('eth-tx','alice','eth',1000,True)
        with self.assertRaises(ValueError): ledger.admit('alice','btc','m','q',1)
        self.assertEqual(ledger.available('alice','eth'),1000)


if __name__=='__main__': unittest.main()
