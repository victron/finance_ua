import unittest
from collections import namedtuple
import pickle
import json
import logging
from os import path
from datetime import datetime, timedelta

from common import date_depends_time
from spiders.mongo_start import data_active
from spiders import parameters
from save_test_pages import files, operations, currencies, filemap, data_path
from spiders.parse_minfin import get_triple_data, data_api_minfin
from spiders.common_spider import local_tz

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

location = 'kiev'
user_agent = parameters.user_agent
headers = {'user-agent': user_agent}



def set_test_environ(fn):
    # decorate fun. Set fixet test_filemap_dict argument in fn
    def wraper(*args, **kwargs):
        return fn(*args, test_data=files)
    return wraper


def response_generator():
    # at that moment used only currency and  operation
    response = namedtuple('response', 'text cookies operation currency res_dict res_cookies')
    for operation in operations:
        for currency in currencies:
            key = filemap(currency=currency, operation=operation, source='m')
            filename = files[key]
            with open(filename.page, 'rb') as f:
                text = f.read().decode()
            with open(filename.cookie, 'rb') as f:
                cookies = pickle.load(f)
            with open(filename.parse_data, 'r') as f:
                res_dict = json.loads(f.read())
            with open(filename.parse_session, 'rb') as f:
                res_cookies = pickle.load(f)
            yield response(text=text, cookies=cookies, operation=operation, currency=currency,
                           res_dict=res_dict, res_cookies=res_cookies)

class ParseMinfin(unittest.TestCase):
    def setUp(self):

        self.response_generator = response_generator()
        self.get_triple_data_test = set_test_environ(get_triple_data) # get_triple_data with fixed karg test_filemap_dict=files

    def test_parser(self):
        for response in self.response_generator:
            # result = get_triple_data(response.currency, response.operation, files)
            result = self.get_triple_data_test(response.currency, response.operation)
            self.assertEqual(len(result[0]), len(response.res_dict), \
                'wrong data lenght get_triple_data= {}, etalon= {}, currency= {}, operation = {}'\
                    .format(len(result[0]), len(response.res_dict), response.currency, response.operation))
            assert result[0] == response.res_dict, 'result dict no equal etalon dict'
            assert result[1]['url'] == response.res_cookies['url'], 'wrong url in session param'
            assert result[1]['cookies'] == response.res_cookies['cookies'], 'not correctly saved cookies in etalons'

    # def test_single_data(self):
        result = data_api_minfin(self.get_triple_data_test)
        with open(data_path + 'minfinUA.data', 'rb') as f:
            result_etalon = pickle.load(f)

        result_etalon = list(map(date_depends_time, result_etalon))     # change date in etalon list
        self.assertEqual(result, result_etalon, 'wrong data in common API format; result= {}\n ' \
                                        'result_etalon= {}'.format(result, result_etalon))
        # with open(data_path + 'minfinUA.data', 'wb') as f:
        #     pickle.dump(result, f)

if __name__ == '__main__':
    unittest.main()