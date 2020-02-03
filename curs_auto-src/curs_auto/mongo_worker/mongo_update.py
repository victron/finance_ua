from pymongo.errors import DuplicateKeyError


from curs_auto.mongo_worker.mongo_start import data_active, records, news, DATABASE
# from spiders import berlox, finance_ua, parse_minfin, news_minfin, minfin
# from spiders.common_spider import current_datetime_tz, datetime
# from spiders.filters import location, currency, operation, filter_or
# from tools.mytools import timer
# import multiprocessing.dummy as multiprocessing
import multiprocessing
from collections import namedtuple

from functools import reduce
import logging

logger = logging.getLogger('curs.mongo_collector.mongo_update')
# TODO:
# - delete some fields, before saving into history
# + delete from data_active all records without "time_update"
# - for minfin, if time grate then current - set yesterday date

time_periods = range(8, 20)


# @timer(logging=logger)
def mongo_insert_history(docs: list, collection):
    duplicate_count = 0
    inserted_count = 0
    for d in docs:
        # The document to insert. Must be a mutable mapping type.
        # If the document does not have an _id field one will be added automatically.
        # temp dictionary for insert_one
        temp_doc = dict(d)
        try:
            result = collection.insert_one(temp_doc)
            inserted_count += 1
            logger.debug('history insert={}'.format(result.acknowledged))
        except DuplicateKeyError as e:
            duplicate_count += 1
            logger.debug('duplicate found={}'.format(str(e)))
    result = namedtuple('result', ['inserted_count', 'duplicate_count'])
    return result(inserted_count, duplicate_count)


def mongo_replace_docs(docs: list, collection, upsert=True) -> tuple:
    """
    :param docs:
    :param collection:
    :param upsert=True: If True, perform an insert if no documents match the filter.
    :return: matched_count, modified_count, new_count (number of new doc)
    """
    matched_count = 0
    modified_count = 0
    new_count = 0
    for doc in docs:
        temp_doc = dict(doc)
        result = collection.replace_one({'_id': temp_doc['_id']}, temp_doc, upsert)
        matched_count += result.matched_count
        modified_count += result.modified_count
        if result.matched_count == result.modified_count != 1:
            # INFO: it's need to test what mongo return if inserting new doc, this should works in any case
            new_count += 1
    return matched_count, modified_count, new_count


# @timer(logging=logger)
def mongo_add_fields(docs: list, collection=None):
    """
    if doc not exist in collection - insert
    if doc exist and same fields - do nothing
    if doc exist, but some fields missing - add those fields
    :param docs: list of docs
    :param collection: pymongo collection, or get collection from source field
    :return: tuple: (inserted_count, modified_count, duplicate_count)
    """
    duplicate_count = 0
    inserted_count = 0
    modified_count = 0
    for d in docs:
        # should works if collection exists
        if collection is None:
            try:
                collection = DATABASE[d['source']]
            except:
                print('problem with mapping \'source\' in doc with colection')
                raise
        find_doc = dict({})
        find_doc = collection.find_one({'_id': d['_id']})
        if bool(find_doc):
            replace_doc = False
            for field in d:
                if (field != 'source') and (field not in find_doc):
                    find_doc[field] = d[field]
                    replace_doc = True
            if replace_doc:
                collection.replace_one({'_id': d['_id']}, find_doc)
                modified_count += 1
            else:
                duplicate_count += 1
        else:
            temp_doc = dict(d)
            result = collection.insert_one(temp_doc)
            inserted_count += 1
            logger.debug('history insert={}'.format(result.acknowledged))
    logger.info('inserted_count={}, modified_count={}, duplicate_count={}'
                .format(inserted_count, modified_count, duplicate_count))
    return inserted_count, modified_count, duplicate_count


def get_selection() -> (set, set, set, set):
    selections_result = data_active.find({}, {'location': 1, 'operation': 1, 'currency': 1, 'source': 1, '_id': 0})
    locations = set()
    operations = set()
    currencies = set()
    sources = set()
    for i in selections_result:
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
