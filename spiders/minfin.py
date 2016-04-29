import requests
from spiders.parameters import proxy_is_used, headers, proxies
from bs4 import BeautifulSoup
from datetime import datetime
from spiders.common_spider import local_tz, date_handler
import json
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
        time = datetime.strptime(i.span.get_text(), '%m/%d/%y').replace(hour=17, tzinfo=local_tz)
        headline = i.find('div', attrs={'class': 'text_i'}).get_text(strip=True)
        headlines.append({'href': href, 'time': time, 'headline': headline, 'source': 'mf'})
    return headlines

def minfin_headlines():
    headlines = []
    for url in ['http://www.minfin.gov.ua/news/borg/zovnishni-suverenni-zobovjazannja',
                'http://www.minfin.gov.ua/news/novini-ta-media']:
        headlines += minfin_headlines_url(url)
    return headlines

if __name__ == '__main__':
    print(json.dumps(minfin_headlines(), sort_keys=True, indent=4, separators=(',', ': '),
                     ensure_ascii=False, default=date_handler))

