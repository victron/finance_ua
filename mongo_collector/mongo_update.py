from pymongo.errors import DuplicateKeyError

from app import mongo_logging
from mongo_collector.mongo_start import data_active, records, news
from spiders import berlox, finance_ua, parse_minfin
from spiders.common_spider import current_datetime_tz, datetime
from spiders.filters import location, currency, operation, filter_or
from spiders.minfin import minfin_headlines
from spiders.news_minfin import parse_minfin_headlines
from tools.mytools import timer
# import multiprocessing.dummy as multiprocessing
import multiprocessing

from functools import reduce
# TODO:
# - delete some fields, before saving into history
# + delete from data_active all records without "time_update"
# - for minfin, if time grate then current - set yesterday date

time_periods = range(8, 20)

@timer('[EXE_TIME] >>>>')
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
            mongo_logging.debug('history insert={}'.format(result.acknowledged))
        except DuplicateKeyError as e:
            dublicate_count += 1
            mongo_logging.debug('duplicate found={}'.format(str(e)))
    return inserted_count, dublicate_count

@timer()
def mongo_update_active(docss: list, time: datetime):
    for document in docss:
        document['time_update'] = time
        key = {'bid': document['bid'], 'time': document['time'], 'source': document['source']}
        try:
            result = data_active.replace_one(key, document, upsert=True)  # upsert used to insert a new document if a matching document does not exist.
            mongo_logging.debug('update result acknowledged={}, '
                                'upserted_id={}'.format(result.acknowledged, result.upserted_id))
        except:
            print(document)
            print(docss)
            raise

def func(f_api, f_fetch):
    return f_api(f_fetch)


@timer('[EXE_TIME] >>>>')
def update_lists() -> int:
    update_time = current_datetime_tz()
    spiders_lists = ((parse_minfin.data_api_minfin, parse_minfin.get_triple_data),
                     (finance_ua.data_api_finance_ua, finance_ua.fetch_data),
                     (berlox.data_api_berlox, berlox.fetch_data),)
    # AttributeError: Can't pickle local object 'update_db.<locals>.<lambda>'
    # doc_set = reduce(lambda x, y: x + y, pool.map(lambda spider: spider[0](spider[1]), spiders))
    output_lists = multiprocessing.Queue()
    alias_lists = lambda param, queue: queue.put(param[0](param[1]))
    # pool = multiprocessing.Pool()  # default == number of CPUs cores
    # doc_set = reduce(lambda x, y: x + y, pool.map(func, spiders))
    processes_lists = [multiprocessing.Process(target=alias_lists, args=(spider, output_lists))
                       for spider in spiders_lists]

    for process in processes_lists:
        process.start()
    # pool.close()
    # pool.join()
    for process in processes_lists:
        process.join(0)
    doc_set_lists = reduce(lambda x, y: x + y, [output_lists.get() for _ in processes_lists])
    # -------- single process -----------
    # for doc_set in [finance_ua.data_api_finance_ua(finance_ua.fetch_data),
    #                 parse_minfin.data_api_minfin(parse_minfin.get_triple_data),
    #                 berlox.data_api_berlox(berlox.fetch_data)]:
    mongo_insert_history(doc_set_lists, records)
    mongo_update_active(doc_set_lists, update_time)
    # delete old records and records without 'time_update'
    result = data_active.delete_many({'$or': [{'time_update': {'$lt': update_time}}, {'time_update': None}]})
    return result.deleted_count

@timer()
def update_news() -> tuple:
    update_time = current_datetime_tz()
    spiders_news = (parse_minfin_headlines, minfin_headlines)
    output_news = multiprocessing.Queue()
    alias_news = lambda param, queue: queue.put(param())
    processes_news = [multiprocessing.Process(target=alias_news, args=(news_site, output_news))
                      for news_site in spiders_news]
    for process in processes_news:
        process.start()
    for process in processes_news:
        process.join(0)
    doc_set_news = reduce(lambda x, y: x + y, [output_news.get() for _ in processes_news])
    # in return inserted_count, duplicate_count
    return mongo_insert_history(doc_set_news, news)



def get_selection() -> (set, set, set, set):
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
