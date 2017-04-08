from falcon import testing
import json
from time import sleep
import subprocess
import logging
from unittest.mock import patch
from pymongo import MongoClient
from datetime import date

from spiders.rest.app import api
from spiders.parameters import simple_rest_secret
from common import mock_requests, DATA_PATH

secret = {'secret': simple_rest_secret,
          'responce': ['ok', 'nok'],
          }

logger = logging.getLogger(__name__)

DB_NAME = 'TEST'
client = MongoClient()
DATABASE = client[DB_NAME]
TEST_DATABASE = client[DB_NAME]

class InitTestCase(testing.TestCase):
    def setUp(self):
        super(InitTestCase, self).setUp()
        self.app = api

    def tearDown(self):
        client.drop_database(DB_NAME)

class TestRest(InitTestCase):
    def test1_get_wrong(self):
        result = self.simulate_get('/wrong')
        self.assertEqual(result.status_code, 404)

        result = self.simulate_get('/command')
        doc = {'description': 'not JSON', 'title': 'Bad request'}
        self.assertEqual(result.json, doc, 'should be body with secret')

        body = json.dumps(secret)
        doc = {'description': 'not JSON', 'title': 'Bad request'}
        result = self.simulate_get('/command', body=body)
        self.assertEqual(result.json, doc, 'check headers "application/json" ')


    def test2_get(self):
        headers = {'content_type': 'application/json'}
        body = json.dumps(secret)
        doc = {'answ': 'ok'}
        result = self.simulate_get('/command', body=body, headers=headers)
        self.assertEqual(result.json, doc, 'GET; body should be in json with authentication, '
                                           'in headers content_type: application/json')

    def tes3_post_wrong(self):
        result = self.simulate_post('/wrong')
        self.assertEqual(result.status_code, 404)

        result = self.simulate_post('/command')
        doc = {'description': 'not JSON', 'title': 'Bad request'}
        self.assertEqual(result.json, doc, 'should be body with secret')

        body = json.dumps(secret)
        doc = {'description': 'not JSON', 'title': 'Bad request'}
        result = self.simulate_get('/command', body=body)
        self.assertEqual(result.json, doc, 'check headers "application/json" ')

        body = '"fake" : json'
        headers = {'content_type': 'application/json'}
        doc = {'description': 'JSONDecodeError', 'title': 'Bad request'}
        result = self.simulate_get('/command', body=body, headers=headers)
        self.assertEqual(result.json, doc, 'check headers "application/json" ')

    def test4_post_integral(self):
        headers = {'content_type': 'application/json'}
        body_init = dict(secret)
        body_init.update({'update': 'fake'})
        body = json.dumps(body_init)
        doc = {'description': 'wrong value in "update",  update= fake', 'title': 'Bad request'}
        result = self.simulate_post('/command', body=body, headers=headers)
        self.assertEqual(result.json, doc, 'checking allowed "update"')

    # TODO: only test for 'news' done; 'lists' api not tested
    @patch('spiders.news_minfin.requests.get', side_effect=mock_requests)
    def test5_post_integral_news(self, requests_fun):
        headers = {'content_type': 'application/json'}
        body_init = dict(secret)
        body_init.update({'update': 'news'})
        body = json.dumps(body_init)
        doc = {'duplicate_count': 0, 'inserted_count': 196, 'resp': 'ok', 'update': 'news'}
        result = self.simulate_post('/command', body=body, headers=headers)
        self.assertEqual(result.json, doc, 'checking allowed "update"')

    def test6_post_DB_down(self):
        # stopping MONGODB
        mongo_start = ['sudo', 'systemctl', 'start', 'mongod']
        mongo_stop = ['sudo', 'systemctl', 'stop', 'mongod']
        stop = subprocess.run(mongo_stop, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sleep(1)

        headers = {'content_type': 'application/json'}
        body_init = dict(secret)
        body_init.update({'update': 'news'})
        body = json.dumps(body_init)
        doc = {'code': 15, 'description': 'DB down', 'title': 'Service Unavailable'}
        result = self.simulate_post('/command', body=body, headers=headers)
        assert result.json == doc, 'In case DB down'

        # start back MONGO
        start = subprocess.run(mongo_start, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sleep(1)

    @patch('spiders.parameters.DATABASE', TEST_DATABASE)    # mock DB only for this test
    @patch('spiders.commodities.businessinsider.requests.get', side_effect=mock_requests)
    @patch('spiders.commodities.businessinsider.requests.post', side_effect=mock_requests)
    @patch('spiders.commodities.graintrade.requests.get', side_effect=mock_requests)
    def test7_commudities(self, get_f, post_f, graitrade_f):
        from spiders.mongo_start import commodities
        from spiders.commodities.update_history_logic import update_commudities_collection

        headers = {'content_type': 'application/json'}
        body_init = dict(secret)
        body_init.update({'update': 'commodities', 'list': ['iron_ore',]})
        body = json.dumps(body_init)

        # http://www.voidspace.org.uk/python/mock/examples.html#partial-mocking
        with patch('spiders.commodities.update_history_logic.date') as mock_date:
            mock_date.today.return_value = date(2017, 3, 28)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            # update_commudities_collection(['Iron Ore', ])
            # find_all = commodities.find()
            # with open(DATA_PATH + 'update_commudities_collection.data', 'rb') as f:
            #     etalon_dict = pickle.load(f)
            # self.assertEqual(etalon_dict, [i for i in find_all])
            result = self.simulate_post('/command', body=body, headers=headers)
            print(result.text)



