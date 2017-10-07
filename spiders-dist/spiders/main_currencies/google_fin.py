# collect data from finance.google.com
# https://stackoverflow.com/questions/46243360/google-api-changed-for-data-from-google-finance
# https://finance.google.com/finance/getprices?p=2d&i=60&f=d,o,h,l,c,v&q=AAPL

# http "https://finance.google.com/finance/getprices?p=30d&f=d,c&q=USDCHF"

import csv
import logging
from datetime import datetime, timedelta, timezone
import requests

from spiders.main_currencies.commons import mongo_multi_column, sympols
from spiders.mongo_start import main_currencies

logger = logging.getLogger(__name__)



def google_get(currency: str, period: int = 2, interval: int = 86400, only_date: bool = True) -> list:
    """
    get currency rate from finance.google.com
    some old url url = strcat('http://www.google.com/finance/historical?q=',symbol,'&startdate=',startDateStr,'&enddate=',endDateStr,'&output=csv');
    :param currency:
    :param period: days
    :param r_interval: seconds
    :return:
    """
    url = "https://finance.google.com/finance/getprices"
    period = str(period) + "d"
    r_interval = str(interval)
    # format ===> date, open, high, low, close, volume
    # format = "d,o,h,l,c,v"
    format = "d,c,v"
    quarter = sympols[currency][0]
    if quarter is None:
        logger.warning("no data for {} in GOOGLE".format(currency))
        return []
    payload = {"p": period, "i": r_interval, "f": format, "q": quarter}
    try:
        r = requests.get(url, params=payload)
    except requests.ConnectionError as e:
        logger.error("connection error with {}".format(url))
        raise
    except Exception as e:
        logger.error("request error: {}".format(e))
        raise

    response = r.text.splitlines()
    reader = csv.reader(response)
    output = []
    for row in enumerate(reader):
        logger.debug("processing row from csv= {}".format(row))
        if row[0] < 7:
            logger.debug("row number {} < 7; do nothing, continue".format(row[0]))
            continue
        elif row[0] == 7:
            logger.debug("processing row number 7")
            # test first symbol should be "a" in 'a1506815880'
            if row[1][0][0] != "a":
                logger.error("wrong format of first data string")
                logger.error("requested data for {} in {}".format(currency, period))
                raise TypeError("first letter should be \"a\"")
            else:
                first_date = row[1][0][1:]
                first_date = datetime.utcfromtimestamp(int(first_date))
                # first_date = first_date.date()
                rate = float(row[1][1])
                output.append({"time": first_date,
                               currency: rate})
        else:
            logger.debug("row=", row[0])
            seconds = int(row[1][0]) * interval
            date = first_date + timedelta(seconds=seconds)
            rate = float(row[1][1])
            output.append({"time": date,
                           currency: rate})

    if len(output) < 1:
        logger.error("no data from GOOGLE for {} in {}".format(currency, period))
        raise IndexError("no data from GOOGLE")

    if only_date:
        for doc in output:
            doc["time"] = doc["time"].replace( hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

    return output


def collect_main_currency_stat(currency: str, interval: int = 86400,
                               start_date: datetime = datetime(year=2017, month=9, day=2, tzinfo=timezone.utc)) -> list:
    """
    collect stat for last available day
    :param currency:
    :param interval: 86400 == 1day
    :param start_date:
    :return:
    """
    today = datetime.now(timezone.utc)
    match = {'$or': [{'source': 'd_ext_stat'}, {'source': 'd_int_stat'}],
              currency: True}
    projection = {'_id': False, 'time': True}
    pipeline = [{'$match': match},
                {'$group': {'_id': None, 'max_time': {'$max': '$time'}}},
                {'$project': {'_id': False, 'max_time': '$max_time'}}]
    command_cursor = main_currencies.aggregate(pipeline)
    if command_cursor.alive:
        newest_daily_stat = command_cursor.next()['max_time']
    else:
        # normaly should not be used
        newest_daily_stat = start_date
        logger.warning("no records in \"main_currencies\" collection, "
                       "set newest_daily_stat= ".format(newest_daily_stat))

    pipeline = [{'$match': match},
                {'$group': {'_id': None, 'min_time': {'$min': '$time'}}},
                {'$project': {'_id': False, 'min_time': '$min_time'}}]
    command_cursor = main_currencies.aggregate(pipeline)
    if command_cursor.alive:
        oldest_daily_stat = command_cursor.next()['min_time']
    else:
        oldest_daily_stat = today
        logger.warning("no records in \"main_currencies\" collection, "
                       "set oldest_daily_stat= {}".format(oldest_daily_stat))
    logger.error("oldest_daily_stat= {}".format(oldest_daily_stat))
    logger.error("newest_daily_stat= {}".format(newest_daily_stat))

    if oldest_daily_stat > start_date:
        intervals_to_collect = today - timedelta(days=1) - start_date
        logger.info("oldest date for {} is {}; collecting from {}, intervals= {}".format(currency,
                                                                                         oldest_daily_stat,
                                                                                         start_date,
                                                                                         intervals_to_collect))
    else:
        if newest_daily_stat + timedelta(days=1) == today:
            logger.info("newest date for {} is {}, nothing to do".format(currency, newest_daily_stat))
            return []
        else:
            intervals_to_collect = today - timedelta(days=1) - newest_daily_stat
            logger.info("newest date for {} is {}, collecting {} intervals".format(currency, newest_daily_stat,
                                                                                    intervals_to_collect))

    return google_get(currency, intervals_to_collect)


def main_currencies_collect(currencies: list):
    """
    update main currencies according to input list
    :param currencies:
    :return:
    """
    #TODO: async io
    result_dict = {}
    for currency in currencies:
        result = mongo_multi_column(collect_main_currency_stat(currency), main_currencies)
        logger.info("currency {}; new docs= {}, modif docs ={}"
                    .format(currency, result.new_doc_count, result.modified_count))

        result_dict[currency] = result
    return result_dict



