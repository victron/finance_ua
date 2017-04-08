from pymongo import MongoClient
import sys

if 'unittest' in list(sys.modules.keys()):
    DB_NAME = 'TESTS'
else:
    DB_NAME = 'fin_ua'

client = MongoClient(connect=False)
DATABASE = client[DB_NAME]