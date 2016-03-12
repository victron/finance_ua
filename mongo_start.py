import pymongo
from pymongo import MongoClient
from berlox import data_api_berlox

client = MongoClient()
# client = MongoClient('localhost', 27017)
# client = MongoClient('mongodb://localhost:27017/')

db = client['fin_ua']
records = db['records']
rusult = records.insert_many(data_api_berlox())
