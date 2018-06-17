import logging
import statistics
from datetime import datetime, timedelta

from pymongo.errors import DuplicateKeyError

from curs_auto.bonds import update_bonds
from curs_auto.mongo_worker.mongo_start import history, data_active, DATABASE
from curs_auto.spiders_legacy.common_spider import local_tz
from curs_auto.spiders_legacy.nbu import auction_get_dates, NbuJson, auction_results
from curs_auto.spiders_legacy.parse_minfin import minfin_history
from curs_auto.spiders_legacy.ukrstat import import_stat

logger = logging.getLogger('curs_auto.mongo_collector.mongo_collect_history')

def insert_history_embedded(input_document: dict):
    """
    {'time':
     'USD': {'buy':
             'sell':
             'nbu_rate':
             'nbu_auction':{

     'EUR': {
    :param document:
    :return:
    """
    if input_document == {}:
        return None
    document = dict(input_document)
    # delete some fields from temp document before inserting it
    currency = document.pop('currency').upper()
    time = document.pop('time')
    # time = time.replace(tzinfo=current_datetime_tz().tzinfo)
    # time = time.replace(hour=17, minute=0, second=0, microsecond=0)
    if document['source'] == 'nbu_auction':
        source = document.pop('source')
        history.update_one({'time': time},
                           {'$set': {currency + '.' + source + '.' + field: document[field] for field in document}},
                           upsert=True)
    else:
        source = document.pop('source')
        history.update_one({'time': time},
                           {'$set': {currency + '.' + field: document[field] for field in document}},
                           upsert=True)
        # embedded document


def insert_history(input_document: dict):
    """
    insert document into collection based on 'source' field
    {'time':
     'buy':
     'sell':
     'nbu_rate':
     'nbu_auction':{'sell':
                    'buy':
    :param document:
    :return:
    """
    if input_document == {} or input_document['currency'] not in ['USD', 'EUR', 'RUB']:
        logger.warning('empty document, nothing to insert')
        return None
    document = dict(input_document)
    db_update = DATABASE[document['currency']]

    # delete some fields from temp document before inserting it
    currency = document.pop('currency').upper()
    # delete "time", in any case pymongo.errors.DuplicateKeyError when call update
    time = document.pop('time')
    if (document['source'] == 'nbu_auction') or (document['source'] == 'nbu'):
        source = document.pop('source')
        logger.debug('source= {}, time= {}'.format(source, time))
        logger.debug('document = {}'.format(document))
        if any(document):
            db_update.update_one({'time': time},
                               {'$set': {source + '.' + field: document[field] for field in document}}, upsert=True)
    else:
        # source = document.pop('source')
        time = datetime.combine(time, datetime.min.time())
        logger.debug('calling update collection= {}'.format(db_update))
        logger.debug('time= {}, document= {}'.format(time, document))
        result = db_update.update_one({'time': time}, {'$set': document}, upsert=True)
        logger.debug('matched_count= {}, modified_count= {}'.format(result.matched_count,
                                                                    result.modified_count))



def insert_history_currency(input_document: dict):
    """
    insert or update document in collection based on currency field
    :param input_document:
    :return:
    """
    if input_document == {} or input_document['currency'] not in ['USD', 'EUR', 'RUB']:
        return None
    document = dict(input_document)
    db_update = DATABASE[document['currency']]
    currency = document.pop('currency').upper()
    time = document.pop('time')
    source = document.pop('source')
    result = db_update.update_one({'time': time}, {'$set': document}, upsert=True)
    return result



def create_hour_stat_doc(currency: str, operation: str, collection: data_active) -> dict:
    """
    collect history for all hour periods in active data. Max, min, avg
    problem with rates which out of standard deviation
    """
    update_time = collection.find_one({}, {'time_update': True, '_id': False})['time_update']
    location = 'Киев'
    # operation = 'sell'
    source = 'hourly_stat'
    pipeline = [{'$match': {'location': location, 'currency': currency, 'operation': operation}},
                {'$sort': {'time': 1}}, # sort for get first and last rate in period
                {'$group': {'_id': {'hour_date': {'$dateToString': {'format': '%Y-%m-%d_%H', 'date': "$time"}}},
                            'min': {'$min': '$rate'}, 'max': {'$max': '$rate'}, 'avg': {'$avg': '$rate'},
                            'open': {'$first': '$rate'}, 'close': {'$last': '$rate'}}},
                {'$project': {'_id': 0, 'time': '$_id.hour_date', operation + '_close': '$close', operation: '$avg',
                              operation+'_open': '$open', operation+'_min': '$min', operation+'_max': '$max',
                              'source': { '$literal': source }, 'currency': { '$literal': currency }}}]

    def doc_correction(document: dict, operation: str):
        document['time'] = datetime.strptime(document['time'], '%Y-%m-%d_%H').replace(tzinfo=local_tz)
        document[operation] = round(document[operation], 2)
        return document

    command_cursor = collection.aggregate(pipeline)
    return [ doc_correction(doc, operation) for doc in command_cursor]


