from datetime import datetime, timedelta
from os import path
import pickle

from spiders.common_spider import local_tz, kyiv_tz

DATA_PATH = path.join('data', 'pages', '')
DB_NAME = 'TEST'

# current_datetime = datetime.now(tz=local_tz)


url_to_file = {
    'http://minfin.com.ua/news/': 'news_minfin.pickle',
    'http://www.minfin.gov.ua/news/borg/zovnishni-suverenni-zobovjazannja': 'minfin_headlines_ZSZ.pickle',
    'http://www.minfin.gov.ua/news/novini-ta-media': 'minfin_headlines_novini-ta-media.pickle',
    'http://www.minfin.gov.ua/news/view/informatsiia-shchodo-auktsioniv-ovdp': 'parse_announcement_ovdp.pickle',
    'http://markets.businessinsider.com/commodities': 'businessinsider_commodities.pickle',
    'http://markets.businessinsider.com/commodities/historical-prices/iron-ore-price/1.1.2014_28.3.2017':
        'history_post1_responce.pickle',
    'http://markets.businessinsider.com/Ajax/CommodityController_HistoricPriceList/iron-ore-price/USD/1.1.2014_28.3.2017':
        'history_post2_responce.pickle',
    'http://www.tradingeconomics.com/commodities': 'tradingeconomics_commodities.pickle',
    'https://graintrade.com.ua/en': 'graintrade_get.pickle'
}

def mock_requests(url: str, **kwargs) -> str:
    if url not in url_to_file:
        raise KeyError('url= {} not in dict url_to_file'.format(url))
    with open(DATA_PATH + url_to_file[url], 'rb') as f:
        return pickle.load(f)


def date_depends_time(doc: dict):
    """
    replace date in doc on today or today-1, if time > current_time
    :param doc:
    :return:
    """
    current_datetime = datetime.utcnow()
    current_time = current_datetime.time()
    current_date = current_datetime.date()
    try:
        doc_time = doc['time'].time()
    except KeyError:
        return doc
    if doc_time <= current_time:
        doc['time'] = doc['time'].replace(current_datetime.year, current_datetime.month, current_datetime.day)
    else:
        doc['time'] = doc['time'].replace(current_datetime.year, current_datetime.month, current_datetime.day)\
                      - timedelta(days=1)
    return doc

# def set_date_today(doc: dict):
#     """
#     replace date in doc on today
#     :param doc:
#     :return:
#     """
#     current_time = current_datetime.time()
#     current_date = current_datetime.date()
#     doc_time = doc['time'].time()
#     if doc_time <= current_time:
#         doc['time'] = doc['time'].combine(current_date, doc_time, tzinfo=local_tz)
#     else:
#         doc['time'] = doc['time'].combine(current_date, doc_time, tzinfo=local_tz) - timedelta(days=1)
#     return doc