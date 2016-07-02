from pymongo import MongoClient

DB_NAME = 'fin_ua'
client = MongoClient(connect=False)
DATABASE = client[DB_NAME]
