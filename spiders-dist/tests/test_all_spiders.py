import unittest
import json
import pickle
from os import path
from datetime import datetime
from pymongo import MongoClient
from functools import reduce
from time import sleep
import logging

from spiders import berlox
from spiders import finance_ua
from spiders import parse_minfin
from save_test_pages import files, gen_files_del
from spiders.common_spider import local_tz
from spiders.mongo_start import records, data_active
from test_parse_minfin import response_generator
from common import date_depends_time

from spiders.parallel import parent

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

DATA_PATH = path.join('data', 'pages', '')

DB_NAME = 'TEST'
client = MongoClient()
DATABASE = client[DB_NAME]


def set_test_environment(fn, data):
    def wraper(*args, **kwargs):
        return fn(*args, test_data=data)
    return wraper


class Parsers(unittest.TestCase):
    def setUp(self):
        ############ berlox #############
        with open(DATA_PATH + 'berlox.enc', 'rb') as f:
            data_enc = f.read()
        with open(DATA_PATH + 'berlox-del.json', 'r') as f:
            self.data_del = json.load(f)
        with open(DATA_PATH + 'berlox.json', 'r') as f:
            self.data_raw = json.load(f)
        with open(DATA_PATH + 'berlox.data', 'rb') as f:
            self.data_berlox = pickle.load(f)

        self.fetch_data_test_berlox = set_test_environment(berlox.fetch_data, data_enc)  # function with test data

        def gen_raw_data_delete():
            return self.data_del

        self.fetch_data_test_berlox_del = gen_raw_data_delete  # simulate self.fetch_data_test

        ########### financeUA ##################
        with open(DATA_PATH + 'financeUA.bin', 'rb') as f:
            data = f.read().decode()
        with open(DATA_PATH + 'financeUA.bin.del', 'rb') as f:
            data_del = f.read().decode()
        with open(DATA_PATH + 'financeUA.data', 'rb') as f:
            self.data_finUA = pickle.load(f)  # docs to insert


        self.fetch_data_test_finUA = set_test_environment(finance_ua.fetch_data, data)
        self.fetch_data_test_finUA_del = set_test_environment(finance_ua.fetch_data, data_del)

        ########### parseminfin ####################
        self.get_triple_data_test = set_test_environment(parse_minfin.get_triple_data, files)
        self.get_triple_data_test_del = set_test_environment(parse_minfin.get_triple_data, gen_files_del())
        with open(DATA_PATH + 'minfinUA.data', 'rb') as f:
            self.data_parseminfin = pickle.load(f)

        self.data_all = self.data_berlox + self.data_finUA + self.data_parseminfin
        self.test_bid = {'test_bid_berlox': '063ba4afd79549e88c1b0e54f2f149ab',
                         'test_bid_finUA': 960072,
                         'test_bid_parseminfin': '32166583'}

    def tearDown(self):
        MongoClient().drop_database(DB_NAME)

    def test_mongo_data(self):
        result = parent([(berlox.data_api_berlox, self.fetch_data_test_berlox),
                         (finance_ua.data_api_finance_ua, self.fetch_data_test_finUA),
                         (parse_minfin.data_api_minfin, self.get_triple_data_test)], 'records')
        print(result)
        print('self.data_all= ', len(self.data_all))
        first_insert_time = datetime.now(tz=local_tz)

        self.assertEqual(result, (len(self.data_all) - 6 + 1, 0),
                         '6 - docs with cookies from minfin in "record";'
                         'in "data_active" present only 1 doc with cookies')
        # TODO: could be poblem. In records inserted not all cookies, in data_active inserted all cookies
        self.assertEqual(result[0], records.find({}).count(), 'should present 1 doc with cookies')
        self.assertEqual(records.find({}).count(), len(self.data_all) - 6 + 1)
        self.assertEqual(data_active.find({}).count(), len(self.data_all), 'should be {} in "data_active"'.format(
            len(self.data_all)))
        self.assertEqual(data_active.find({}).count(), records.find({}).count() + 6 - 1)

        test_record_times = {}
        test_record_first_update_time = {}
        for spider, bid in self.test_bid.items():
            test_record_times[spider] = data_active.find_one({'bid': bid})['time']
            doc = data_active.find_one({'bid': bid})
            doc = date_depends_time(doc)    # fix date if time is grade then current TODO: need check, if change need in code
            self.assertLess(doc['time'], doc['time_update'])
            test_record_first_update_time[spider] = data_active.find_one({'bid': bid})['time_update']
        sleep(1)

# second insert of same data
        result = parent([(berlox.data_api_berlox, self.fetch_data_test_berlox),
                         (finance_ua.data_api_finance_ua, self.fetch_data_test_finUA),
                         (parse_minfin.data_api_minfin, self.get_triple_data_test)], 'records')
        self.assertEqual(result, (0, 0))
        for spider, bid in self.test_bid.items():
            assert data_active.find_one({'bid': bid})['time'] == test_record_times[spider], 'after UPDATE "time" should be same'
            assert data_active.find_one({'bid': bid})['time_update'] > test_record_first_update_time[spider], \
                'time_update should be changed in UPDATE '

        assert data_active.find({}).count() == len(self.data_all), 'should be {} in ' \
                                                                   '"data_active"'.format(len(self.data_all))
        self.assertEqual(records.find({}).count(), len(self.data_all) - 6 + 1)
        assert first_insert_time < data_active.find_one()['time_update'], 'time_update is not newer'

        # 3-d inssert of data with deleted records
        result = parent([(berlox.data_api_berlox, self.fetch_data_test_berlox_del),
                         (finance_ua.data_api_finance_ua, self.fetch_data_test_finUA_del),
                         (parse_minfin.data_api_minfin, self.get_triple_data_test_del)], 'records')
        print(result)
        self.assertEqual(result, (0, 8))
        assert data_active.find({}).count() != records.find({}).count(), 'after insert "records" and "data_active"' \
                                                                         'should not be equal'
        for spider, bid in self.test_bid.items():
            assert data_active.find_one({'bid': bid})['time'] == test_record_times[spider], 'after UPDATE ' \
                                                                                            '"time" should be same'
            assert data_active.find_one({'bid': bid})['time_update'] > test_record_first_update_time[spider], \
            'time_update should be changed in UPDATE'



if __name__ == '__main__':
    unittest.main()
