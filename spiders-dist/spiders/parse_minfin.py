# -*- coding: utf-8 -*-
# TODO:
# + minfin_history return data in float
# from sh import curl
# import sh
import json
import pickle
from datetime import datetime, timedelta
from time import sleep
import logging
from collections import namedtuple
from typing import Dict, Union
import re


import requests
from hyper import HTTP20Connection as h2
from hyper.contrib import HTTP20Adapter
from bs4 import BeautifulSoup
import sys
# sys.path.append('./')
# import spiders

from spiders import filters
from spiders import parameters
from spiders.check_proxy import proxy_is_used
from spiders.simple_encrypt_import import secret
from spiders.common_spider import current_datetime_tz, date_handler, kyiv_tz
from spiders.tables import reform_table_fix_columns_sizes, print_table_as_is

logger = logging.getLogger('spiders.parse_minfin')

# user settings
currency = filters.currency.lower()
operation = filters.operation
location_orig = filters.location
location_dict = {'Киев': 'kiev',
                 }
location = location_dict[location_orig]
################  filter data  ################
filter_or = filters.filter_or


# global vars to save vars
bid_to_payload = secret.bid_to_payload
cook = {}

headers = {'Host': 'minfin.com.ua',
           'User-Agent': 'Mozilla/5.0 (X11; Windows amd64; rv:60.0) Gecko/20100101 Firefox/60.0',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Language': 'en,uk;q=0.7,ru;q=0.3',
           'Accept-Encoding': 'gzip, deflate, br',
           'DNT': '1',
           'Connection': 'keep-alive',
           'Pragma': 'no-cache',
           'Cache-Control': 'max-age=0, no-cache',
           'Upgrade-Insecure-Requests': '1'}


# @timer()
def get_triple_data(currency: str, operation: str, test_data: dict = None) -> tuple:
    """

        # minfin_urls = {'usd_sell' : 'http://minfin.com.ua/currency/auction/usd/sell/kiev/?presort=&sort=time&order=desc',
        #                'usd_buy' : 'http://minfin.com.ua/currency/auction/usd/buy/kiev/?presort=&sort=time&order=desc',
        #                'eur_sell' : 'http://minfin.com.ua/currency/auction/eur/sell/kiev/?presort=&sort=time&order=desc',
        #                'eur_buy' : 'http://minfin.com.ua/currency/auction/eur/buy/kiev/?presort=&sort=time&order=desc'}

        # ------------- curl alternative ---------------
        # raw_data_file = 'minfin.html'
        # cookies_file = 'minfin_cooks.txt'
        # try:
        #     curl(url, '-o', raw_data_file, '--user-agent', user_agent, '-m', '3')
        # except :
        #     curl(url, '-o', raw_data_file, '--user-agent', user_agent, '-x', proxy)
        # ----------------------------------------------


    """

    url = 'https://minfin.com.ua/currency/auction/' + currency + '/' + operation + '/' + location + '/'
    s = requests.Session()
    s.mount(url, HTTP20Adapter())
    responce_get = s.get(url, headers=headers)

    if responce_get.status_code != 200:
        logger.error('could not fetch list from minfin.com.ua, resp.status= {}'.format(responce_get.status_code))
        logger.error('url={}'.format(url))
        return ()
    responce_get.encoding = 'utf-8' # set utf-8 as main coding (requests doc)
    page = responce_get.text
    soup = BeautifulSoup(page, "html.parser")
    data = {}
    logger.debug('soup size = {}'.format(len(soup.get_text())))

    # regex = re.compile(r'[\t\n\r\x0b\x0c]')
    for i in soup.find_all('div', attrs={'data-bid': True,
                                              'class':  ['js-au-deal', 'au-deal']
                                              }):
        logger.debug('get_triple_data> i= {}'.format(i))
        try:
            key = i['data-bid']
            data[key] = {}
            data[key]['time'] = i.find('span', class_="au-deal-time").string
            data[key]['currency'] = currency
            data[key]['operation'] = operation
            data[key]['rate'] = i.find('span', class_="au-deal-currency").string.strip()
            data[key]['rate'] = data[key]['rate'].replace(',', '.')
            data[key]['amount'] = i.find('span', class_="au-deal-sum").contents[0].strip()
            data[key]['amount'] = data[key]['amount'].replace(' ', '')
            comment = i.find('div', class_ = "au-msg-wrapper js-au-msg-wrapper").get_text(strip=True)
            # data[key]['comment'] = regex.sub('', comment)
            # ' '.join(str.split()) works better then regex
            data[key]['comment'] = ' '.join(comment.split())
            data[key]['phone'] = i.find('div', class_="au-dealer-phone").get_text(strip=True)
            data[key]['id'] = i.find('div', class_="au-dealer-phone").a['data-bid-id']
        except KeyError:
            logger.error('missing key data-bid i= {}'.format(i))
        except Exception as e:
            logger.error(e)
    # print('----------------- fetch -------------------------')
    # transfer session parameters
    session_parm = {'cookies': pickle.dumps(responce_get.cookies), 'url': url}
    # may be needed for reference
    return data, session_parm


