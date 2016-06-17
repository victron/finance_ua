from pymongo import MongoClient
# TODO: put configs in one place
CSRF_ENABLED = True
# WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'
# MONGODB_SETTINGS = {'DB': "my_tumble_log"}

OPENID_PROVIDERS = [
    { 'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id' },
    { 'name': 'Yahoo', 'url': 'https://me.yahoo.com' },
    { 'name': 'AOL', 'url': 'http://openid.aol.com/<username>' },
    { 'name': 'Flickr', 'url': 'http://www.flickr.com/<username>' },
    { 'name': 'MyOpenID', 'url': 'https://www.myopenid.com' }]

DB_NAME = 'users'
DATABASE = MongoClient(connect=False)[DB_NAME]
USERS_COLLECTION = DATABASE['users']




DEBUG = True



