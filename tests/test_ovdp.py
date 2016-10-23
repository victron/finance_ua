import unittest
from bson.codec_options import CodecOptions
from spiders.common_spider import get_tzinfo
from data.ovdp import data, data2, income_result_etalon, bonds_etalon, payments_etalon

from mongo_collector.bonds import colection_meta, bonds_income, update_auctions
from mongo_collector.bonds import bonds_match, generate_bonds, internal_payments

local_tz = get_tzinfo()
DB_NAME = 'TESTS'
# from mongo_collector import DB_NAME
import pymongo
from pymongo import MongoClient
client = MongoClient()
DATABASE = client[DB_NAME]
aware_times = lambda collection: DATABASE[collection].with_options(codec_options=CodecOptions(tz_aware=True,
                                                                                              tzinfo=local_tz))
bonds_auction = aware_times('bonds_auction')
bonds_payments = aware_times('bonds_payments')
bonds = aware_times('bonds')



class Ovdp(unittest.TestCase):

    def setUp(self):
        bonds_auction.create_index([('auctiondate', pymongo.ASCENDING),
                                    ('auctionnum', pymongo.ASCENDING)], unique=True, name='bonds_auction')
        bonds_payments.create_index([('bond', pymongo.ASCENDING),
                                     ('time', pymongo.ASCENDING),
                                     ('pay_type', pymongo.ASCENDING)], unique=True, name='payments')
        bonds_auction.insert_many(data)

    def tearDown(self):
        MongoClient().drop_database('TESTS')

    def test_auction(self):
        bonds_auction_state = colection_meta(bonds_auction)
        assert bonds_auction_state.actual is False, 'meta data wrong'
        assert bonds_auction_state.update_time == bonds_auction_state.insert_time

        update_auctions(data)
        bonds_auction_state = colection_meta(bonds_auction)
        assert bonds_auction_state.actual is False, 'meta data wrong'
        assert bonds_auction_state.update_time > bonds_auction_state.insert_time

    # def test_income(self):
        bonds_income()
        income_results = bonds_payments.find({'pay_type': 'income', '_id': {'$ne': 'update'}}, {'_id': False})
        income_result = [doc for doc in income_results]
        assert income_result == income_result_etalon, 'income data wrong'

    # def test_bonds_collection(self):
        match_bonds = bonds_match(bonds, 'update_time')
        assert match_bonds.update is True, 'bonds present in DB'
        generate_bonds(match_bonds)
        cursor_bonds = bonds.find({'_id': {'$ne': 'update'}})
        result_bonds = [doc for doc in cursor_bonds]
        assert result_bonds == bonds_etalon, 'wrong data in "bonds" collection'

        # generate payments information
        for doc in bonds.find({'_id': {'$ne': 'update'}}):
            internal_payments(doc)
        cursor_payments = bonds_payments.find({'_id': {'$ne': 'update'}}, {'_id': False})
        result_payments = [doc for doc in cursor_payments]
        assert result_payments == payments_etalon, 'wrong date in "bonds_payments"'

if __name__ == '__main__':
    unittest.main()