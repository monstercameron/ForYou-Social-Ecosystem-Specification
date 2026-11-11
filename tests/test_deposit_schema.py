"""Synthetic deposit structure and unit conversion; not chain verification."""
import copy
import unittest
import jsonschema
from test_operations_profile import structural
from test_security_profile import AUTHOR,PROVIDER,did


def credit(network='bitcoin-mainnet'):
    btc=network=='bitcoin-mainnet'
    return {'credit_id':'fydc2:'+'a'*64,'provider_id':did(PROVIDER),'author_id':did(AUTHOR),
            'deposit_id':'fydi2:'+'b'*64,'network':network,
            'transfer':{'network':network,'txid':'c'*64,'output_index':0} if btc else {'network':network,'tx_hash':'c'*64},
            'amount_chain_units':'12','amount_accounting_units':'12000' if btc else '12',
            'credit_sequence':1,'credited_at':'2026-11-11T00:00:00Z','provider_signature':'A'*86}


def check_conversion(record):
    structural('DepositCredit',record)
    chain=int(record['amount_chain_units']); accounting=int(record['amount_accounting_units'])
    expected=chain*1000 if record['network']=='bitcoin-mainnet' else chain
    if accounting!=expected: raise ValueError('wrong unit conversion')


class DepositSchemaTests(unittest.TestCase):
    def test_btc_millisatoshi_and_eth_wei_conversion(self):
        for network in ('bitcoin-mainnet','ethereum-mainnet'):
            value=credit(network); check_conversion(value)
            value['amount_accounting_units']='1'
            with self.assertRaisesRegex(ValueError,'conversion'): check_conversion(value)

    def test_cross_network_transfer_and_negative_amount_rejected(self):
        value=credit(); value['transfer']={'network':'ethereum-mainnet','tx_hash':'c'*64}
        with self.assertRaises(jsonschema.ValidationError): structural('DepositCredit',value)
        value=credit(); value['amount_chain_units']='-1'
        with self.assertRaises(jsonschema.ValidationError): structural('DepositCredit',value)


if __name__=='__main__': unittest.main()
