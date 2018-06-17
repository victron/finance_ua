from pymongo import MongoClient
import sys

if 'unittest' in list(sys.modules.keys()):
    DB_NAME = 'TESTS'
else:
    DB_NAME = 'fin_ua'

mongo_host = 'localhost'

client = MongoClient(mongo_host, 27017, connect=True,
                     serverSelectionTimeoutMS=10000)
DATABASE = client[DB_NAME]