def create_hour_stat_doc2(currency: str, operation: str, collection: data_active) -> dict:
    """
     collect history for all hour periods in active data. Median only.
    """
    location = 'Киев'
    source = 'hourly_stat'
    pipeline = [{'$match': {'location': location, 'currency': currency, 'operation': operation}},
                {'$group': {'_id': {'hour_date': {'$dateToString': {'format': '%Y-%m-%d_%H', 'date': "$time"}}},
                            'rates': {'$push': '$rate'}}},
                {'$project': {'_id': False, 'time': '$_id.hour_date', operation + '_rates': '$rates'}}]

    def form_output_doc(document):
        document['time'] = datetime.strptime(document['time'], '%Y-%m-%d_%H')
        try:
            document[operation] = round(statistics.median(document[operation + '_rates']), 2)
        except statistics.StatisticsError:
            document[operation] = None
        document['currency'] = currency
        document['source'] = source
        return document

    command_cursor = collection.aggregate(pipeline)
    return [form_output_doc(doc) for doc in command_cursor]


def hour_stat(collection: data_active) -> list:
    """
    forms hour statistics
    result document format:
    { "_id" : { "$oid" : "57015b77f0bccb05021e8182"} ,
    "time" : { "$date" : "2016-04-03T18:00:00.000Z"} ,
    "buy" : 25.92 ,  # median from range
    "source" : "h_stat" ,
    "sell" : 26.05 , # median from range
    "buy_rates" : [ 25.95 , 25.7 , 25.7 , 25.9 , 25.95 , 25.95] ,
    "sell_rates" : [ 26.05 , 26.03 , 26.1],
    "currency": "USD"}
    """
    update_time = collection.find_one({}, {'time_update': True, '_id': False})['time_update']
    # stop_time = update_time.replace(minute=0, second=0, microsecond=0)
    # assume that it called at the end of hour
    stop_time = datetime.now(tz=local_tz)
    # stop_time write into db, minute=59 means stat data
    stop_time = stop_time.replace(minute=59, second=0, microsecond=0)
    start_time = stop_time - timedelta(hours=1)
    location = 'Киев'
    source = 'h_int_stat'
    pipeline = [{'$match': {'location': location,
                            '$and': [{'time': {'$gte': start_time}}, {'time': {'$lt': stop_time}}]}},
                {'$group': {'_id': {'operation': '$operation', 'currency': '$currency'},
                            'rates': {'$push':  '$rate'}, 'vales': {'$push': '$amount'}}},
                {'$project': {'_id': False, 'operation': '$_id.operation', 'currency': '$_id.currency',
                              'rates': '$rates', 'vales': '$vales'}}]

    command_cursor = collection.aggregate(pipeline)

    def form_output_doc(document):
        document[document['operation']] = round(statistics.median(document['rates']), 2)
        document[document['operation'] + '_val'] = sum(document['vales'])
        document[document['operation'] + '_rates'] = document['rates']
        document[document['operation'] + '_vales'] = document['vales']
        del document['operation']
        del document['rates']
        del document['vales']
        document['source'] = source
        document['time'] = stop_time
        return document
    return [form_output_doc(doc) for doc in command_cursor]


def ext_history(currency=None):
    """
    collects currencies rates from minfin, nbu rates, nbu auction
    :return:
    """
    if currency is None:
        currencies = ['USD', 'EUR']
    else:
        currencies = [currency]
    auction_dates = set()
    for year in ['2014', '2015', '2016']:
        auction_dates.update(auction_get_dates(datetime.strptime(year, '%Y')))
    for currency in currencies:
        for doc in minfin_history(currency, datetime.now()):
            if DATABASE[doc['currency']].find({'time': doc['time']}).count() == 0:
            # db.somName.find({"country":{"$exists":True}}).count()
            #     insert_history(doc)
                insert_history(NbuJson().rate_currency_date(doc['currency'], doc['time']))
                if doc['time'] in auction_dates:
                    insert_history(auction_results(doc['time']))
                insert_history(dict(doc, source='d_ext_stat'))


