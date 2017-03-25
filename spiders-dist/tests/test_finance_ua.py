import unittest
import requests
import json
import pickle
from os import path
from datetime import datetime, timedelta

from common import date_depends_time
from spiders.finance_ua import fetch_data, data_api_finance_ua
from spiders.common_spider import local_tz

def set_tes_environ(fn, data):
    def wraper(*args):
        return fn(data)
    return wraper




data_path = path.join('data', 'pages', '')

class ParseFinanceUA(unittest.TestCase):
    def setUp(self):
        with open(data_path + 'financeUA.bin', 'rb') as f:
            data = f.read().decode()

        self.fetch_data_test = set_tes_environ(fetch_data, data)

    def test_parser(self):
        result = self.fetch_data_test()
        with open(data_path + 'financeUA.json', 'r') as f:
            dic = json.load(f)
        assert result == dic, 'fun fetch_data return wrog results'

        # convert in common API format
        result = data_api_finance_ua(self.fetch_data_test)
        with open(data_path + 'financeUA.data', 'rb') as f:
            docs = pickle.load(f)
        assert len(result) == len(docs), 'lenght results= {}, docs= {}'.format(len(result), len(docs))

        current_date = datetime.now().date()
        set_date_today = lambda doc: {**doc, **{'time': doc['time'].replace(year=current_date.year,
                                                                            month=current_date.month,
                                                                            day=current_date.day)}}
        docs = list(map(set_date_today, docs))       # change date in etalon list to today, for all!! docs
        assert result == docs, 'result not as espected result={},\n docs={}'.format(result, docs)



if __name__ == '__main__':
    unittest.main()