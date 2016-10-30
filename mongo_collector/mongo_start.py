import pymongo
from bson.codec_options import CodecOptions
# from app import app
from mongo_collector import DATABASE
from spiders.common_spider import local_tz

# TODO:
# - move DBs init in config

# client = MongoClient()
# client = MongoClient('localhost', 27017)
# client = MongoClient('mongodb://localhost:27017/')

# db = app.config['DATABASE_DATA']

records = DATABASE['records']
history = DATABASE['history']   # TODO: check if needed

# wraper for collection tz_aware and tzinfo
aware_times = lambda collection: DATABASE[collection].with_options(codec_options=CodecOptions(tz_aware=True,
                                                                                              tzinfo=local_tz))
# data_active = db['data_active']
data_active = aware_times('data_active') # pymongo 3.2.2
news = aware_times('news')
bonds = aware_times('bonds')
ukrstat = aware_times('ukrstat')
bonds_auction = aware_times('bonds_auction')
bonds_payments = aware_times('bonds_payments')

records.create_index([('bid', pymongo.ASCENDING),
                      ('time', pymongo.ASCENDING),
                      ('source', pymongo.ASCENDING)], unique=True, name='unique_keys')

data_active.create_index([('bid', pymongo.ASCENDING),
                          ('time', pymongo.ASCENDING),
                          ('source', pymongo.ASCENDING)], name='acctive_key')

data_active.create_index([('time_update', pymongo.ASCENDING)], name='update_time_key')
data_active.create_index([('comment', pymongo.TEXT)], default_language='russian', name='comment_text')

# -------- news ---------------
news.create_index([
                  #  ('time', pymongo.ASCENDING),
                   ('href', pymongo.ASCENDING)], name='news_time', unique=True)
news.create_index([('headline', pymongo.TEXT)], default_language='russian', name='headline')

bonds_auction.create_index([('auctiondate', pymongo.ASCENDING),
                            ('auctionnum', pymongo.ASCENDING)], unique=True, name='bonds_auction')
bonds_payments.create_index([('bond', pymongo.ASCENDING),
                             ('time', pymongo.ASCENDING),
                             ('pay_type', pymongo.ASCENDING)], unique=True, name='payments')

history.create_index([('time', pymongo.DESCENDING)], name='history_time', unique=True)
for currency in ['USD', 'EUR', 'RUB']:
    DB = DATABASE[currency]
    DB.create_index([('time', pymongo.DESCENDING)], name='history_time', unique=True)
