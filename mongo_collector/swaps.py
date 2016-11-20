import logging
from datetime import datetime, timedelta
from time import sleep

from mongo_collector.mongo_start import swaps
from mongo_collector.mongo_update import mongo_insert_history
from spiders.nbu import NbuJson
from collections import namedtuple
from mongo_collector.meta import collection_state, update_meta, local_tz

logger = logging.getLogger('curs.mongo_collector.swaps')


def collect_nbu_swaps():
    swaps_state = collection_state(swaps, timedelta(hours=5))
    result_tuple = namedtuple('collect_nbu_swaps', ['inserted_count', 'duplicate_count'])
    result = result_tuple(0, 0)
    if not swaps_state.actual:
        if swaps_state.create_time is None:
            start_date = datetime(year=2015, month=12, day=28, tzinfo=local_tz)
        else:
            start_date = swaps_state.update_time

        output_docs = []
        logger.info('last update_time= {}'.format(swaps_state.update_time))
        while start_date <= swaps_state.current_time:
            for period in ['OVERNIGHT', '1WEEK', '2WEEKS', '1MONTH', '3MONTHS']:
                docs = NbuJson().swaps_per_date(start_date, period)
                sleep(1)
                if len(docs) > 0:
                    # workaround for 'OVERNIGHT' compact one dict from two
                    # if period == 'OVERNIGHT':
                    # if data in two dicts, merge it. delete fields with 0.0
                    if len(docs) > 1:
                        merged_doc = {}
                        for doc in docs:
                            merged_doc.update({key: val for key, val in doc.items() if val != 0})
                        output_doc = merged_doc
                    else:
                        output_doc = docs[0]
                    # output_doc['flag'] = 'raw'
                    output_docs.append(output_doc)
            if len(output_docs) > 0:
                logger.debug('inserting {}'.format(output_docs))
                result_insert = mongo_insert_history(output_docs, swaps)
            else:
                result_insert = result_tuple(0, 0)
            start_date += timedelta(days=1)
            result = result_tuple(inserted_count=result.inserted_count + result_insert.inserted_count,
                                  duplicate_count=result.duplicate_count + result_insert.duplicate_count)
    logger.info('inserted= {}, duplicated= {}'.format(result.inserted_count, result.duplicate_count))
    if result.inserted_count > 0:
        update_meta(swaps_state, swaps)
    return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    collect_nbu_swaps()