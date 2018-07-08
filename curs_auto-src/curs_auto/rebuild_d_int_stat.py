from datetime import datetime, timedelta
from curs_auto.mongo_worker.mongo_start import DATABASE
from bson import ObjectId
from pymongo.collection import ReturnDocument
import logging
from curs_auto.spiders_legacy.nbu import auction_get_dates, NbuJson, auction_results
from curs_auto.mongo_worker.mongo_collect_history import insert_history
logger = logging.getLogger('curs_auto.mongo_collector.mongo_collect_history')


# def correct_h_int_stat():
#     """
#     one run function to add in "h_int_stat" docs fields buy_val and sell_val based on buy_vales and sell_vales
#
#     :return:
#     """
#     start_day = datetime(2014, 1, 1)
#     stop_day = datetime.utcnow()
#     collections = [DATABASE[currency] for currency in ['USD', 'EUR', 'RUB']]
#     num = 0
#     for collection in collections:
#         command_cursor = collection.find({"source": "h_int_stat"})
#         for doc in command_cursor:
#             update_doc = {}
#             if doc.get('sell_val') is None and doc.get('sell_vales') is not None:
#                 print('sell_val=', doc.get('sell_val'), 'sell_vales=', doc.get('sell_vales'))
#                 update_doc['sell_val'] = doc['sell_vales']
#             if doc.get('buy_val') is None and doc.get('buy_vales') is not None:
#                 update_doc['buy_val'] = doc['buy_vales']
#             if update_doc != {}:
#                 for k in ['sell_val', 'buy_val']:
#                     if k not in update_doc:
#                         continue
#                     for id, i in enumerate(update_doc[k]):
#                         if type(i) == str:
#                             update_doc[k][id] = int(i.replace(' ', ''))
#                     update_doc[k] = sum(update_doc[k])
#                 print('update===', update_doc)
#                 result = collection.find_one_and_update({'_id': ObjectId(doc['_id'])}, {'$set': update_doc },
#                                                return_document=ReturnDocument.AFTER)
#                 print(result)
#     num += 1
#     print('updated docs= {}'.format(num))
#
#
#
# def daily_stat(day: datetime, collection) -> dict:
#     """
#     create day statistics based on hourly data
#     currently put in stat data for business hours
#     :param day: datetime, date for aggregation hour statistic
#     :param collection:
#     :return:
#     """
#     business_time = (day.replace(hour=9, minute=0), day.replace(hour=17, minute=59))
#     full_time = (day.replace(hour=0, minute=0), day.replace(hour=23, minute=59))
#     time = business_time
#     source = 'd_int_stat'
#     pipeline = [{'$match': {'source': 'h_int_stat',
#                             '$and': [{'time': {'$gte': time[0]}}, {'time': {'$lt': time[1]}}]}},
#                 {'$group': {'_id': None, 'sell': {'$avg': '$sell'}, 'sell_rates': {'$push':  '$sell'},
#                                          'buy': {'$avg': '$buy'}, 'buy_rates': {'$push':  '$buy'},
#                             'sell_val': {'$sum': '$sell_val'}, 'buy_val': {'$sum': '$buy_val'}}},
#                 {'$project': {'_id': False, 'buy': '$buy', 'sell': '$sell', 'sell_rates': '$sell_rates',
#                               'buy_rates': '$buy_rates', 'sell_val': '$sell_val', 'buy_val': '$buy_val'}}]
#     command_cursor = collection.aggregate(pipeline)
#
#     def form_output_doc(document):
#         if collection.name == 'RUB':
#             round_dig = 4
#         else:
#             round_dig = 2
#         document['sell'] = round(document['sell'], round_dig)
#         document['buy'] = round(document['buy'], round_dig)
#         document['source'] = source
#         document['time'] = time[1].replace(hour=0, minute=0)
#         return document
#     # actually one document
#     try:
#         result_doc = [form_output_doc(doc) for doc in command_cursor][0]
#     except IndexError:
#         return {}
#     document = dict(result_doc)
#     time = document.pop('time')
#     collection.update_one({'time': time}, {'$set': document}, upsert=True)
#     return result_doc


def correct_nbu_stat():
    start_day = datetime(year=2017, month=12, day=4)
    stop_day = datetime(year=2018, month=4, day=7)
    # stop_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    day = start_day
    while day <= stop_day:
        print('day= {}'.format(day))
        if day in auction_get_dates(day):
            print('day in auction')
            result = auction_results(day)
            print('result= {}'.format(result))
            insert_history(result)
        day += timedelta(days=1)


# to execute
# cd /opt/curs/curs_auto/lib/python3.6/site-packages
# python3.6 -c "import curs_auto.rebuild_d_int_stat; curs_auto.rebuild_d_int_stat.correct_h_int_stat()"
