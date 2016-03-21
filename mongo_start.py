from pymongo import MongoClient
import pymongo


client = MongoClient()
# client = MongoClient('localhost', 27017)
# client = MongoClient('mongodb://localhost:27017/')

db = client['fin_ua']
records = db['records']
data_active = db['data_active']

# records.create_index([('bid', pymongo.ASCENDING),
#                       ('time', pymongo.ASCENDING),
#                       ('source', pymongo.ASCENDING)], unique=True, name='unique_keys')

data_active.create_index([('bid', pymongo.ASCENDING),
                          ('time', pymongo.ASCENDING),
                          ('source', pymongo.ASCENDING)], name='acctive_key')

data_active.create_index([('time_update', pymongo.ASCENDING)], name='update_time_key')
data_active.create_index([('comment', pymongo.TEXT)], default_language='russian', name='comment_text')


