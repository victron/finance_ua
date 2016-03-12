import pymongo
import json
from pymongo import MongoClient
from filters import location, currency, operation, filter_or
location = 'Киев'
currency = 'USD'

client = MongoClient()
db = client['fin_ua']
records = db['records']

result = records.find({'location' : location, 'currency' : currency, 'operation' : operation })
for p in result:
    print(p)
