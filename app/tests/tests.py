import unittest
from app import app
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
from app.forms import LoginForm

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

if __name__ == '__main__':
    unittest.main()