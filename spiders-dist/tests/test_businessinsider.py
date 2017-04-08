# could be as example - how to mock test DB
import unittest
from unittest.mock import patch
import requests
import pickle
import datetime
from datetime import date
import pytz
from pymongo import MongoClient

from common import DATA_PATH, mock_requests
from spiders.commodities.businessinsider import current_commodities, history_commodity, available_commodities

CURRENT_DATE = date(2017, 3, 28)

DB_NAME = 'TEST'
client = MongoClient()
TEST_DATABASE = client[DB_NAME]

@patch('spiders.parameters.DATABASE', TEST_DATABASE)    # mock DB to all
class Parser(unittest.TestCase):
    # def setUp(self):
    #     importlib.reload(m_start)

    def tearDown(self):
        client.drop_database(DB_NAME)

    @patch('spiders.commodities.businessinsider.requests.get', side_effect=mock_requests)
    def test1_current_commodities(self,requests_fun):
        iron = [{'iron-ore-price': 88.35,
                 'time': datetime.datetime(2017, 3, 24, 0, 0, tzinfo=pytz.utc)}]
        self.assertEqual(current_commodities(['Iron Ore']), iron)

        list_commodities = [
            {'rhodium': 1015.0, 'time': datetime.datetime(2017, 3, 24, 0, 0, tzinfo=pytz.utc)},
            {'iron-ore-price': 88.35, 'time': datetime.datetime(2017, 3, 24, 0, 0, tzinfo=pytz.utc)},
            {'copper-price': 5804.76, 'time': datetime.datetime(2017, 3, 24, 0, 0, tzinfo=pytz.utc)}]
        self.assertEqual(current_commodities(['Iron Ore', 'Copper', 'Rhodium']), list_commodities)
        self.assertRaises(NameError, current_commodities, ['Iron Orerrrror',]) # wrong name in arg
        print(current_commodities(['Iron Ore', 'Copper', 'Rhodium']))

    @patch('spiders.commodities.businessinsider.requests.get', side_effect=mock_requests)
    @patch('spiders.commodities.businessinsider.requests.post', side_effect=mock_requests)
    def test2_history_commodity(self, requests_fun_get, requests_fun_post):
        result = history_commodity('Iron Ore', datetime.datetime(2014, 1, 1), datetime.datetime(2017, 3, 28))
        with open(DATA_PATH + 'history_commodity.data', 'rb') as f:
            etalon = pickle.load(f)
            # pickle.dump(result, f)
        self.assertEqual(len(result), len(etalon), 'wrong lenght of data')
        self.assertEqual(result, etalon)

    @patch('spiders.commodities.businessinsider.requests.get', side_effect=mock_requests)
    def test3_available_commodities(self, requests_fun):
        etalon_available = {'Gold': 'gold-price', 'Iron Ore': 'iron-ore-price', 'Palladium': 'palladium-price',
                            'Platinum': 'platinum-price',
                            'Rhodium': 'rhodium', 'Silver': 'silver-price',
                            'Natural Gas (Henry Hub)': 'natural-gas-price', 'Ethanol': 'ethanol-price',
                            'Heating Oil': 'heating-oil-price', 'Coal': 'coal-price', 'Uran': 'uranpreis',
                            'Oil (Brent)': 'oil-price?type=Brent', 'Oil (WTI)': 'oil-price?type=WTI',
                            'Aluminium': 'aluminum-price', 'Lead': 'lead-price',
                            'Copper': 'copper-price', 'Nickel': 'nickel-price', 'Zinc': 'zinc-price',
                            'Tin': 'tin-price', 'Cotton': 'cotton-price', 'Oats': 'oats-price',
                            'Lumber': 'lumber-price', 'Coffee': 'coffee-price', 'Cocoa': 'cocoa-price',
                            'Live Cattle': 'live-cattle-price', 'Lean Hog': 'lean-hog-price', 'Corn': 'corn-price',
                            'Feeder Cattle': 'feeder-cattle-price', 'Milk': 'milk-price',
                            'Orange Juice': 'orange-juice-price', 'Palm Oil': 'palm-oil-price',
                            'Rapeseed': 'rapeseed-price', 'Rice': 'rice-price', 'Soybeans': 'soybeans-price',
                            'Soybean Meal': 'soybean-meal-price', 'Soybean Oil': 'soybean-oil-price',
                            'Wheat': 'wheat-price', 'Sugar': 'sugar-price'}
        self.assertEqual(available_commodities(), etalon_available)

    # @patch('spiders.parameters.DATABASE', TEST_DATABASE)    # mock DB only for this test
    @patch('spiders.commodities.businessinsider.requests.get', side_effect=mock_requests)
    @patch('spiders.commodities.businessinsider.requests.post', side_effect=mock_requests)
    def test4_history_commodity(self, requests_fun_get, requests_fun_post):
        from spiders.mongo_start import commodities
        from spiders.commodities.update_history_logic import update_commudities_collection

        # http://www.voidspace.org.uk/python/mock/examples.html#partial-mocking
        with patch('spiders.commodities.update_history_logic.date') as mock_date:
            mock_date.today.return_value = date(2017, 3, 28)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            # self.assertRaises(KeyError, update_commudities_collection, ['Iron Ore',]) # site key should not be used
                                                                                      # in this function
            update_commudities_collection(['iron_ore',])
            find_all = commodities.find()
            with open(DATA_PATH + 'update_commudities_collection.data', 'rb') as f:
                # pickle.dump([doc for doc in find_all], f)
                etalon_dict = pickle.load(f)
            self.assertEqual(etalon_dict, [i for i in find_all])