# @timer()
def data_api_minfin(fn):
    def convertor_minfin(dic: dict, current_date: datetime, id: int) -> dict:
        dic['bid'] = dic['id']
        del dic['id']
        # dic['id'] = id
        dic['currency'] = dic['currency'].upper()
        dic['location'] = location_orig
        dic['source'] = 'm'
        dic['session'] = False
        time = dic['time'].split(':')
        dic['time'] = current_date.replace(hour=int(time[0]), minute=int(time[1]), second=0, microsecond=0)
        dic['rate'] = float(dic['rate'])
        dic['amount'] = int(''.join(filter(lambda x: x.isdigit(), dic['amount'])))
        # TODO: remove below strings
        # if dic['time'] > current_date:
        #     dic['time'] = dic['time'] - timedelta(days=1)
        return dic

    data = {}
    sessions = []
    for cur in ['RUB', 'EUR', 'USD']:
        for oper in ['sell', 'buy']:
            fn_result = fn(cur.lower(), oper)
            if len(fn_result) < 1:
                logger.error('empty result for currency={}, operation= {}'.format(cur, oper))
                continue
            data.update(fn_result[0])
            sessions.append({'currency': cur.upper(), 'source': 'm', 'operation': oper,
                             'url': fn_result[1]['url'], 'cookies': fn_result[1]['cookies'],
                             'session': True})
    current_date = kyiv_tz.localize(datetime.now())
    return [convertor_minfin(value, current_date, index) for index, value in enumerate(data.values())] + sessions


def day_secret(currency: str, operation: str, location:str) -> int:
    """

    :param currency:
    :param operation:
    :param location:
    :return:
    """
    url = 'https://minfin.com.ua/currency/auction/' + currency.lower() + '/' + operation.lower() + '/' + location.lower() + '/'
    logger.debug('url= {}'.format(url))
    s = requests.Session()
    s.mount(url, HTTP20Adapter())
    responce_get = s.get(url, headers=headers)
    if responce_get.status_code != 200:
        logger.error('could not fetch list from minfin.com.ua, resp.status= {}'.format(responce_get.status_code))
        logger.error('url={}'.format(url))
        raise ValueError
    page = responce_get.text
    soup = BeautifulSoup(page, 'html.parser')
    logger.debug('soup = {}'.format(soup))
    url_js = soup.find('script', attrs={'src': re.compile(r'/dist/js/currency/au-currency-.*\.js')})['src'].strip()
    logger.info('url_js= {}'.format(url_js))
    if url_js == '':
        logger.error('parser error')
        raise ValueError

    url = 'https://minfin.com.ua' + url_js
    s = requests.Session()
    s.mount(url, HTTP20Adapter())
    responce_get = s.get(url, headers=headers)
    if responce_get.status_code != 200:
        logger.error('could not fetch list from minfin.com.ua, resp.status= {}'.format(responce_get.status_code))
        logger.error('url={}'.format(url))
        raise ValueError
    page = responce_get.text
    search_text = '(parseInt(bidID)'
    first_leter = page.find(search_text)
    try:
        secret = int(page[first_leter + len(search_text): first_leter + len(search_text) + 2])
    except Exception as e:
        logger.error('can\'t get secret; exeption={}'.format(e))
        raise e
    return secret


