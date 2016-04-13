from pymongo import MongoClient

DB_NAME = 'fin_ua'
DATABASE = MongoClient()[DB_NAME]
