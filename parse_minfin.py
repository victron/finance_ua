# -*- coding: utf-8 -*-
# TODO:
# + minfin_history return data in float
# from sh import curl
# import sh
import requests
from bs4 import BeautifulSoup
from time import sleep
from tables import reform_table_fix_columns_sizes, print_table_as_is
from check_proxy import proxy_is_used
import json
import parameters, filters
from datetime import datetime, timedelta
from common_spider import current_datetime_tz, date_handler
import secret
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



def get_triple_data(currency: str, operation: str) -> dict:

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
    soup = BeautifulSoup(responce_get.text, "html.parser")
    data = {}
    # regex = re.compile(r'[\t\n\r\x0b\x0c]')
    for i in soup.body.find_all('div', attrs={'data-bid' : True, 'class':  ['js-au-deal', 'au-deal']}):
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
            pass
    # print('----------------- fetch -------------------------')
    return data, responce_get


def data_api_minfin(fn):
    def convertor_minfin(dic: dict, current_date: datetime, id: int) -> dict:
        dic['bid'] = dic['id']
        del dic['id']
        # dic['id'] = id
        dic['currency'] = dic['currency'].upper()
        dic['location'] = location_orig
        dic['source'] = 'm'
        time = dic['time'].split(':')
        dic['time'] = current_date.replace(hour= int(time[0]), minute= int(time[1]), second=0, microsecond=0)
        dic['rate'] = float(dic['rate'].replace(',', '.'))
        if dic['time'] > current_date:
            dic['time'] = dic['time'] - timedelta(days=1)
        return dic

    data = {}
    for cur in ['rub', 'eur', 'usd']:
        for oper in ['sell', 'buy']:
            data.update(fn(cur, oper)[0])

    current_date = current_datetime_tz()
    return [convertor_minfin(value, current_date, index) for index, value in enumerate(data.values())]


def get_contacts(bid: str, cookies: str, data_func, proxy_is_used: bool = False) -> requests:
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
    form_urlencoded = 'http://minfin.com.ua/modules/connector/connector.php'
    payload, data = data_func(bid)
    # headers = {'user-agent': 'Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)'}
    if proxy_is_used ==False:
        return requests.post(form_urlencoded, params=payload, headers=headers, data=data, cookies=cookies)
    else:
        return requests.post(form_urlencoded, params=payload, headers=headers, data=data, cookies=cookies,
                             proxies=proxies)
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


    data, responce_get = fn_data(currency, operation)
    bid_to_payload = secret.bid_to_payload
    # filter by keywords
    filter_or = filters.filter_or.lower()
    filter_or = filter_or.split()
    filtered_set = set()
    for filter_  in  filter_or:
        filtered_set = filtered_set.union(set(filter_data_json(data, filter_)))

    for bid in filtered_set:
        r = fn_contacts(bid, responce_get.cookies, bid_to_payload, proxy_is_used)
        data[bid]['phone'] = data[bid]['phone'].replace('xxx-x', r.json()['data'] )
        responce_get.cookies['minfin_sessions'] = r.cookies['minfin_sessions']
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
        document['time'] = datetime.strptime(key, '%Y-%m-%d %H:%M:%S')\
            .replace(hour=17, minute=0, microsecond=0, tzinfo=current_datetime_tz().tzinfo)
        document['currency'] = currency
        document['source'] = 'm'
        document['buy'] = float(val['b'])
        document['sell'] = float(val['s'])
        data.append(document)
    return data



if __name__ == '__main__':
    table = reform_table_fix_columns_sizes(table_api_minfin(get_triple_data, get_contacts), parameters.table_column_size)
    print(json.dumps(data_api_minfin(get_triple_data), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False,
                     default=date_handler))
    print (u'----- results for {currency} {contract} ------'.format(contract=location, currency=currency))
    print (u'=== filter: location= {location}, filter= {filtered}'.format(location=location,
                                                                          filtered=u' '.join(filter_or)))
    print_table_as_is(table)
    # print(json.dumps(minfin_history('USD', datetime.now()), sort_keys=True, indent=4, separators=(',', ': '),
    #                  ensure_ascii=False, default=date_handler))

