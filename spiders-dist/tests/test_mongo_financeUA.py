import unittest
import logging
import pickle
from pymongo import MongoClient
from datetime import datetime

from spiders.mongo_start import data_active
from save_test_pages import files, operations, currencies, filemap, data_path, gen_files_del
from spiders.finance_ua import fetch_data, data_api_finance_ua
from spiders.mongo_start import records, data_active

from spiders.parallel import parent
from spiders.common_spider import local_tz


logger = logging.getLogger()
# logging.basicConfig(level=logging.DEBUG)


DB_NAME = 'TEST'
client = MongoClient()
DATABASE = client[DB_NAME]

def set_tes_environ(fn, data):
    def wraper(*args):
        return fn(data)
    return wraper


class MongoTests(unittest.TestCase):
    def setUp(self):
        with open(data_path + 'financeUA.bin', 'rb') as f:
            data = f.read().decode()
        with open(data_path + 'financeUA.bin.del', 'rb') as f:
            data_del = f.read().decode()
        with open(data_path + 'financeUA.data', 'rb') as f:
            self.data = pickle.load(f)                      # docs to insert

        self.fetch_data_test = set_tes_environ(fetch_data, data)
        self.fetch_data_test_del = set_tes_environ(fetch_data, data_del)


    def tearDown(self):
        MongoClient().drop_database(DB_NAME)


    def test_insert(self):
        result = parent([(data_api_finance_ua, self.fetch_data_test),], 'records')
        print(result)
        first_insert_time = datetime.now(tz=local_tz)
        assert result == (len(self.data), 0), 'wrong parent return, etalon is {} records'.format(len(self.data))
        assert result[0] == records.find({}).count(), 'function insert report wrong'
        assert records.find({}).count() == len(self.data), 'should be {} in "records"'.format(len(self.data))
        assert data_active.find({}).count() == len(self.data), 'should be {} in "data_active"'.format(len(self.data))
        assert data_active.find({}).count() == records.find({}).count(), 'after first insert "records" and "data_active"' \
                                                                         'should be equal'
        test_bid = 960072
        test_record_time = data_active.find_one({'bid': test_bid})['time']
        bid_time = data_active.find_one({'bid': test_bid})['time']
        bid_time_update = data_active.find_one({'bid': test_bid})['time_update']
        # assert bid_time < bid_time_update, 'bid_time= {}, bid_time_update= {}'.format(bid_time, bid_time_update)
        test_record_first_update_time = data_active.find_one({'bid': test_bid})['time_update']

        # second insert of same data
        result = parent([(data_api_finance_ua, self.fetch_data_test),], 'records')
        assert result == (len(self.data), 0), 'wrong parent return, etalon is {} records'.format(len(self.data))
        assert data_active.find_one({'bid': test_bid})['time'] == test_record_time, 'after UPDATE "time" should be same'
        assert data_active.find_one({'bid': test_bid})['time_update'] > test_record_first_update_time, \
            'time_update should be changed in UPDATE'
        assert data_active.find({}).count() == len(self.data), 'should be {} in "data_active"'.format(len(self.data))
        assert records.find({}).count() == len(self.data) * 2, 'should be {} in "records"'.format(len(self.data)*2)
        assert first_insert_time < data_active.find_one()['time_update'], 'time_update is not newer'

        # 3-d inssert of data with deleted records
        result = parent([(data_api_finance_ua, self.fetch_data_test_del), ], 'records')
        print(result)
        assert result == (len(self.data) - 1, 1), 'wrong parent return, etalon is {} records'.format(len(self.data)-1)
        assert result[0] == data_active.find({}).count(), 'function insert report wrong'
        assert data_active.find({}).count() == len(self.data) - 1, 'should be {} in "records"'.format(len(self.data)-1)
        assert data_active.find({}).count() != records.find({}).count(), 'after insert "records" and "data_active"' \
                                                                         'should not be equal'
        assert data_active.find_one({'bid': test_bid})['time'] == test_record_time, 'after UPDATE "time" should be same'
        assert data_active.find_one({'bid': test_bid})['time_update'] > test_record_first_update_time, \
            'time_update should be changed in UPDATE'