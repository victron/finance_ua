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
    logger.debug(f'collection {aggregators.name}: update_time= {aggregators_state.update_time}, '
                 f'create_time= {aggregators_state.create_time}')
    if not aggregators_state.actual:
        logger.info(f'collection {aggregators.name} in actual= {aggregators_state.actual}')
        if aggregators_state.create_time is None or aggregators_state.update_time is None:
            start_date = datetime(year=2003, month=1, day=1)
        else:
            start_date = aggregators_state.update_time
        while start_date <= aggregators_state.current_time:
            logger.info(f'setting start_date= {start_date} for updating collection {aggregators.name}')
            year = start_date.year
            docs = NbuJson().agregators_per_month(start_date)
            if 'error' in docs:
                months = 1
                start_date = datetime(year=start_date.year + (start_date.month + months) // 12,
                                      month=start_date.month + (start_date.month + months) % 12,
                                      day=start_date.day)
                sleep(5)
                continue
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
    else:
        logger.info(f'collection {aggregators.name} in actual= {aggregators_state.actual}')
    if result.inserted_count > 0:
        update_meta(aggregators_state, aggregators)
    logger.info('inserted= {}, duplicated= {}'.format(result.inserted_count, result.duplicate_count))
    return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    collect_nbu_aggregators()