from mongo_start import history
from datetime import datetime
from common_spider import current_datetime_tz
from parse_minfin import minfin_history
from nbu import NbuJson, auction_results, auction_get_dates


def insert_history(input_document: dict):
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


if __name__ == '__main__':
    auction_dates = set()
    for year in ['2014', '2015', '2016']:
        auction_dates.update(auction_get_dates(datetime.strptime(year, '%Y')))
    for doc in minfin_history('USD', datetime(2016, 3, 27)):
        insert_history(doc)
        insert_history(NbuJson().rate_currency_date(doc['currency'], doc['time']))
        if doc['time'] in auction_dates:
            insert_history(auction_results(doc['time']))







