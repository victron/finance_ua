import pymongo
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from finance_ua import data_api_finance_ua
from parse_minfin import data_api_minfin
from berlox import data_api_berlox
from common_spider import current_datetime_tz, datetime

client = MongoClient()
# client = MongoClient('localhost', 27017)
# client = MongoClient('mongodb://localhost:27017/')

db = client['fin_ua']
records = db['records']
data_active = db['data_active']


def mongo_insert_history(docs: list):
    for d in docs:
        # The document to insert. Must be a mutable mapping type.
        # If the document does not have an _id field one will be added automatically.
        # temp dictionary for insert_one
        temp_doc = dict(d)
        try:
            result = records.insert_one(temp_doc)
            print('history insert={}'.format(result.acknowledged))
        except DuplicateKeyError as e:
            print('duplcate found={}'.format(str(e)))


def mongo_update_active(docss: list, time: datetime):
    for document in docss:
        document['time_update'] = time
        key = {'bid': document['bid'], 'time': document['time'], 'source': document['source']}
        try:
            result = data_active.replace_one(key, document, upsert=True)  # upsert used to insert a new document if a matching document does not exist.
            print('update result acknowledged={}, upserted_id={}'.format(result.acknowledged, result.upserted_id))
        except:
            print(document)
            print(docss)
            raise


records.create_index([('bid', pymongo.ASCENDING),
                      ('time', pymongo.ASCENDING),
                      ('source', pymongo.ASCENDING)], unique=True, name='unique_keys')

data_active.create_index([('bid', pymongo.ASCENDING),
                          ('time', pymongo.ASCENDING),
                          ('source', pymongo.ASCENDING)], name='acctive_key')

data_active.create_index([('time_update', pymongo.ASCENDING)], name='update_time_key')

update_time = current_datetime_tz()
for doc_set in [data_api_finance_ua, data_api_minfin, data_api_berlox]:
    mongo_insert_history(doc_set)
    mongo_update_active(doc_set, update_time)

result = data_active.delete_many({'time_update': {'$lt': update_time }})
print('deleted from active={}'.format(result.deleted_count))