def get_contacts(bid: str, number: str, currency: str, operation: str, location: str) -> str:
    """

    :param operation:
    :param currency:
    :param bid:
    :param data_func:
    :param session_parm: get session parameters, such as 'Referer', 'cookies'
    :param content_json: return in json format
    :return: response or serialized json
    # --------- curl method -----------------
    # url_get_contacts = 'http://minfin.com.ua/modules/connector/connector.php?action=auction-get-contacts&bid=' \
    #                    + str(int(bid) + 1) + '&r=true'
    # form_urlencoded = 'bid=' + bid + '&action=auction-get-contacts&r=true'
    # header_Content_Type = 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8'
    # if proxy == None:
    #     curl(url_get_contacts, '-c', cookies_file, '-b', cookies_file,  '--user-agent', user_agent, '-X', 'POST', '-e', url,
    #          '-d', form_urlencoded, '-H', header_Content_Type)
    # else:
    #     curl(url_get_contacts, '-c', cookies_file, '-b', cookies_file,  '--user-agent', user_agent, '-X', 'POST', '-e', url,
    #          '-d', form_urlencoded, '-H', header_Content_Type, '-x', proxy)
# ---------------------------------------------

    # ---------- requests ---------------------
    # at that moment successful response on
    # http -f POST "http://minfin.com.ua/modules/connector/connector.php?action=auction-get-contacts&bid=25195556&
    # r=true" bid=25195555 action=auction-get-contacts r=true 'Cookie: minfincomua_region=1' 'Referer: http://minfin.com.ua/currency
    # /auction/usd/sell/kiev/?presort=&sort=time&order=desc'
    # global cook
    http - f POST
    "https://minfin.com.ua/modules/connector/connector.php?action=auction-get-contacts&bid=73626264&
    # r=true" bid=73626262 action=auction-get-contacts r=true 'Cookie: minfincomua_region=0;minfin_sessions=26d573e41c9b65af1dc72004b6cde5413346d783;__cfduid=d4f757511b27ef8da4931141b6336093e1529854768'
    """
    secret_bid = int(bid) + day_secret(currency, operation, location)
    logger.debug('secret bid= {}, secret_bid= {}'.format(bid, secret_bid))
    data = {'bid': bid, 'action': 'auction-get-contacts',  'r': 'true'}
    url = 'https://minfin.com.ua/modules/connector/connector.php?action=auction-get-contacts&bid=' + \
          str(secret_bid) + '&r=true'
    logger.debug('final url= {}'.format(url))
    s = requests.Session()
    s.mount(url, HTTP20Adapter())
    response = s.post(url, data=data, headers=headers)

    if response.status_code != 200:
        logger.error('wrong response from minfin= {}'.format(response.status_code))
        raise ValueError

    # if content_json == False:
    logger.debug('minfin response= {}'.format(response.json()))
    # return response
    # else:
    #     logger.info('minfin answer= {}'.format(response.content))
    #     return response.content
    contact = response.json()['data']
    contact = number.replace('xxx-x', '-' + contact)
    logger.info('contact= {}'.format(contact))
    return contact


def table_api_minfin(fn_data, fn_contacts):
    def filter_data_json(data: dict, keyword: str) -> list:
        """

        :type data: {'11898627': {'amount': '2000',
                                             'comment': 'М. Дворец Украины,       целиком, От 1 тыс.',
                                             'currency': 'usd',
                                             'id': '11898627',
                                             'operation': 'sell',
                                             'phone': '067xxx-x6-98',
                                             'rate': '27,14',
                                             'time': '13:10'}}
        """
        return [key for key, val in data.items() if val['comment'].find(keyword) != -1 and val['operation'] == operation ]


    data, session_parm = fn_data(currency, operation)
    bid_to_payload = secret.bid_to_payload
    # filter by keywords
    filter_or = filters.filter_or.lower()
    filter_or = filter_or.split()
    filtered_set = set()
    for filter_  in  filter_or:
        filtered_set = filtered_set.union(set(filter_data_json(data, filter_)))

    for bid in filtered_set:
        r = fn_contacts(bid, bid_to_payload, session_parm, proxy_is_used)
        logger.debug('table_api_minfin>> r= {}'.format(r))
        data[bid]['phone'] = data[bid]['phone'].replace('xxx-x', r.json()['data'] )
        pickle.loads(session_parm['cookies'])['minfin_sessions'] = r.cookies['minfin_sessions']
        sleep(0.5)
    return [(data[Id]['time'], data[Id]['currency'], data[Id]['operation'], data[Id]['rate'], data[Id]['amount'],
               location, data[Id]['comment'], data[Id]['phone'], 'm') for Id in filtered_set]


def minfin_history(currency: str, today: datetime) -> list:
    """
    data available for USD and EUR
    :param currency:
    :param today: in datetime, in url should be example 2016-03-27 == 160327 in request
    :return:
    """
    params = {'v': today.strftime('%y%m%d')}
    url = 'http://minfin.com.ua/data/currency/auction/' + currency.lower() + '.0.median.daily.json'
    data = []
    for key, val in requests.get(url, params=params).json().items():
        if val == []: # protect from empty data for date
            continue
        document = {}
        document['time'] = datetime.strptime(key, '%Y-%m-%d %H:%M:%S')
        document['currency'] = currency
        document['source'] = 'm'
        document['buy'] = float(val['b'])
        document['sell'] = float(val['s'])
        data.append(document)
    return data

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # logging.basicConfig(level=logging.INFO)
    table = reform_table_fix_columns_sizes(table_api_minfin(get_triple_data, get_contacts),
                                           parameters.table_column_size)
    print(json.dumps(data_api_minfin(get_triple_data('USD', 'sell')), sort_keys=True, indent=4, separators=(',', ': '),
                     ensure_ascii=False, default=date_handler))
    print(u'----- results for {currency} {contract} ------'.format(contract=location, currency=currency))
    print(u'=== filter: location= {location}, filter= {filtered}'.format(location=location,
                                                                          filtered=u' '.join(filter_or)))
    print_table_as_is(table)
    # # print(json.dumps(minfin_history('USD', datetime.now()), sort_keys=True, indent=4, separators=(',', ': '),
    # #                  ensure_ascii=False, default=date_handler))
    #
