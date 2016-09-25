import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from spiders.common_spider import local_tz, date_handler, current_datetime_tz
from spiders.parameters import proxy_is_used, headers, proxies
from tools.mytools import timer
import logging

logger = logging.getLogger('curs.spiders.minfin')


#
def minfin_headlines_url(url) -> list:
    #url = 'http://www.minfin.gov.ua/news/borg/zovnishni-suverenni-zobovjazannja'
    if proxy_is_used == False:
        responce_get = requests.get(url, headers=headers)
    else:
        responce_get = requests.get(url, headers=headers, timeout=3, proxies=proxies)

    soup = BeautifulSoup(responce_get.text, 'html.parser')
    headlines = []
    for i in soup.body.find('div', attrs={'class': ['posts-box__list', 'float-nav-wr']}).find_all('div', attrs={'class': 'text'}):
        href = 'http://www.minfin.gov.ua' + i.a['href']
        time = datetime.strptime(i.span.get_text(), '%m/%d/%y').replace(tzinfo=local_tz)
        headline = i.find('div', attrs={'class': 'text_i'}).get_text(strip=True)
        headlines.append({'href': href, 'time': time, 'headline': headline, 'source': 'mf'})
    return headlines

@timer(logging=logger)
def minfin_headlines():
    headlines = []
    for url in ['http://www.minfin.gov.ua/news/borg/zovnishni-suverenni-zobovjazannja',
                'http://www.minfin.gov.ua/news/novini-ta-media']:
        headlines += minfin_headlines_url(url)
    return headlines


def announcement_ovdp() -> list:
    url = 'http://www.minfin.gov.ua/news/view/informatsiia-shchodo-auktsioniv-ovdp'
    responce_get = requests.get(url, headers=headers)
    soup = BeautifulSoup(responce_get.text, 'html.parser')
    current_date = current_datetime_tz()
    data = []
    for news in soup.body.table.tbody.find_all('tr'):
        dic = {'time_auction': news.td.get_text(),
               'time': current_date,
               'href_announce': news.td.next_sibling.a['href'],
               'source': 'mf',
               'headline': 'OVDP ' + news.td.get_text()}
        try:
            dic['href_results'] = news.td.next_sibling.next_sibling.a['href']
        except TypeError:
            dic['href_results'] = None
        dic['time_auction'] = datetime.strptime(dic['time_auction'], '%d.%m.%Y').replace(hour=17, tzinfo=local_tz)

        if not dic['href_announce'].startswith('http://'):
            dic['href_announce'] = 'http://www.minfin.gov.ua' + dic['href_announce']
        if dic['href_results'] is not None:
            if not dic['href_results'].startswith('http://'):
                dic['href_results'] = 'http://www.minfin.gov.ua' + dic['href_results']
        dic['href'] = url
        # if auction day == current day, add field 'flag'
        if dic['time_auction'].day == current_date.day:
            dic['flag'] = 'same_date'
            dic['headline'] = dic['headline'] + dic['flag']
        else:
            dic['flag'] = 'normal'
        data.append(dic)
    return data


if __name__ == '__main__':
    print(json.dumps(minfin_headlines(), sort_keys=True, indent=4, separators=(',', ': '),
                     ensure_ascii=False, default=date_handler))
    print(json.dumps(announcement_ovdp(), sort_keys=True, indent=4, separators=(',', ': '),
                     ensure_ascii=False, default=date_handler))

