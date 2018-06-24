import json
import logging
from datetime import datetime, timezone

from spiders import parameters
import requests
from bs4 import BeautifulSoup
from spiders.check_proxy import proxy_is_used
from hyper import HTTP20Connection as h2

from spiders.common_spider import current_datetime_tz, date_handler, kyiv_tz

logger = logging.getLogger('spiders.news_minfin')

# TODO:
# - convert time into datetime

# internet settings
user_agent = parameters.user_agent
headers = {'Host': 'minfin.com.ua',
           'User-Agent': 'Mozilla/5.0 (X11; Windows amd64; rv:60.0) Gecko/20100101 Firefox/60.0',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Language': 'en,uk;q=0.7,ru;q=0.3',
           'Accept-Encoding': 'gzip, deflate, br',
           'DNT': '1',
           'Connection': 'keep-alive',
           'Pragma': 'no-cache',
           'Cache-Control': 'no-cache'}
proxies = parameters.proxies
# news_type = parameters.news_type

urls_dict = {'currency': 'commerce'}

def parse_page(responce_get: str) -> list:
    conn = h2('minfin.com.ua:443')
    conn.request('GET', '/news/'+ urls_dict['currency'] + '/', headers=headers)
    resp = conn.get_response()
    if resp.status != 200:
        logger.error('could not fetch news from minfin.com.ua, resp.status= {}'.format(resp.status))
        return []
    text = resp.read()

    soup = BeautifulSoup(text, 'html.parser')
    current_date = current_datetime_tz()
    data = []
    news_table = soup.body.find(attrs={'class': ['all-news', 'news-all']})
    for news in news_table.find_all(attrs={'class': ['item']}):
        logger.debug('news= {}'.format(news))
        if news.div != None:
            continue
        dic = {'time': news.span['content'],
               'href': 'http://minfin.com.ua' + news.a['href'],
               'headline': news.a.get_text(),
               'source': 'm'}
        dic['time'] = datetime.strptime(dic['time'], '%Y-%m-%d %H:%M:%S')
        dic['time'] = kyiv_tz.localize(dic['time']).astimezone(timezone.utc)
        data.append(dic)
    logger.debug('minfin_headlines data= {}'.format(data))
    return data


# @timer(logging=logger)
def parse_minfin_headlines():
    news_type = parameters.news_type
    # url = 'http://minfin.com.ua/news/' + urls_dict[news_type] + '/'
   # http://minfin.com.ua/news/commerce/
   #  http://minfin.com.ua/news/commerce/money-management
    url = 'http://minfin.com.ua/news/'
    responce_get = requests.get(url)
    logger.debug('responce_get= {}'.format(responce_get))
    return parse_page(responce_get.text)


if __name__ == '__main__':
    print(json.dumps(parse_minfin_headlines(), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False,
                     default=date_handler))

