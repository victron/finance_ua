import pymongo
from bson.codec_options import CodecOptions
from spiders.parameters import DATABASE
import logging

from spiders.common_spider import local_tz

logger = logging.getLogger(__name__)
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

bonds = DATABASE['bonds']
ukrstat = DATABASE['ukrstat']
bonds_auction = DATABASE['bonds_auction']
bonds_payments = DATABASE['bonds_payments']
news = DATABASE['news']
meta = aware_times('meta')
swaps = DATABASE['swaps']
aggregators = DATABASE['aggregators']
commodities = DATABASE['commodities']
numbers = aware_times('numbers')
contracts = aware_times('contracts')

try:
    numbers.create_index([('comment', pymongo.TEXT)], default_language='russian', name='comment_text')
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
    # information about collections

    swaps.create_index([('date', pymongo.ASCENDING),
                        ('period', pymongo.ASCENDING)], unique=True, name='swaps')

    aggregators.create_index([('date', pymongo.ASCENDING),
                              ('id_api', pymongo.ASCENDING),
                              ('k076txt', pymongo.ASCENDING)], unique=True, name='aggregators')

    for currency in ['USD', 'EUR', 'RUB']:
        DB = DATABASE[currency]
        DB.create_index([('time', pymongo.DESCENDING)], name='history_time', unique=True)

except pymongo.errors.ServerSelectionTimeoutError as e:
    logger.error('MONGO not ready; sckip index creating in case clean start - {}'.format(e))
finally:
    pass