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
logger = logging.getLogger()

import requests
from bs4 import BeautifulSoup
import sys
# sys.path.append('./')
# import spiders

from spiders import filters
from spiders import parameters
from spiders.check_proxy import proxy_is_used
from spiders.simple_encrypt_import import secret
from spiders.common_spider import current_datetime_tz, date_handler
# from spiders.tables import reform_table_fix_columns_sizes, print_table_as_is
import requests
from collections import namedtuple

# user settings
currency = filters.currency.lower()
operation = filters.operation
location_orig = filters.location
location_dict = {'Киев': 'kiev',
                 }
location = location_dict[location_orig]
################  filter data  ################
filter_or = filters.filter_or

# internet settings
user_agent = parameters.user_agent
headers = {'user-agent': user_agent}
proxies = parameters.proxies

# global vars to save vars
bid_to_payload = secret.bid_to_payload
cook = {}


# @timer()
def get_triple_data(currency: str, operation: str, test_page: namedtuple = None) -> tuple:

    # minfin_urls = {'usd_sell' : 'http://minfin.com.ua/currency/auction/usd/sell/kiev/?presort=&sort=time&order=desc',
    #                'usd_buy' : 'http://minfin.com.ua/currency/auction/usd/buy/kiev/?presort=&sort=time&order=desc',
    #                'eur_sell' : 'http://minfin.com.ua/currency/auction/eur/sell/kiev/?presort=&sort=time&order=desc',
    #                'eur_buy' : 'http://minfin.com.ua/currency/auction/eur/buy/kiev/?presort=&sort=time&order=desc'}

    url = 'http://minfin.com.ua/currency/auction/' + currency + '/' + operation + '/' + location + \
          '/?presort=&sort=time&order=desc'

    # ------------- curl alternative ---------------
    # raw_data_file = 'minfin.html'
    # cookies_file = 'minfin_cooks.txt'
    # try:
    #     curl(url, '-o', raw_data_file, '--user-agent', user_agent, '-m', '3')
    # except :
    #     curl(url, '-o', raw_data_file, '--user-agent', user_agent, '-x', proxy)
    # ----------------------------------------------
    if proxy_is_used == False:
        responce_get = requests.get(url, headers=headers)
    else:
        responce_get = requests.get(url, headers=headers, timeout = 3, proxies=proxies)

    ###
    if test_page is not None:
        logger.debug('TEST is active')
        soup = BeautifulSoup(test_page.text, "html.parser")
    else:
        logger.debug('TEST is inactive')
        soup = BeautifulSoup(responce_get.text, "html.parser")
    # global cook
    # cook['cookies'] = responce_get.cookies
    # cook['url'] = url
    data = {}
    logger.debug('soup = {}'.format(soup))
    # regex = re.compile(r'[\t\n\r\x0b\x0c]')
    for i in soup.find_all('div', attrs={'data-bid' : True,
                                              'class':  ['js-au-deal', 'au-deal']
                                              }):
        logger.debug('get_triple_data> i= {}'.format(i))
        try:
            key = i['data-bid']
            data[key] = {}
            data[key]['time'] = i.small.string
            data[key]['currency'] = currency
            data[key]['operation'] = operation
            data[key]['rate'] = i.find('span', class_ = "au-deal-currency").string
            data[key]['amount'] = [text for text in i.find('span', class_ = "au-deal-sum").strings][0].replace(' ', '')
            # data[key]['comment'] = i.find('span', class_ = "au-msg-wrapper js-au-msg-wrapper").string.strip()\
            #     .replace('\n', '')
            comment = i.find('span', class_ = "au-msg-wrapper js-au-msg-wrapper").get_text(strip=True)
            # data[key]['comment'] = regex.sub('', comment)
            # ' '.join(str.split()) works better then regex
            data[key]['comment'] = ' '.join(comment.split())
            data[key]['phone'] = i.find('span', class_ = "au-dealer-phone").get_text(strip=True)
            data[key]['id'] = i.find('span', class_ = "au-dealer-phone").a['data-bid-id']
        except KeyError:
            logger.error('missing key data-bid i= {}'.format(i))
    # print('----------------- fetch -------------------------')
    # transfer session parameters
    session_parm = {}
    if test_page is not None:
        session_parm['cookies'] = pickle.dumps(test_page.cookies)
    else:
        session_parm['cookies'] = pickle.dumps(responce_get.cookies)
    session_parm['url'] = url
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
        dic['time'] = current_date.replace(hour= int(time[0]), minute= int(time[1]), second=0, microsecond=0)
        dic['rate'] = float(dic['rate'].replace(',', '.'))
        if dic['time'] > current_date:
            dic['time'] = dic['time'] - timedelta(days=1)
        return dic

    data = {}
    sessions = []
    for cur in ['rub', 'eur', 'usd']:
        for oper in ['sell', 'buy']:
            fn_result = fn(cur, oper)
            data.update(fn_result[0])
            sessions.append({'currency': cur.upper(), 'source': 'm', 'operation': oper,
                             'url': fn_result[1]['url'], 'cookies': fn_result[1]['cookies'],
                             'session': True})
    current_date = current_datetime_tz()
    return [convertor_minfin(value, current_date, index) for index, value in enumerate(data.values())] + sessions


def get_contacts(bid: str, data_func, session_parm: dict, content_json: bool = False) -> requests:
    """

    :param bid:
    :param data_func:
    :param session_parm: get session parameters, such as 'Referer', 'cookies'
    :param content_json: return in json format
    :return: response or serialized json
    """
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
    # at that moment successful responce on
    # http -f POST "http://minfin.com.ua/modules/connector/connector.php?action=auction-get-contacts&bid=25195556&
    # r=true" bid=25195555 action=auction-get-contacts r=true 'Cookie: minfincomua_region=1' 'Referer: http://minfin.com.ua/currency
    # /auction/usd/sell/kiev/?presort=&sort=time&order=desc'
    # global cook
    form_urlencoded = 'http://minfin.com.ua/modules/connector/connector.php'
    payload, data = data_func(bid)
    headers = {'user-agent': 'Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)'}
    headers.update({'Referer': session_parm['url']})

    # headers.update({'Cookie': 'minfincomua_region=1'})
    if content_json ==False:
        return requests.post(form_urlencoded, params=payload, headers=headers, data=data,
                             cookies=pickle.loads(session_parm['cookies']))
    else:
        return requests.post(form_urlencoded, params=payload, headers=headers, data=data,
                             cookies=pickle.loads(session_parm['cookies'])).content
    # return r.json()['data']


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
