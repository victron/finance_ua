from pymongo import MongoClient
import sys

# DB for test, in test_businessinsider used mock on test DB
if 'unittest' in list(sys.modules.keys()):
    DB_NAME = 'TEST'
else:
    DB_NAME = 'fin_ua'

mongo_host = 'localhost'


# client = MongoClient()
# client = MongoClient('localhost', 27017)
# client = MongoClient('mongodb://localhost:27017/')
# db = app.config['DATABASE_DATA']

# TODO: move DB to separete server
client = MongoClient(mongo_host, 27017, connect=False,
                     serverSelectionTimeoutMS=10000)

DATABASE = client[DB_NAME]

simple_rest_secret = 'temp_secret'

user_agent = '"Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)"'
headers = {'user-agent': user_agent}

# waite time before collect info
sleep_time = 300
proxy_is_used = False
news_type = 'currency'
# table settings
table_column_size = (5, 3, 4, 5, 7, 5, 30, 15, 1)