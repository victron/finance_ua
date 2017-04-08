import unittest
import logging
from pymongo import MongoClient
from datetime import datetime

from spiders.mongo_start import data_active
from save_test_pages import files, operations, currencies, filemap, data_path, gen_files_del
from spiders.parse_minfin import get_triple_data, data_api_minfin
from spiders.mongo_start import records, data_active

from spiders.parallel import parent
from spiders.common_spider import local_tz


logger = logging.getLogger()
# logging.basicConfig(level=logging.DEBUG)

DB_NAME = 'TEST'
client = MongoClient()
DATABASE = client[DB_NAME]


# def set_test_environ(fn):
#     # decorate fun. Set fixet test_filemap_dict argument in fn
#     def wraper(*args, **kwargs):
#         return fn(*args, test_filemap_dict=files)
#     return wraper


def set_test_environ(fn=get_triple_data, dic=files):
    # decorate fun. Set fixet test_filemap_dict argument in fn
    def wraper(*args, files=dic):
        return fn(*args, test_data=files)
    return wraper


class MongoTests(unittest.TestCase):
    def setUp(self):
        self.get_triple_data_test = set_test_environ(get_triple_data)
        self.get_triple_data_test_del = set_test_environ(get_triple_data, gen_files_del())
    #
    def tearDown(self):
        MongoClient().drop_database(DB_NAME)

    def test_insert(self):
        result = parent([(data_api_minfin, self.get_triple_data_test),], 'records')
        print(result)
        first_insert_time = datetime.now(tz=local_tz)
        assert result == (308, 0), 'wrong parent return, etalon is 308 records'
        assert result[0] == records.find({}).count(), 'function insert report wrong'
        assert records.find({}).count() == 308, 'should be 308 in "records"'
        assert data_active.find({}).count() == 308, 'should be 308 in "data_active"'
        assert data_active.find({}).count() == records.find({}).count(), 'after first insert "records" and "data_active"' \
                                                                         'should be equal'
        assert records.find({'session': True}).count() == 6, 'should be 6 cookies in "records"'
        assert data_active.find({'session': True}).count() == 6, 'should be 6 cookies in "data_active"'
        test_record_time = data_active.find_one({'bid': '32166583'})['time']
        assert data_active.find_one({'bid': '32166583'})['time'] < \
               data_active.find_one({'bid': '32166583'})['time_update']
        test_record_first_update_time = data_active.find_one({'bid': '32166583'})['time_update']

        # second insert of same data
        result = parent([(data_api_minfin, self.get_triple_data_test), ], 'records')
        assert result == (308, 0), 'wrong parent return, etalon is 308 records'
        assert data_active.find_one({'bid': '32166583'})['time'] == test_record_time, 'after UPDATE "time" should be same'
        assert data_active.find_one({'bid': '32166583'})['time_update'] > test_record_first_update_time, \
            'time_update should be changed in UPDATE'
        assert data_active.find({}).count() == 308, 'should be 308 in "data_active"'
        assert records.find({}).count() == 308 * 2, 'should be 616 in "records"'
        assert first_insert_time < data_active.find_one()['time_update'], 'time_update is not newer'

        # 3-d inssert of data with deleted records
        result = parent([(data_api_minfin, self.get_triple_data_test_del), ], 'records')
        print(result)
        assert result == (302, 6), 'wrong parent return, etalon is 302 records'
        assert result[0] == data_active.find({}).count(), 'function insert report wrong'
        assert data_active.find({}).count() == 302, 'should be 302 in "records"'
        assert data_active.find({}).count() != records.find({}).count(), 'after insert "records" and "data_active"' \
                                                                         'should not be equal'
        assert data_active.find({'session': True}).count() == 6, 'should be 6 cookies in "data_active"'
        assert data_active.find_one({'bid': '32166583'})['time'] == test_record_time, 'after UPDATE "time" should be same'
        assert data_active.find_one({'bid': '32166583'})['time_update'] > test_record_first_update_time, \
            'time_update should be changed in UPDATE'


if __name__ == '__main__':
    unittest.main()

