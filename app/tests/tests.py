import unittest
import mongo_collector
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
from formats import stat_format
import json

mongo_collector.DB_NAME = 'TESTS'
mongo_collector.DATABASE =  MongoClient()[mongo_collector.DB_NAME]
from app import app
# copy list in tuple !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
original_list = tuple(dict(doc) for doc in stat_format)


class TestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['CSRF_ENABLED'] = False
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DB_NAME'] = 'TESTS'
        app.config['DATABASE'] = MongoClient()[app.config['DB_NAME']]
        app.config['USERS_COLLECTION'] = app.config['DATABASE']['users']
        self.app = app.test_client()
        app.config['USERS_COLLECTION'].insert_one({'_id': 'admin', 'password': generate_password_hash('default', 'sha256')})

        mongo_collector.DATABASE['USD'].insert_many(stat_format)

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

    def test_api_history(self):
        self.login('admin', 'default')

        resp = self.app.get('/api/history/usdd')
        assert resp.status_code == 404, 'wrong staus code, for wrong request'

        resp = self.app.get('/api/history/usd', follow_redirects=True)
        assert resp.status_code == 200, 'wrong staus code'
        data = json.loads(resp.data.decode())
        octothorpe = lambda x, dictionary: x * -1 if dictionary['nbu_auction']['operation'] == 'buy' else x
        def reformat_for_js(doc):
            if 'nbu_auction' in doc:
                doc['amount_requested'] = octothorpe(doc['nbu_auction'].pop('amount_requested'), doc)
                doc['amount_accepted_all'] = octothorpe(doc['nbu_auction'].pop('amount_accepted_all'), doc)
                del doc['nbu_auction']
            doc['time'] = doc['time'].strftime('%Y-%m-%d_%H')
            return doc
        original = [ reformat_for_js(doc) for doc in original_list]
        self.assertEquals(data['USD'], original)





if __name__ == '__main__':
    unittest.main()