def hourly_history() -> None:
    """
    collects hourly stat from data_active, and put in currency collections
    :return: None
    """
    for doc in hour_stat(data_active):
        insert_history(doc)


def daily_stat(day: datetime, collection) -> dict:
    """
    create day statistics based on hourly data
    currently put in stat data for business hours
    :param day: datetime, date for aggregation hour statistic
    :param collection:
    :return:
    """
    business_time = (day.replace(hour=9, minute=0), day.replace(hour=17, minute=59))
    full_time = (day.replace(hour=0, minute=0), day.replace(hour=23, minute=59))
    time = business_time
    source = 'd_int_stat'
    pipeline = [{'$match': {'source': 'h_int_stat',
                            '$and': [{'time': {'$gte': time[0]}}, {'time': {'$lt': time[1]}}]}},
                {'$group': {'_id': None, 'sell': {'$avg': '$sell'}, 'sell_rates': {'$push':  '$sell'},
                                         'buy': {'$avg': '$buy'}, 'buy_rates': {'$push':  '$buy'},
                            'sell_val': {'$sum': '$sell_val'}, 'buy_val': {'$sum': '$buy_val'}}},
                {'$project': {'_id': False, 'buy': '$buy', 'sell': '$sell', 'sell_rates': '$sell_rates',
                              'buy_rates': '$buy_rates', 'sell_val': '$sell_val', 'buy_val': '$buy_val'}}]
    command_cursor = collection.aggregate(pipeline)

    def form_output_doc(document):
        if collection.name == 'RUB':
            round_dig = 4
        else:
            round_dig = 2
        logger.debug('document= {}'.format(document))
        if not (any(document['sell_rates']) and any(document['buy_rates'])):
            logger.warning('rates missing in stat; len(document[\'sell_rates\'])= {},'
                           'len(document[\'buy_rates\']= {}'.format(document['sell_rates'],
                                                                    document['buy_rates']))
            return {}
        document['sell'] = round(document['sell'], round_dig)
        document['buy'] = round(document['buy'], round_dig)
        document['source'] = source
        document['time'] = time[1].replace(hour=0, minute=0)
        return document
    # actually one document
    try:
        result_doc = [form_output_doc(doc) for doc in command_cursor][0]
    except IndexError or TypeError:
        return {}
    # TODO: need to correct (bad code)
    logger.debug('result_doc= {}'.format(result_doc))
    if result_doc == {}:
        logger.warning('document empty nothing to insert, result_doc= {}'.format(result_doc))
        return {}
    document = dict(result_doc)
    time = document.pop('time')
    collection.update_one({'time': time}, {'$set': document}, upsert=True)
    return result_doc

def agg_daily_stat():
    """
    collects daily statistic for internal hourly stat or external stat
    :return:
    """
    # find missing stat period
    # assume call done at the end of day
    def ext_stat(date):
        if currency == 'RUB':
            return None
        for doc in minfin_data:
            if doc['time'].date() == date.date():
                logger.debug('inserting doc = {}'.format(doc))
                logger.info('inserting doc as \'d_ext_stat\'')
                insert_history(dict(doc, source='d_ext_stat'))
                break

    if datetime.now().hour >= 18:
        stop_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        stop_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)

    for currency in ['USD', 'EUR', 'RUB']:
        collection = DATABASE[currency]
        # save data localy to limit acces to external website
        if currency != 'RUB':
            # no ext data for RUB
            minfin_data = minfin_history(currency, stop_day)

        filter = {'$or': [{'source': 'd_ext_stat'}, {'source': 'd_int_stat'}]}
        projection = {'_id': False, 'time': True}
        pipeline = [{'$match': {'$or': [{'source': 'd_ext_stat'}, {'source': 'd_int_stat'}]}},
                    {'$group': {'_id': None, 'max_time': {'$max': '$time'}}},
                     {'$project': {'_id': False, 'max_time': '$max_time'}}]
        command_cursor = collection.aggregate(pipeline)
        if command_cursor.alive:
            last_daily_stat = command_cursor.next()['max_time']
            start_day = last_daily_stat + timedelta(days=1)
            #  for manual insert external stat
            # start_day = datetime(year=2017, month=9, day=19)
        elif currency == 'RUB':
            pipeline = [{'$match': {'$or': [{'source': 'h_int_stat'}]}},
                        {'$group': {'_id': None, 'min_time': {'$min': '$time'}}},
                        {'$project': {'_id': False, 'min_time': '$min_time'}}]
            command_cursor = collection.aggregate(pipeline)
            start_day = command_cursor.next()['min_time']
        else:
            if currency != 'RUB':
                ext_history(currency)
            continue

        # days = []
        start_day = start_day.replace(hour=0, minute=0, second=0, microsecond=0)
        day = start_day
        while day <= stop_day:
            # days.append(start_day)

            logger.info('daily stat currency= {} day= {}'.format(currency, day))
        # for day in days:
            day_stat = daily_stat(day, collection)

            # if hourly stat less then 5
            # overwrite internal daily stat by external stat data
            if day_stat:
                if len(day_stat['sell_rates']) < 5:
                    logger.debug('using ext_stat')
                    ext_stat(day)
            else:
                logger.debug('using ext_stat')
                ext_stat(day)
            # insert NBU rate
            insert_history_currency(NbuJson().rate_currency_date(currency, day))
            # insert auction_results
            if day in auction_get_dates(day):
                insert_history(auction_results(day))
            day += timedelta(days=1)

