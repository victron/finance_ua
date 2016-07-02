import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from spiders import parameters
from spiders.check_proxy import proxy_is_used
from spiders.common_spider import current_datetime_tz, date_handler
from tools.mytools import timer
import logging

logger = logging.getLogger('curs.spiders.news_minfin')

# TODO:
# - convert time into datetime

# internet settings
user_agent = parameters.user_agent
headers = {'user-agent': user_agent}
proxies = parameters.proxies
# news_type = parameters.news_type

urls_dict = {'currency': 'commerce'}

@timer(logging=logger)
def parse_minfin_headlines():
    news_type = parameters.news_type
    url = 'http://minfin.com.ua/news/' + urls_dict[news_type] + '/'
    if proxy_is_used == False:
        responce_get = requests.get(url, headers=headers)
    else:
        responce_get = requests.get(url, headers=headers, timeout = 3, proxies=proxies)

    soup = BeautifulSoup(responce_get.text, "html.parser")
    current_date = current_datetime_tz()
    data = []
    for news in soup.body.table.find_all(attrs={'class': ['title']}):
        dic = {'time': news.div['content'],
               'href': 'http://minfin.com.ua' + news.a['href'],
               'headline':  news.a.string,
               'source': 'm'}
        dic['time'] = datetime.strptime(dic['time'], '%Y-%m-%d %H:%M:%S')
        dic['time'] = dic['time'].replace(tzinfo=current_date.tzinfo)
        data.append(dic)
    return data

def func(arg):
    return arg()

if __name__ == '__main__':
    print(json.dumps(parse_minfin_headlines(), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False,
                     default=date_handler))

