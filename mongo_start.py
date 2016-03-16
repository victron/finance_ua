import pymongo
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from finance_ua import data_api_finance_ua
from parse_minfin import data_api_minfin
from berlox import data_api_berlox

client = MongoClient()
# client = MongoClient('localhost', 27017)
# client = MongoClient('mongodb://localhost:27017/')

db = client['fin_ua']
records = db['records']


def mongo_insert(data: list):
    for d in data:
        try:
            records.insert_one(d)
        except DuplicateKeyError as e:
            print('duplcate found={}'.format(str(e)))

if 'unique_keys' not in records.index_information().keys():
    records.create_index([('bid', pymongo.ASCENDING),
                          ('time', pymongo.ASCENDING),
                          ('source', pymongo.ASCENDING)], unique=True, name='unique_keys')

for data in [data_api_berlox, data_api_finance_ua, data_api_minfin]:
    mongo_insert(data)

