import pymongo
from bson.codec_options import CodecOptions
# from app import app
from curs_auto.mongo_worker import DATABASE
from curs_auto.spiders_legacy.common_spider import local_tz

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


# -------- news ---------------
news = DATABASE['news']
# information about collections
meta = aware_times('meta')
swaps = DATABASE['swaps']
aggregators = DATABASE['aggregators']
