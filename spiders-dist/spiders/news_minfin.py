import json
import logging
from datetime import datetime, timezone

from spiders import parameters
import requests
from bs4 import BeautifulSoup
from spiders.check_proxy import proxy_is_used

from spiders.common_spider import current_datetime_tz, date_handler, kyiv_tz

logger = logging.getLogger('curs.spiders.news_minfin')

# TODO:
# - convert time into datetime

# internet settings
user_agent = parameters.user_agent
headers = {'user-agent': user_agent}
proxies = parameters.proxies
# news_type = parameters.news_type

urls_dict = {'currency': 'commerce'}

def parse_page(responce_get: str) -> list:

    soup = BeautifulSoup(responce_get, 'html.parser')
    current_date = current_datetime_tz()
    data = []
    for news in soup.body.table.find_all(attrs={'class': ['title']}):
        dic = {'time': news.div['content'],
               'href': 'http://minfin.com.ua' + news.a['href'],
               'headline': news.a.get_text(),
               'source': 'm'}
        dic['time'] = datetime.strptime(dic['time'], '%Y-%m-%d %H:%M:%S')
        dic['time'] = kyiv_tz.localize(dic['time']).astimezone(timezone.utc)
        data.append(dic)
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

