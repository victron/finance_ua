from mongo_collector.mongo_start import DATABASE
from datetime import datetime
import logging

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


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    collection = 'RUB'
    source = 'd_int_stat'
    # remove_time(collection, source)
    correct_news()