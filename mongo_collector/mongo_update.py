from pymongo.errors import DuplicateKeyError

from mongo_collector.mongo_start import data_active, records, news
from spiders import berlox, finance_ua, parse_minfin
from spiders.news_minfin import minfin_headlines

# from finance_ua import data_api_finance_ua
# from parse_minfin import data_api_minfin

# from berlox import data_api_berlox

from spiders.common_spider import current_datetime_tz, datetime
from spiders.filters import location, currency, operation, filter_or

# TODO:
# - delete some fields, before saving into history
# + delete from data_active all records without "time_update"
# - for minfin, if time grate then current - set yesterday date

time_periods = range(8, 20)

def mongo_insert_history(docs: list, collection):
    dublicate_count = 0
    inserted_count = 0
    for d in docs:
        # The document to insert. Must be a mutable mapping type.
        # If the document does not have an _id field one will be added automatically.
        # temp dictionary for insert_one
        temp_doc = dict(d)
        try:
            result = collection.insert_one(temp_doc)
            inserted_count += 1
            print('history insert={}'.format(result.acknowledged))
        except DuplicateKeyError as e:
            dublicate_count += 1
            print('duplicate found={}'.format(str(e)))
    return inserted_count, dublicate_count


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


def update_db() -> int:
    update_time = current_datetime_tz()
    for doc_set in [finance_ua.data_api_finance_ua(finance_ua.fetch_data),
                    parse_minfin.data_api_minfin(parse_minfin.get_triple_data),
                    berlox.data_api_berlox(berlox.fetch_data)]:
        mongo_insert_history(doc_set, records)
        mongo_insert_history(minfin_headlines(), news)
        mongo_update_active(doc_set, update_time)
    # delete old records and records without 'time_update'
    result = data_active.delete_many({'$or': [{'time_update': {'$lt': update_time}}, {'time_update': None}]})
    return result.deleted_count


def get_selection() -> (set, set, set):
    result = data_active.find({}, {'location': 1, 'operation': 1, 'currency': 1, 'source': 1, '_id': 0})
    locations = set()
    operations = set()
    currencies = set()
    sources = set()
    for i in result:
        locations.add(i.get('location', 'None'))
        operations.add(i.get('operation', 'None'))
        currencies.add(i.get('currency', 'None'))
        sources.add(i.get('source', 'None'))
    return locations, operations, currencies, sources



if __name__ == '__main__':
    result = data_active.find({'location': location, 'currency': currency, 'operation': operation,
                               '$text': {'$search': filter_or}})
    for p in result:
        print(p)
