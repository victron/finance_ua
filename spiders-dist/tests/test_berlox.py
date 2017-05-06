import unittest
import importlib
import json
import pickle
from os import path
from datetime import datetime
from time import sleep
from pymongo import MongoClient
from unittest.mock import patch

from common import mock_requests
from spiders import berlox
from spiders.parallel import parent
from spiders.common_spider import local_tz
from spiders.mongo_start import records, data_active
import spiders.mongo_start as mongo_start

DATA_PATH = path.join('data', 'pages', '')

DB_NAME = 'TEST'
client = MongoClient()
DATABASE = client[DB_NAME]

def current_key():
    # test key for test file
    return b'2\xe8[9%g\xacL\xe2\x10Q)\x96\xfeI<)\xec\x9b\xa0\xdf\xa3\xc5;\x13\xe4F\x14\x15\xa2\xd6\x0f'


def set_tes_environ(fn, data):
    def wraper(*args):
        return fn(data)
    return wraper

class InitTestsCase(unittest.TestCase):
    importlib.reload(mongo_start)

    def setUp(self):
        with open(DATA_PATH + 'berlox.data', 'rb') as f:
            self.data = pickle.load(f)

    def tearDown(self):
        MongoClient().drop_database(DB_NAME)


class ParseBerlox(InitTestsCase):

    @patch('spiders.berlox.requests.get', side_effect=mock_requests)
    @patch('spiders.berlox.current_key', side_effect=current_key)
    def test1_decryptor(self, request_fun, current_key_fun):
        decrypt_result = berlox.fetch_data()
        with open(DATA_PATH + 'berlox.json', 'r') as f:
            data_raw = json.load(f)
        self.assertEqual(decrypt_result, data_raw, 'RAW data after decryption not as expected')

        # convert in common API format
        result = berlox.data_api_berlox(berlox.fetch_data)
        self.assertEqual(self.data, result, 'error in common API data')


    @patch('spiders.berlox.requests.get', side_effect=mock_requests)
    @patch('spiders.berlox.current_key', side_effect=current_key)
    def test2_mongo_data(self, requests_fun, current_key_fun):
        result = parent([(berlox.data_api_berlox, berlox.fetch_data), ], 'records')
        print(result)
        first_insert_time = datetime.now(tz=local_tz)
        assert result == (len(self.data), 0), 'wrong parent return, etalon is {} records'.format(len(self.data))
        assert result[0] == records.find({}).count(), 'function insert report wrong'
        assert records.find({}).count() == len(self.data), 'should be {} in "records"'.format(len(self.data))
        assert data_active.find({}).count() == len(self.data), 'should be {} in "data_active"'.format(len(self.data))
        assert data_active.find({}).count() == records.find({}).count(), 'after first insert "records" and ' \
                                                                         '"data_active" should be equal'

        test_bid = '2ffe1e92429d4abf9f98af42c7afdaf6'
        test_record_time = data_active.find_one({'bid': test_bid})['time']
        assert data_active.find_one({'bid': test_bid})['time'] < \
               data_active.find_one({'bid': test_bid})['time_update']
        test_record_first_update_time = data_active.find_one({'bid': test_bid})['time_update']
        sleep(2)

        # second insert of same data
        result = parent([(berlox.data_api_berlox, berlox.fetch_data), ], 'records')
        self.assertEqual(result, (len(self.data), 0))
        assert data_active.find_one({'bid': test_bid})['time'] == test_record_time, 'after UPDATE "time" should be same'
        assert data_active.find_one({'bid': test_bid})['time_update'] > test_record_first_update_time, \
            'time_update should be changed in UPDATE'
        self.assertEqual(data_active.find({}).count(), len(self.data))
        self.assertEqual(records.find({}).count(), len(self.data) * 2)
        self.assertLess(first_insert_time, data_active.find_one({'bid': test_bid})['time_update'],
                        'time_update is not newer;')



    @patch('spiders.berlox.fetch_data')
    def test3_no_one_in_new_file(self, fetch_data_mock):
        with open(DATA_PATH + 'berlox.json', 'r') as f:
            decrypt_result = json.load(f)
        with open(DATA_PATH + 'berlox-delete_one.json', 'r') as f:
            decrypt_result_delete_one = json.load(f)
        fetch_data_mock.return_value = decrypt_result
        # first insert in collection
        result = parent([(berlox.data_api_berlox, berlox.fetch_data), ], 'records')
        print(result)
        test_bid = '2ffe1e92429d4abf9f98af42c7afdaf6'
        test_record_time = data_active.find_one({'bid': test_bid})['time']
        test_record_first_update_time = data_active.find_one({'bid': test_bid})['time_update']
        # second insert in collection, one bid missing
        fetch_data_mock.return_value = decrypt_result_delete_one
        result = parent([(berlox.data_api_berlox, berlox.fetch_data), ], 'records')
        print(result)
        self.assertEqual(result, (len(self.data) - 1, 1))
        assert result[0] == data_active.find({}).count(), 'function insert report wrong'
        assert data_active.find({}).count() == len(self.data) - 1, 'should be {} in "records"'.format(
            len(self.data) - 1)
        assert data_active.find({}).count() != records.find({}).count(), 'after insert "records" and "data_active"' \
                                                                         'should not be equal'
        assert data_active.find_one({'bid': test_bid})['time'] == test_record_time, 'after UPDATE "time" should be same'
        assert data_active.find_one({'bid': test_bid})['time_update'] > test_record_first_update_time, \
            'time_update should be changed in UPDATE'


if __name__ == '__main__':
    unittest.main()