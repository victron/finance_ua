# TODO:
# http://www.ukrstat.gov.ua/operativ/operativ2016/zd/tsztt/tsztt_u/tsztt0216_u.htm

import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from spiders import parameters
from spiders.check_proxy import proxy_is_used
from spiders.common_spider import date_handler, local_tz
import re


# internet settings
user_agent = parameters.user_agent
headers = {'user-agent': user_agent}
proxies = parameters.proxies

def import_stat(date) -> dict:
    year = date.strftime('%Y')
    month_year = date.strftime('%m%y')
    url = 'http://www.ukrstat.gov.ua/operativ/operativ' + year + '/zd/tsztt/tsztt_u/tsztt' \
          + month_year + '_u.htm'
    if proxy_is_used == False:
        responce_get = requests.get(url, headers=headers)
    else:
        responce_get = requests.get(url, headers=headers, timeout=3, proxies=proxies)

    soup = BeautifulSoup(responce_get.content.decode('1251'), 'html.parser')

    marker = soup.find(string = re.compile('Усього'))
    if marker == None:
        marker = soup.find(string=re.compile('Всього'))
    if marker ==None:
        return None

    data_string = marker.find_parent('tr')
    data_list = data_string.find_all('td')
    if data_list == []:
        data_list = data_string.find_all('span')
        delete_el = data_string.find('span', attrs={'lang': 'EN-US'})
        if delete_el in data_list:
            data_list.remove(delete_el)

    out_dict = {}
    out_dict['export'] = float(data_list[1].get_text().replace(',', '.'))
    out_dict['import'] = float(data_list[4].get_text().replace(',', '.'))
    out_dict['_id'] = datetime.strptime(month_year, '%m%y').replace(day=1, hour=17, minute=0, tzinfo=local_tz)
    out_dict['source'] = 'ukrstat'
    return out_dict




if __name__ == '__main__':
    print(json.dumps(import_stat(datetime.strptime('2006-12', '%Y-%m')), sort_keys=True, indent=4,
          separators=(',', ': '), ensure_ascii=False, default=date_handler))


