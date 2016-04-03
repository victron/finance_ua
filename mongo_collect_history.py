from mongo_start import history, db, data_active, aware_times
from datetime import datetime, timedelta
from common_spider import current_datetime_tz, local_tz, main_currencies, operations
from parse_minfin import minfin_history
from nbu import NbuJson, auction_results, auction_get_dates
import statistics


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
        return None
    document = dict(input_document)
    db_update = aware_times(document['currency'])

    # delete some fields from temp document before inserting it
    currency = document.pop('currency').upper()
    time = document.pop('time')
    if document['source'] == 'nbu_auction':
        source = document.pop('source')
        db_update.update_one({'time': time},
                           {'$set': {source + '.' + field: document[field] for field in document}}, upsert=True)
    else:
        # source = document.pop('source')
        db_update.update_one({'time': time}, {'$set': document}, upsert=True)


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

def last_hour_stat(collection: data_active) -> dict:
    """
    result of document

    { "_id" : { "$oid" : "57015b77f0bccb05021e8182"} ,
    "time" : { "$date" : "2016-04-03T18:00:00.000Z"} ,
    "buy" : 25.92 ,  # median from range
    "source" : "h_stat" ,
    "sell" : 26.05 , # median from range
    "buy_rates" : [ 25.95 , 25.7 , 25.7 , 25.9 , 25.95 , 25.95] ,
    "sell_rates" : [ 26.05 , 26.03 , 26.1]}
    """
    update_time = collection.find_one({}, {'time_update': True, '_id': False})['time_update']
    stop_time = update_time.replace(minute=0, second=0, microsecond=0)
    start_time = stop_time - timedelta(hours=1)
    location = 'Киев'
    source = 'h_stat'
    pipeline = [{'$match': {'location': location,
                            '$and': [{'time': {'$gte': start_time}}, {'time': {'$lt': stop_time}}]}},
                {'$group': {'_id': {'operation': '$operation', 'currency': '$currency'},
                            'rates': {'$push':  '$rate'}}},
                {'$project': {'_id': False, 'operation': '$_id.operation', 'currency': '$_id.currency', 'rates': '$rates'}}]

    command_cursor = collection.aggregate(pipeline)

    def form_output_doc(document):
        document[document['operation']] = round(statistics.median(document['rates']), 2)
        document[document['operation'] + '_rates'] = document['rates']
        del document['operation']
        del document['rates']
        document['source'] = source
        document['time'] = stop_time
        return document
    return [form_output_doc(doc) for doc in command_cursor]



if __name__ == '__main__':
    # auction_dates = set()
    # for year in ['2014', '2015', '2016']:
    #     auction_dates.update(auction_get_dates(datetime.strptime(year, '%Y')))
    # for doc in minfin_history('USD', datetime(2016, 3, 31)):
    #     insert_history(doc)
    #     insert_history(NbuJson().rate_currency_date(doc['currency'], doc['time']))
    #     if doc['time'] in auction_dates:
    #         insert_history(auction_results(doc['time']))
    for currency in main_currencies:
        for operation in operations:
            for doc in last_hour_stat(data_active):
                insert_history(doc)






