# About: https://www.alphavantage.co/#about
# Docs:
# Reference: https://stackoverflow.com/questions/10040954/alternative-to-google-finance-api

import logging
from datetime import datetime, timedelta, timezone, time, date
import time as t
import requests
import pymongo

from spiders.main_currencies.commons import mongo_multi_column, sympols
from spiders.mongo_start import main_currencies
from spiders.providers.secrets import apikey

logger = logging.getLogger(__name__)


def get_data(symbol: str, apikey: str, function: str ='TIME_SERIES_DAILY', outputsize: str ='compact',
             datatype: str ='json') -> (str, dict):
    """
    get historic data
    :param symbol:
    :param apikey:
    :param function:
    :param outputsize:
    :param datatype:
    :return:
    """
    # t.sleep(1)
    url = 'https://www.alphavantage.co/query'
    params = {'symbol': symbol, 'apikey': apikey, 'function': function, 'outputsize': outputsize, 'datatype': datatype}

    response = requests.get(url, params=params)
    if response.status_code != 200:
        logger.error(f'provider return {response.status_code} for {symbol}')
        return symbol, {}
    rdict = response.json()
    try:
        meta = rdict['Meta Data']
    except KeyError:
        logger.error(f'no data for \'{symbol}\'')
        return symbol, {}
    data = rdict['Time Series (Daily)']
    if meta['2. Symbol'] != symbol:
        logger.warning('wrong metadata, \'2. Symbol\'= {}; expected symbol= {}'.format(meta['2. Symbol'], symbol))
        return symbol, data

    # tz = meta['5. Time Zone']
    return symbol, data


def dayily_stat_prepare(input: tuple, start: datetime, stop: datetime) -> list:
    """

    :param input:
('EURUSD', {
 '2018-02-19':
 {'1. open': '1.2398',
  '2. high': '1.2398',
  '3. low': '1.2398',
  '4. close': '1.2398',
  '5. volume': '0'},
 '2018-02-20':
 {'1. open': '1.2343',
  '2. high': '1.2343',
  '3. low': '1.2343',
  '4. close': '1.2343',
  '5. volume': '0'},})

    :return:
    [{'time': datetime(2018, 2, 19), 'EURUSD': 1.2398},
     {'time': datetime(2018, 2, 20), 'EURUSD': 1.2343}]
    """
    symbol, data = input
    if data == {}:
        return []
    data_formated = []
    while start < stop:
        day = {}
        record = {}
        _date = start.strftime('%Y-%m-%d')
        try:
            day = data[_date]
        except Exception as e:
            logger.warning('date= {}, not found in data for symbol= {}'.format(start, symbol))
            start += timedelta(days=1)
            continue
        record['time'] = datetime.strptime(_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        record[symbol] = day['4. close']
        data_formated.append(record)
        start += timedelta(days=1)

    return data_formated


def fill_main_currency(symbol, start: datetime =datetime(2000, 1, 1)):
    """
    put data in db from start till today
    :param symbol:
    :param star:
    :return:
    """
    stop = datetime.combine(date.today(), time.min)
    start = main_currencies.find_one({symbol: {'$exists': True}}, sort=[('time', pymongo.DESCENDING)])['time']
    logger.info(f'last document for {symbol} in DB at {start}')
    start -= timedelta(days=2)
    if stop - start > timedelta(days=100):
        logger.info('working with 10 year data, for symbol= {}'.format(symbol))
        data = dayily_stat_prepare(get_data(symbol, apikey, outputsize='full'), start, stop)
    else:
        logger.info('working with last 100 records, for symbol= {}'.format(symbol))
        data = dayily_stat_prepare(get_data(symbol, apikey), start, stop)

    result = mongo_multi_column(data, main_currencies)
    logger.info(f"currency {symbol}; new docs= {result.new_doc_count}, modif docs ={result.modified_count}")

    return result


def fill_main_currencies(currencies: list):
    result_dict = {}
    for currency in currencies:
        result = fill_main_currency(currency)
        result_dict[currency] = result
    return result_dict


