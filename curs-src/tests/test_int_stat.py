import unittest
import pymongo
from datetime import datetime
from pymongo import MongoClient
from tests.data.stats import d_int_stat_result, h_int_stat_lite
from mongo_collector.mongo_collect_history import daily_stat

DB_NAME = 'TESTS'
client = MongoClient()
DATABASE = client[DB_NAME]


usd = DATABASE['USD']

class Ovdp(unittest.TestCase):

    def setUp(self):
        usd.create_index([('time', pymongo.DESCENDING)], name='history_time', unique=True)
        usd.insert_many(h_int_stat_lite)

    def tearDown(self):
        MongoClient().drop_database(DB_NAME)

    def test_daily_stat(self):
        day = datetime.strptime("2016-11-27T00:00", '%Y-%m-%dT%H:%M')
        day_stat = daily_stat(day, usd)
        assert day_stat == d_int_stat_result, 'day_stat= {}  d_int_stat_result= {}'.format(day_stat, d_int_stat_result)


if __name__ == '__main__':
    unittest.main()

