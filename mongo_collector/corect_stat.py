from mongo_collector.mongo_start import DATABASE
from datetime import datetime, timedelta
from spiders.parse_minfin import minfin_history
from spiders.nbu import auction_get_dates, NbuJson, auction_results
from mongo_collector.mongo_collect_history import insert_history
import logging
from collections import namedtuple

#!!!!!!!!!! on FreBSD, I still don't know how to instal pandas for py35
import pandas as pd


logger = logging.getLogger()



def remove_time(collection: str, source: str):
    result_cursor = DATABASE[collection].find({'source': source})
    for doc in result_cursor:
        logger.debug('input doc => {}'.format(doc))
        new_date = doc['time'].replace(hour=0)
        logger.debug('new time field= {}'.format(new_date))
        result = DATABASE[collection].update_one({'_id': doc['_id']}, {'$set': {'time': new_date}})
        logger.info('matched= {}, modified= {}'.format(result.matched_count, result.modified_count))


def add_field_to_news(collection: str = 'news'):
    filter = {'source': 'mf', 'time_auction': {'$ne': None}}
    result_cursor = DATABASE[collection].find(filter)
    for doc in result_cursor:
        logger.debug('input doc => {}'.format(doc))
        new_field = datetime(year=doc['time'].year, month=doc['time'].month, day=doc['time'].day)
        logger.debug('new time field= {}'.format(new_field))
        result = DATABASE[collection].update_one({'_id': doc['_id']}, {'$set': {'time_stat': new_field}})
        logger.info('matched= {}, modified= {}'.format(result.matched_count, result.modified_count))


def correct_news(collection: str = 'news'):
    filter = {'source': 'mf', 'time_auction': {'$ne': None}}
    result_cursor = DATABASE[collection].find(filter)
    for doc in result_cursor:
        logger.debug('input doc => {}'.format(doc))
        new_date = doc['time_auction'].replace(hour=0)
        logger.debug('new time field= {}'.format(new_date))
        result = DATABASE[collection].update_one({'_id': doc['_id']}, {'$set': {'time_auction': new_date}})
        logger.info('matched= {}, modified= {}'.format(result.matched_count, result.modified_count))


def get_missing_stat(currency: str):
    """
    going though db, and insert missing stat for main currencies,
    from external source if internal missing
    :param currency: 'USD', 'EUR'
    :return: namedtuple('result', ['currency', 'days_summ', 'in_db', 'inserted', 'errors'])
    """
    function_result = namedtuple('result', ['currency', 'days_summ', 'in_db', 'inserted', 'errors'])
    if currency == 'RUB':
        return function_result(currency, None, None, None, None)
    collection = DATABASE[currency]
    pipeline = [{'$match': {'$or': [{'source': 'd_ext_stat'}, {'source': 'd_int_stat'}]}},
                {'$group': {'_id': None, 'min_time': {'$min': '$time'}}},
                {'$project': {'_id': False, 'min_time': '$min_time'}}]
    command_cursor = collection.aggregate(pipeline)
    if command_cursor.alive:
        first_daily_stat = command_cursor.next()['min_time']
        start_day = first_daily_stat
        stop_day = datetime.now() - timedelta(days=1)
    else:
        return function_result(currency, None, None, None, None)
    minfin_data = minfin_history(currency, stop_day)
    minfin_data = pd.DataFrame(minfin_data,
                               index=[i['time'] for i in minfin_data],
                               columns=['buy', 'sell'])
    logger.debug('pandas data= {}'.format(minfin_data))
    days_summ, in_db, inserted, errors = 0, 0, 0, 0
    while start_day <= stop_day:
        result_cursor = collection.find_one({'$or': [{'source': 'd_ext_stat'}, {'source': 'd_int_stat'}],
                                                       'time': start_day})
        if result_cursor is not None:
            start_day += timedelta(days=1)
            days_summ += 1
            in_db += 1
            continue
        elif result_cursor is None:
            document = {}
            document['time'] = start_day
            document['source'] = 'd_ext_stat'
            day = start_day.replace(hour=17)
            try:
                document['buy'] = minfin_data.loc[day]['buy']
                document['sell'] = minfin_data.loc[day]['sell']
            except KeyError:
                logger.debug('there are no key with date= {}'.format(day))
                start_day += timedelta(days=1)
                days_summ += 1
                errors += 1
                continue
            logger.debug('inserting document= {}'.format(document))
            result = collection.update_one({'time': start_day}, {'$set': document}, upsert=True)
            if result.modified_count <= 0:
                logger.debug('inserting error')
                errors += 1
            else:
                logger.debug('inserted')
                inserted += 1
        start_day += timedelta(days=1)
        days_summ +=1
    return function_result(currency, days_summ, in_db, inserted, errors)


def get_missing_nbu_auction():
    """
    going though db, and inserting missing NBU auction
    :return: namedtuple('result', ['days_summ', 'auc_in_db', 'inserted', 'errors'])
    """
    function_result = namedtuple('result', ['days_summ', 'auc_in_db', 'inserted', 'errors'])
    collection = DATABASE['USD']
    pipeline = [{'$match': {'$or': [{'source': 'd_ext_stat'}, {'source': 'd_int_stat'}]}},
                {'$group': {'_id': None, 'min_time': {'$min': '$time'}}},
                {'$project': {'_id': False, 'min_time': '$min_time'}}]
    command_cursor = collection.aggregate(pipeline)
    if command_cursor.alive:
        first_daily_stat = command_cursor.next()['min_time']
        start_day = first_daily_stat
        stop_day = datetime.now() - timedelta(days=1)
    else:
        return function_result(None, None, None, None)
    # get NBU auction dates
    auction_dates = set()
    for year in ['2014', '2015', '2016']:
        auction_dates.update(auction_get_dates(datetime.strptime(year, '%Y')))
    days_summ, auc_in_db, inserted, errors = 0, 0, 0, 0
    while start_day <= stop_day:
        if start_day not in auction_dates:
            start_day += timedelta(days=1)
            days_summ += 1
            continue
        else:
            result_cursor = collection.find_one({'time': start_day})
            if result_cursor is None:
                logger.debug('error in request for date= {}'.format(start_day))
                start_day += timedelta(days=1)
                days_summ += 1
                errors += 1
                continue
            else:
                if 'nbu_auction' in result_cursor:
                    logger.debug('auction in db for date= {}'.format(start_day))
                    start_day += timedelta(days=1)
                    days_summ += 1
                    auc_in_db += 1
                    continue
                else:
                    insert_history(auction_results(start_day))
                    logger.debug('inserting stat for date= {}'.format(start_day))
                    start_day += timedelta(days=1)
                    days_summ += 1
                    inserted += 1
    return function_result(days_summ, auc_in_db, inserted, errors)




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # collection = 'RUB'
    # source = 'd_int_stat'
    # # remove_time(collection, source)
    # correct_news()

    # print(get_missing_stat('EUR'))

    print(get_missing_nbu_auction())
