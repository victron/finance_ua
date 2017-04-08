import unittest
import requests
from unittest.mock import patch
import pickle
from datetime import datetime, date, time, timezone
from pymongo import MongoClient
from collections import namedtuple

#
# import sys
# print(sys.path)
from common import DATA_PATH, mock_requests, DB_NAME
from spiders.commodities.graintrade import available_commodities, get_page, get_commudities, update_mongo

client = MongoClient()
TEST_DATABASE = client[DB_NAME]

etalon_list = ['Corn ', 'Wheat', 'Oats', 'Rice', 'Soybean', 'Soybean oil meal', 'Soybean oil', 'Rapeseeds',
                       'EUR-USD', 'Corn ', 'Wheat', 'Rapeseeds', 'Nitrogen solution', 'Sunflower-seed oil']
etalon_docs = [{'sunflower_oil': 763.55, 'time': datetime.combine(date.today(), time.min, timezone.utc)},
  #duplicity   {'Corn ': 143.6, 'time': datetime.datetime(2017, 4, 5, 0, 0, tzinfo=datetime.timezone.utc)},
               {'corn': 183.14, 'time': datetime.combine(date.today(), time.min, timezone.utc)},
  # duplicity  {'Wheat': 157.45, 'time': datetime.datetime(2017, 4, 5, 0, 0, tzinfo=datetime.timezone.utc)},
               {'wheat': 175.14, 'time': datetime.combine(date.today(), time.min, timezone.utc)},
               {'oats': 129.09, 'time': datetime.combine(date.today(), time.min, timezone.utc)}]

class Parser(unittest.TestCase):

    def tearDown(self):
        client.drop_database(DB_NAME)

    @patch('spiders.commodities.graintrade.requests.get', side_effect=mock_requests)
    def test1_available_commodities(self, requests_fun):
        self.assertEqual(len(available_commodities(get_page())), len(etalon_list))
        self.assertEqual(available_commodities(get_page()), etalon_list)

    @patch('spiders.commodities.graintrade.requests.get', side_effect=mock_requests)
    def test2_get_commudities(self, requsts_fun):
        self.assertEqual(get_commudities(['Sunflower-seed oil', 'Corn ', 'Wheat', 'Oats']), etalon_docs)
        # print(get_commudities(['Sunflower-seed oil', 'Corn_errrrrrror ', 'Wheat', 'Oats']))
        self.assertRaises(NameError, get_commudities, ['Sunflower-seed oil', 'Corn_errrrrrror ', 'Wheat', 'Oats'])

    @patch('spiders.commodities.graintrade.requests.get', side_effect=mock_requests)
    @patch('spiders.commodities.graintrade.available_commodities', side_effect=ValueError)
    def test3_error_in_available_commodities(self, requests_fun, available_fun):
        self.assertRaises(ValueError, get_commudities, ['Sunflower-seed oil', 'Corn ', 'Wheat', 'Oats'])

    @patch('spiders.commodities.graintrade.requests.get', side_effect=mock_requests)
    def test4_mongo_update(self, requests_fun):
        result_tuple = namedtuple('update_history', 'matched_count modified_count upserted')
        etalon_result = result_tuple(matched_count=3, modified_count=3, upserted=1)
        self.assertEqual(update_mongo(['sunflower_oil', 'corn', 'wheat', 'oats']), etalon_result)
        print(update_mongo(['sunflower_oil', 'corn', 'wheat', 'oats']),
                           result_tuple(matched_count=4, modified_count=4, upserted=0))