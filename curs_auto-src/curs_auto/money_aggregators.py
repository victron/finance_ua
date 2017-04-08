import logging
from datetime import datetime, timedelta
from time import sleep
from curs_auto.mongo_worker.mongo_start import aggregators
from curs_auto.mongo_worker.mongo_update import mongo_insert_history
from curs_auto.mongo_worker.meta import collection_state, update_meta
from curs_auto.spiders_legacy.nbu import NbuJson
from collections import namedtuple

logger = logging.getLogger('curs.mongo_collector.money_aggregators')


def collect_nbu_aggregators():
    aggregators_state = collection_state(aggregators, timedelta(days=10))
    result_tuple = namedtuple('collect_nbu_aggregators', ['inserted_count', 'duplicate_count'])
    result = result_tuple(0, 0)
    if not aggregators_state.actual:
        if aggregators_state.create_time is None:
            start_date = datetime(year=2003, month=1, day=1)
        else:
            start_date = aggregators_state.update_time
        logger.debug('last update_time= {}'.format(aggregators_state.update_time))
        year = start_date.year
        while start_date <= aggregators_state.current_time:
            docs = NbuJson().agregators_per_month(start_date)
            sleep(1)
            if len(docs) > 0:
                logger.debug('inserting {}'.format(docs))
                result_insert = mongo_insert_history(docs, aggregators)
            else:
                result_insert = result_tuple(0, 0)
            month = (start_date.month + 1) % 12
            logger.debug('start_date= {}'.format(start_date))
            if month == 0:
                month = 12
                year += 1
                start_date = start_date.replace(month=month, year=year - 1)
            else:
                start_date = start_date.replace(month=month, year=year)
            result = result_tuple(inserted_count=result.inserted_count + result_insert.inserted_count,
                                  duplicate_count=result.inserted_count + result_insert.duplicate_count)
    if result.inserted_count > 0:
        update_meta(aggregators_state, aggregators)
    logger.info('inserted= {}, duplicated= {}'.format(result.inserted_count, result.duplicate_count))
    return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    collect_nbu_aggregators()