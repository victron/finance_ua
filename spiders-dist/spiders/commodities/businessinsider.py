import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import pytz
import logging

from spiders.commodities.common_dict import businessinsder_key

logger = logging.getLogger(__name__)


def available_commodities() -> dict:
    url = 'http://markets.businessinsider.com/commodities'
    response_get = requests.get(url)
    soup = BeautifulSoup(response_get.text, 'html.parser')
    result = {}
    for row in soup.find_all('td', attrs={'class': 'bold', 'width': False}):
        parent = row.parent
        result[parent.a['title']] = parent.a['href'].split('/')[2]  # from '/commodities/wheat-price'
                                                                    # get only 'wheat-price'
    return result


def current_commodities(commodities: list) -> list:
    """
    :param commodities: 
    :return: 
    [{'rhodium': 1015.0, 'time': datetime.datetime(2017, 3, 24, 0, 0, tzinfo=<UTC>)}, 
    {'iron-ore-price': 88.35, 'time': datetime.datetime(2017, 3, 24, 0, 0, tzinfo=<UTC>)}, 
    {'copper-price': 5804.76, 'time': datetime.datetime(2017, 3, 24, 0, 0, tzinfo=<UTC>)}]
    """
    for commodity in commodities:
        if commodity not in available_commodities():
            logger.error('commodity= {} not available on page'.format(commodity))
            raise NameError
    url = 'http://markets.businessinsider.com/commodities'
    response_get = requests.get(url)
    soup = BeautifulSoup(response_get.text, 'html.parser')
    result = []
    for row in soup.find_all('td', attrs={'class': 'bold', 'width': False}):
        parent = row.parent
        if parent.a['title'] in commodities:
            commodity = available_commodities()[parent.a['title']]
            doc = {
                # 'commodity': commodity,
                   commodity: parent.span.get_text(),
                   'time': parent.find_all('span')[3].get_text()}
            doc[commodity] = doc[commodity].replace(',', '')
            doc[commodity] = float(doc[commodity])
            doc['time'] = datetime.strptime(doc['time'], '%m/%d/%Y')
            doc['time'] = pytz.utc.localize(doc['time'])
            result.append(doc)
    return result


def history_commodity(commodity: str, start_date: datetime, stop_date: datetime) -> list:
    """
1-st step post on url
'http://markets.businessinsider.com/commodities/historical-prices/iron-ore-price/27.2.2014_27.3.2017'
and get 
__atts: 2017-03-27-12-31-39
__ath: FNopawU4SP67mFdOfMtIYC4RFA+6XdCAWN6iBoGjxQc=
__atcrv: 778775284
add them to headers

2-nd stet post on url
http://markets.businessinsider.com/Ajax/CommodityController_HistoricPriceList/iron-ore-price/USD/27.2.2014_27.3.2017?type=Brent

    :param commodity: 
    :param start_date: 
    :param stop_date: 
    :return: [{'time': datetime.datetime(2017, 3, 28, 0, 0, tzinfo=<UTC>), 'iron-ore-price': 87.63}, 
              {'time': datetime.datetime(2017, 3, 27, 0, 0, tzinfo=<UTC>), 'iron-ore-price': 87.91}]
    """
    businessinsder_values = {v: k for k, v in businessinsder_key.items()}
    commodity_db = businessinsder_values[commodity]
    if commodity not in available_commodities():
        logger.error('commodity= {} not available in list'.format(commodity))
        raise NameError(commodity)
    commodity = available_commodities()[commodity]
    start = str(int(start_date.strftime('%d'))) + '.' + \
            str(int(start_date.strftime('%m'))) + '.' + \
            str(int(start_date.strftime('%Y')))
    stop = str(int(stop_date.strftime('%d'))) + '.' + \
           str(int(stop_date.strftime('%m'))) + '.' + \
           str(int(stop_date.strftime('%Y')))
    url = 'http://markets.businessinsider.com/commodities/historical-prices/' \
          + commodity + '/' + start + '_' + stop
    headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                 'Accept-Encoding': 'gzip, deflate',
                 'Accept-Language': 'uk,en-US;q=0.8,en;q=0.5,ru;q=0.3',
                 'Cache-Control': 'no-cache',
                 'Connection': 'keep-alive',
                 'Content-Length': '0',
                 'DNT': '1',
                 'Host': 'markets.businessinsider.com',
                 'Pragma': 'no-cache',
                 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0',
                 }

    responce_post1 = requests.post(url, headers=headers)
    logger.info('respoce_1= {}, from url= {}'.format(responce_post1.status_code, url))
    if responce_post1.status_code != 200:
        logger.error('wrong AUTH responce from businessinsider= {}'.format(responce_post1.status_code))
        logger.info('requested url= {}'.format(url))
        raise ValueError('bad responce')

    soup1 = BeautifulSoup(responce_post1.text, 'html.parser')
    # modify headers for data collection
    for key in ['__atts', '__ath', '__atcrv']:
        headers[key] = soup1.find('input', attrs={'name': key})['value']
        if key == '__atcrv':
            headers[key] = str(eval(headers[key]))

########## 2-nd step ###############

    url2 = 'http://markets.businessinsider.com/Ajax/CommodityController_HistoricPriceList/' \
          + commodity + '/USD/' + start + '_' + stop
    params = {'type': 'Brent'}

    responce_post2 = requests.post(url2, params=params, headers=headers)
    logger.info('respoce_2= {}, from url2= {}'.format(responce_post2.status_code, url2))
    if responce_post2.status_code != 200:
        logger.error('wrong DATA responce from businessinsider= {}'.format(responce_post2.status_code))
        logger.info('requested url= {}'.format(url2))
        raise ValueError('bad responce')

    soup2 = BeautifulSoup(responce_post2.text, 'html.parser')
    logger.debug('soup= {}'.format(soup2))
    logger.debug('soup text= {}'.format(soup2.div.get_text(strip=True)))
    # try another url
    if soup2.div.get_text(strip=True) == 'No data available':
        logger.warning('trying another url')
        url2 = 'http://markets.businessinsider.com/Ajax/CommodityController_HistoricPriceList/' \
               + commodity + '/USc/' + start + '_' + stop
        responce_post2 = requests.post(url2, params=params, headers=headers)
        logger.info('respoce_2= {}, from url2= {}'.format(responce_post2.status_code, url2))
        if responce_post2.status_code != 200:
            logger.error('wrong DATA responce from businessinsider= {}'.format(responce_post2.status_code))
            logger.info('requested url= {}'.format(url2))
            raise ValueError('bad responce')
        soup2 = BeautifulSoup(responce_post2.text, 'html.parser')
        logger.debug('soup= {}'.format(soup2))

    result = []

    for row in soup2.find_all('tr', attrs={'class': False}):
        logger.debug('row= {}'.format(row))
        row_list = row.find_all('td')
        logger.debug('row_list= {}'.format(row_list))
        result.append({'time': pytz.utc.localize(datetime.strptime(row_list[0].get_text(strip=True), '%m/%d/%Y')),
                       commodity_db: float(row_list[1].get_text(strip=True))})
    logger.debug('result= {}'.format(result))
    return result




