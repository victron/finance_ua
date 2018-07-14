# collect info from www.minfin.gov.ua (only news)

import json
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from spiders.parameters import proxy_is_used, headers, proxies

from spiders.common_spider import local_tz, date_handler, current_datetime_tz

logger = logging.getLogger('curs.spiders.minfin')

def p_minfin_headlines(responce_get: str) -> list:
    soup = BeautifulSoup(responce_get, 'html.parser')
    headlines = []
    # for i in soup.body.find('div', attrs={'class': ['posts-box__list', 'float-nav-wr']}).find_all('div', attrs={'class': 'text'}):
    for i in soup.body.find_all('div', attrs={'class': ['posts-box__item']}):
        href = 'http://www.minfin.gov.ua' + i.a['href']
        time = datetime.strptime(i.span.get_text(), '%m/%d/%y').replace(tzinfo=local_tz)
        # headline = i.find('div', attrs={'class': 'text_i'}).get_text(strip=True)
        headline = i.img['title']
        headlines.append({'href': href, 'time': time, 'headline': headline, 'source': 'mf'})
    return headlines


#
def minfin_headlines_url(url) -> list:
    #url = 'http://www.minfin.gov.ua/news/borg/zovnishni-suverenni-zobovjazannja'
    responce_get = requests.get(url)
    return p_minfin_headlines(responce_get.text)


# @timer(logging=logger)
def minfin_headlines():
    headlines = []
    for url in ['http://www.minfin.gov.ua/news/borg/zovnishni-suverenni-zobovjazannja',
                'http://www.minfin.gov.ua/news/novini-ta-media']:
        headlines += minfin_headlines_url(url)
    return headlines


def parse_announcement_ovdp(responce_get: requests) -> list:
    soup = BeautifulSoup(responce_get.text, 'html.parser')
    current_date = datetime.utcnow()
    data = []
    for news in soup.body.table.tbody.find_all('tr'):
        if news.td.next_sibling.a == None:
            continue
        dic = {'time_auction': news.td.get_text().strip().replace(' ', ''),
               'time': current_date,
               'href_announce': news.td.next_sibling.a['href'].replace(' ', '%20'),
               'source': 'mf',
               'type': 'ovdp',
               'headline': 'OVDP ' + news.td.get_text()}
        try:
            dic['href_results'] = news.td.next_sibling.next_sibling.a['href']
        except TypeError:
            dic['href_results'] = None
        try:
            dic['time_auction'] = datetime.strptime(dic['time_auction'], '%d.%m.%Y')
        except Exception as e:
            logger.error('error in parsing date dic[\'time_auction\']= \"{}\"'.format(dic['time_auction']))
            raise e

        if not dic['href_announce'].startswith('http://'):
            dic['href_announce'] = 'http://www.minfin.gov.ua' + dic['href_announce']
        if dic['href_results'] is not None:
            if not dic['href_results'].startswith('http://'):
                dic['href_results'] = 'http://www.minfin.gov.ua' + dic['href_results']

        dic['href'] = responce_get.url
        # if auction day == current day, add field 'flag'
        if dic['time_auction'].date() == current_date.date():
            dic['flag'] = 'same_date'
            dic['headline'] = dic['headline'] + ' in a ' + dic['flag']
        else:
            dic['flag'] = 'normal'
        # manipulate with fields
        # at that moment there are no clear format
        # 'href' at taht moment unique
        dic['href_docs'] = dic['href']
        dic['href'] = dic['href'] + '?ref=' + dic['href_announce']
        data.append(dic)
    return data


def announcement_ovdp() -> list:
    url = 'http://www.minfin.gov.ua/news/view/informatsiia-shchodo-auktsioniv-ovdp'
    responce_get = requests.get(url)
    return parse_announcement_ovdp(responce_get)


if __name__ == '__main__':
    # print(json.dumps(minfin_headlines(), sort_keys=True, indent=4, separators=(',', ': '),
    #                  ensure_ascii=False, default=date_handler))
    print(json.dumps(announcement_ovdp(), sort_keys=True, indent=4, separators=(',', ': '),
                     ensure_ascii=False, default=date_handler))

