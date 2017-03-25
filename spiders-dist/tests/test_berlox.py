import unittest
import importlib
import json
import pickle
from os import path
from datetime import datetime
from time import sleep
from pymongo import MongoClient

from spiders.berlox import data_api_berlox, fetch_data
from spiders.parallel import parent
from spiders.common_spider import local_tz
from spiders.mongo_start import records, data_active
import spiders.mongo_start as mongo_start

DATA_PATH = path.join('data', 'pages', '')

DB_NAME = 'TEST'
client = MongoClient()
DATABASE = client[DB_NAME]

def set_tes_environ(fn, data):
    def wraper(*args):
        return fn(data)
    return wraper



class ParseBerlox(unittest.TestCase):
    importlib.reload(mongo_start)
    def setUp(self):
        with open(DATA_PATH + 'berlox.enc', 'rb') as f:
            data_enc = f.read()
        with open(DATA_PATH + 'berlox-del.json', 'r') as f:
            self.data_del = json.load(f)
        with open(DATA_PATH + 'berlox.json', 'r') as f:
            self.data_raw = json.load(f)
        with open(DATA_PATH + 'berlox.data', 'rb') as f:
            self.data = pickle.load(f)

        self.fetch_data_test = set_tes_environ(fetch_data, data_enc)    # function with test data

        def gen_raw_data_delete():
            return self.data_del

        self.fetch_data_test_del = gen_raw_data_delete                  # simulate self.fetch_data_test
                                                                            # with one deleted order
    def tearDown(self):
        MongoClient().drop_database(DB_NAME)

    def test1_parser(self):
        result = self.fetch_data_test()
        assert result == self.data_raw, 'RAW data after decryption not as expected'

        # convert in common API format
        result = data_api_berlox(self.fetch_data_test)
        assert self.data == result, 'error in common API data'


    def test2_mongo_data(self):
        result = parent([(data_api_berlox, self.fetch_data_test), ], 'records')
        print(result)
        first_insert_time = datetime.now(tz=local_tz)
        assert result == (len(self.data), 0), 'wrong parent return, etalon is {} records'.format(len(self.data))
        assert result[0] == records.find({}).count(), 'function insert report wrong'
        assert records.find({}).count() == len(self.data), 'should be {} in "records"'.format(len(self.data))
        assert data_active.find({}).count() == len(self.data), 'should be {} in "data_active"'.format(len(self.data))
        assert data_active.find({}).count() == records.find({}).count(), 'after first insert "records" and ' \
                                                                         '"data_active" should be equal'

        test_bid = '063ba4afd79549e88c1b0e54f2f149ab'
        test_record_time = data_active.find_one({'bid': test_bid})['time']
        assert data_active.find_one({'bid': test_bid})['time'] < \
               data_active.find_one({'bid': test_bid})['time_update']
        test_record_first_update_time = data_active.find_one({'bid': test_bid})['time_update']
        sleep(2)

        # second insert of same data
        result = parent([(data_api_berlox, self.fetch_data_test), ], 'records')
        assert result == (len(self.data), 0), 'wrong parent return ={}, etalon is {} records'.format(result, len(self.data))
        assert data_active.find_one({'bid': test_bid})['time'] == test_record_time, 'after UPDATE "time" should be same'
        assert data_active.find_one({'bid': test_bid})['time_update'] > test_record_first_update_time, \
            'time_update should be changed in UPDATE'
        assert data_active.find({}).count() == len(self.data), 'should be {} in "data_active"'.format(len(self.data))
        assert records.find({}).count() == len(self.data) * 2, 'should be {} in "records"'.format(len(self.data) * 2)
        assert first_insert_time < data_active.find_one({'bid': test_bid})['time_update'], 'time_update is not newer; ' \
                                                                          'first_insert_time= {}, ' \
                                                                          'time_update= {}'.format(first_insert_time,
                                                                                                   data_active.find_one()['time_update'])

        # 3-d inssert of data with deleted records
        result = parent([(data_api_berlox, self.fetch_data_test_del), ], 'records')
        print(result)
        assert result == (len(self.data) - 1, 1), 'wrong parent return, etalon is {} records'.format(len(self.data) - 1)
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