def ukrstat(start_date: datetime) -> tuple:
    duplicate_count = 0
    inserted_count = 0
    end_date = datetime.now()
    date = start_date
    while date < end_date.replace(month=(end_date.month - 1), day=1, hour=0, minute=0, second=0, microsecond=0):
        try:
            insert_result = DATABASE['ukrstat'].insert_one(import_stat(date))
            inserted_count += 1
        except DuplicateKeyError as e:
            print('duplicate found={}'.format(str(e)))
            duplicate_count += 1
        # protection from None in import_stat(date)
        except TypeError:
            pass
        if date.month // 12 == 0:
            date = date.replace(month=(date.month + 1))
        else:
            date = date.replace(year=(date.year + 1), month=1)
    return inserted_count, duplicate_count


if __name__ == '__main__':
    # # collect currencies rates from minfin.ua and nbu auction results
    # ext_history()
    # # internal_history()
    # # TODO: minor: validate counts of records from ovdp_all and by currency
    # # mongo_insert_history(NbuJson().ovdp_all(), bonds)
    #
    # for currency in ['UAH', 'USD', 'EUR']:
    #     print(hourly_history())
    #     doc_list = NbuJson().ovdp_currency(currency)
    #     # in json from NBU 'amount' is number of papers, value of paper == 1000
    #     doc_list = [dict(doc, amount=doc['amount'] * 1000) for doc in doc_list]
    #     if currency == 'USD':
    #         doc_list += external_loans_USD
    #     mongo_insert_history(doc_list, aware_times('bonds_' + currency))
    #     times_from_bonds = []
    #     for doc in doc_list:
    #         if 'coupon_date' not in doc:
    #             times_from_bonds += [{'time': doc[field]} for field in ['repaydate', 'paydate', 'auctiondate']]
    #         else:
    #             # currently coupon_date available only for infor for external borrows
    #             # TODO: borrows for different currencies, if needed
    #             coupon_dates = [datetime.strptime(date+'.'+str(year), '%d.%m.%Y').replace(hour=17, tzinfo=local_tz)
    #                             for date in doc['coupon_date']
    #                             for year in range(2016, int(doc['repaydate'].strftime('%Y'))+1)]
    #             times_from_bonds += [{'time': doc['repaydate']}]
    #             # Be careful with ref, after delete colection ref still exist on None object
    #             times_from_bonds += [{'time': coupon_date, 'bonds': [DBRef('bonds_' + currency, doc['_id'])]}
    #                                  for coupon_date in coupon_dates]
    #     for cur in ['USD', 'EUR']:
    #         mongo_insert_history(times_from_bonds, aware_times(cur))
    #
    # # ----------- colect ukrstat -------------------
    # start_date = datetime.strptime('2006-01', '%Y-%m')
    # # result = ukrstat(start_date)
    # result = mongo_add_fields(ukrstat_().saldo(), ukrstat_db)
    # print('inserted= {}, duplicated= {}'.format(result[0], result[1]))
    # # ================================================
    # agg_daily_stat()
    #
    # add values to h_int_stat based on buy_vales and sell_values


    pass












