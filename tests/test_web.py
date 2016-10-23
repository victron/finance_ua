import json
import unittest

from pymongo import MongoClient
from werkzeug.security import generate_password_hash

import mongo_collector

from data.formats import stat_format, active_format

# copy list in tuple !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
original_list = tuple(dict(doc) for doc in stat_format)


class Login(unittest.TestCase):

    def setUp(self):
        # data need to put in DB before 'app' context creation
        mongo_collector.DATABASE['USD'].insert_many(stat_format)
        mongo_collector.DATABASE['data_active'].insert_many(active_format)

        # context create after inserting data in DB
        # bbecause some function looking on data before rendering page
        from app import app
        from app.views_func import reformat_for_js

        app.config['TESTING'] = True
        app.config['CSRF_ENABLED'] = False
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DB_NAME'] = 'TESTS'
        app.config['DATABASE'] = MongoClient()[app.config['DB_NAME']]
        app.config['USERS_COLLECTION'] = app.config['DATABASE']['users']
        # it's better to link context in class
        self.app = app.test_client()
        self.reformat_for_js = reformat_for_js
        app.config['USERS_COLLECTION'].insert_one({'_id': 'admin', 'password': generate_password_hash('default', 'sha256')})


    def tearDown(self):
        MongoClient().drop_database('TESTS')

    # def test_empty_db(self):
    #     rv = self.app.get('/')
    #     assert 'No entries here so far' in rv.data

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_login_logout(self):
        rv = self.login('admin', 'default')
        assert 'Logged in successfully' in rv.data.decode()
        rv = self.logout()
        assert 'You were logged out' in rv.data.decode()
        rv = self.login('adminx', 'default')
        assert 'Wrong username or password' in rv.data.decode()
        rv = self.login('admin', 'defaultx')
        assert 'Wrong username or password' in rv.data.decode()


class TestViews(Login):
    def test_api_history(self):
        self.login('admin', 'default')

        resp = self.app.get('/api/history/usdd')
        assert resp.status_code == 404, 'wrong staus code, for wrong request'

        resp = self.app.get('/api/history/usd', follow_redirects=True)
        assert resp.status_code == 200, 'wrong staus code'
        data = json.loads(resp.data.decode())
        original = [self.reformat_for_js(doc) for doc in original_list]
        self.assertEqual(data['USD'], original)


    def test_lists(self):
        self.login('admin', 'default')
        resp = self.app.get('/lists')
        assert resp.status_code == 200, 'wrong staus code'

        assert '063xxx-x7-58' in resp.data.decode()
        assert not '380979650955' in resp.data.decode(), 'wrong default filter'
        resp = self.app.post('/lists', data = {'locations': 'Киев', 'currencies': '--USDh--', 'operations': 'sell',
                                               'sources': 'all', 'text': '',
                                               'sort_order-0-sort_field': 'rate',
                                               'sort_order-0-sort_direction': 'ASCENDING',
                                               'sort_order-1-sort_field': 'time',
                                               'sort_order-1-sort_direction': 'ASCENDING',
                                               'sort_order-2-sort_field': 'None',
                                               'sort_order-2-sort_direction': 'ASCENDING'})

        assert 'Not a valid choice' in resp.data.decode(), 'Form validation not works'
        resp = self.app.post('/lists', data = {'locations': 'Киев', 'currencies': 'USD', 'operations': 'sell',
                                               'sources': 'all', 'text': '',
                                               'sort_order-0-sort_field': 'rate',
                                               'sort_order-0-sort_direction': 'ASCENDING',
                                               'sort_order-1-sort_field': 'time',
                                               'sort_order-1-sort_direction': 'ASCENDING',
                                               'sort_order-2-sort_field': 'None',
                                               'sort_order-2-sort_direction': 'ASCENDING'})
        assert '063xxx-x7-58' in resp.data.decode()
        assert '380688731157' in resp.data.decode()
        assert resp.data.decode().find('380688731157') > resp.data.decode().find('063xxx-x7-58'), 'wrong sort order'


if __name__ == '__main__':
    unittest.main()
