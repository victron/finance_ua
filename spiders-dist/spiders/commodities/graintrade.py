import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, date, time
import pytz
import logging
from collections import namedtuple


from spiders.mongo_start import commodities as commodities_collection
from spiders.commodities.update_history_logic import update_history
from spiders.commodities.common_dict import graintrade_key

logger = logging.getLogger(__name__)

def get_page() -> requests.Response:
    url = 'https://graintrade.com.ua/en'
    resp_get = requests.get(url)
    return resp_get


def available_commodities(page: requests.Response) -> list:
    soup = BeautifulSoup(page.text, 'html.parser')
    try:
        result = [row.td.b.get_text()
                      for table in soup.find_all('table', attrs={'class': 'ExchangeRate Bloomberg table'})
                      for row in table.find_all('tr')]
    except:
        msg = 'can\'t get available_commodities list'
        logger.error(msg)
        raise ValueError(msg)
    return result


def get_commudities(commodities: list) -> list:
    """
    from list of commudities get list of dos
    :param page: 
    :param commodity: 
    :return: list(dict)
    """
    graintrade_val = {v: k for k, v in graintrade_key.items()}
    page = get_page()
    soup = BeautifulSoup(page.text, 'html.parser')
    result = []
    current_date = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)
    try:
        a_available = available_commodities(page)
    except ValueError as e:
        logger.error('can\'t get available_commodities list')
        raise
    for commodity in commodities:
        if commodity not in a_available:
            logger.error('commodity {} not available; available commudities= {}'.format(commodity, a_available))
            raise NameError
        for table in soup.find_all('table', attrs={'class': 'ExchangeRate Bloomberg table'}):
            for row in table.find_all('tr'):
                if row.td.b.get_text() == commodity:
                    result.append({graintrade_val[commodity]:
                                       float(row.td.next_sibling.next_sibling.get_text().split(' ')[0]),
                                   'time': current_date})
    # remove duplicates, leave last (from Euronext)
    temp_list = []
    for dic in result:
        for k in dic.keys():
            if k != 'time':
                temp_list.append(k)
    temp_result = list(result)
    for doc in temp_result:
        key = temp_list.pop(0)
        if key in temp_list:
            logger.debug('removed duplicity {}'.format(doc))
            result.remove(doc)
    return result


def update_mongo(commodities: list) -> namedtuple:
    """
    check if data for today availble in collection for today add into db
    :return: 
    """
    try:
        commodities_site = [graintrade_key[c] for c in commodities]
    except KeyError as e:
        logger.error('commodity {} not in graintrade_key dict'.format(e))
        raise e
    current_date = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)
    result = commodities_collection.find_one({'time': current_date})
    if result:
        need_to_get_commodities = [commodity for commodity in commodities_site if result.get(commodity) is None]
        if need_to_get_commodities == []:
            logger.info('don\'t need update {}'.format(commodities))
            return {'not updated': commodities}
    else:
        need_to_get_commodities = commodities_site
    logger.info('need to update= {}'.format(need_to_get_commodities))
    docs = get_commudities(need_to_get_commodities)
    return update_history(docs, commodities_collection)





