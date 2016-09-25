# TODO:
# http://www.ukrstat.gov.ua/operativ/operativ2016/zd/tsztt/tsztt_u/tsztt0216_u.htm

import json
from datetime import datetime

import requests
from functools import reduce
from bs4 import BeautifulSoup

from spiders import parameters
from spiders.check_proxy import proxy_is_used
from spiders.common_spider import date_handler, local_tz, current_datetime_tz
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

class ukrstat():
    def __init__(self):
        self.url = 'http://www.ukrstat.gov.ua/operativ'

    def saldo(self) -> list:
        """
        data from two tables on http://www.ukrstat.gov.ua/imf/arhiv/ztorg_u.htm
        :return: list of documents
        [{
        '_id': '',
        'export': '',
        'import': '',
        'source': 'ukrstat'}]
        """
        self.url = 'http://www.ukrstat.gov.ua/imf/arhiv/ztorg_u.htm'
        response_get = requests.get(self.url)
        soup = BeautifulSoup(response_get.content.decode('1251'), 'html.parser')
        title = 'Зовнішня торгівля товарами'

        assert soup.head.title.get_text(strip=True) == title, 'wrong page info'
        tables = soup.find_all('table')
        tables_types = {0: 'export',
                        1: 'import'}
        assert len(tables) == 2, 'wrong tables'
        out_list = []
        for type_ in tables_types:
            for row in tables[type_].find_all('tr')[1:]:
                cells = row.find_all('td')
                assert len(cells) == 13, 'wrong cells number'
                # in first cell year, slice [:4] for limint chars in string,
                # this will folter such numbers '20141' to '2014'
                year = int(cells[0].get_text(strip=True)[:4])
                month = 1
                for cell in cells[1:]:
                    doc = {}
                    doc['_id'] = datetime(year=year, month=month, day=1, hour=17, minute=0, tzinfo=local_tz)
                    month += 1
                    value = cell.get_text(strip=True)
                    patern = r'[0-9]'
                    if not re.match(patern, value):
                        break   # if no numbers in cell, last cell not filled

                    # TODO: could be problem in future with numbers biger then 4 digits
                    value = ''.join(filter(lambda x: x.isdigit(), value))
                    value = float(value[:4])
                    doc[tables_types[type_]] = value
                    doc['source'] = 'ukrstat'
                    out_list.append(doc)
        assert len(out_list)%2 == 0, 'wrong number of cells'
        # {**doc1, **doc2} - new syntax in 3.5, merge 2 dicts
        result = [{**doc1, **doc2} for doc1, doc2 in zip(out_list[:int(len(out_list) / 2)],
                                                         out_list[int(len(out_list) / 2):])]
        return result






class ukrstat_o():
    def __init__(self):
        self.url = 'http://oblstat.kiev.ukrstat.gov.ua/content/p.php3'
        self.current_year = current_datetime_tz().strftime('%Y')

    def building_index(self) -> list:
        """
        http://oblstat.kiev.ukrstat.gov.ua/content/p.php3?lang=1&c=955
        :return: list of index for current year
        [{
        '_id': '',
        'index': '',
        'source' 'ukrstat_obl_k'
        },]
        """
        params = {'c': '955', 'lang': '1'}
        response_get = requests.get(self.url, params=params)
        soup = BeautifulSoup(response_get.content.decode('1251'), 'html.parser')
        search_string = 'Індекси будівельної продукції за видами у ' + self.current_year + ' році'

        assert len(soup.body.find_all(string=search_string)) == 1, 'wrong page info'
        string = soup.body.find(string='житлові').parent.parent.parent
        values = string.find_all(string=re.compile('[0-9]'))
        out_list = []
        for month in range(1, len(values) + 1):
            doc = {}
            doc['_id'] = datetime(year=int(self.current_year), month=month, day=1, hour=17, minute=0, tzinfo=local_tz)
            doc['index'] = float(values[month - 1].replace(',', '.'))
            doc['source'] = 'ukrstat_obl_k'
            out_list.append(doc)
        return out_list

    def housing_meters(self) -> dict:
        """
        http://oblstat.kiev.ukrstat.gov.ua/content/p.php3?c=956&lang=1
        :return: dict, m2 in region in quoter period
        [{
        '_id': '',
        'granularity': '',
        'm2_sum': '',
        'index_sum': '',
        'm2_city': '',
        'index_city': '',
        'source': 'ukrstat_obl_k'
        },]
        """
        params = {'c': '956', 'lang': '1'}
        response_get = requests.get(self.url, params=params)
        content = response_get.content.decode('1251')
        # rmoves tag <b></b> from content
        tags_to_remove = ('<b>', '</b>', '<B>', '</B>')
        content = reduce(lambda input, val: input.replace(val, ''), tags_to_remove, content)
        soup = BeautifulSoup(content, 'html.parser')
        patern = r'^Прийняття в експлуатацію.*[^)]$'
        table_title = soup.body.find(string=re.compile(patern))

        assert table_title.string.find(self.current_year) != -1, 'wrong page info \'year\' != ' + self.current_year
        table = table_title.find_parent('table')
        string = table.find(string='Київська область').find_parent('tr')
        values = string.find_all(string=re.compile('[0-9]'))
        assert len(values) == 4, 'wrong data in values'
        doc = {}
        granularity_dict = {'січні–березні': 3, 'січні-червні': 6, 'січні-вересні': 9, 'січні-грудні': 12}
        for month in granularity_dict:
            if table_title.string.find(month) != -1:
                doc['_id'] = datetime(year=datetime.now().year, month=granularity_dict[month], day=1, hour=17, minute=0,
                                      tzinfo=local_tz)
                break
        assert doc.get('_id') is not None, 'can\'t get correct period value'
        doc['granularity'] = 3
        doc['source'] = 'ukrstat_obl_k'
        for key in ['m2_sum', 'index_sum', 'm2_city', 'index_city']:
            doc[key] = values.pop(0)
        return doc





if __name__ == '__main__':
    # print(json.dumps(import_stat(datetime.strptime('2006-12', '%Y-%m')), sort_keys=True, indent=4,
    #       separators=(',', ': '), ensure_ascii=False, default=date_handler))
    # print(json.dumps(import_stat(datetime.strptime('2016-04', '%Y-%m')), sort_keys=True, indent=4,
    #       separators=(',', ': '), ensure_ascii=False, default=date_handler))
    # print(json.dumps(ukrstat_o().building_index(), sort_keys=True, indent=4, separators=(',', ': '),
    #                  ensure_ascii=False, default=date_handler))
    print(json.dumps(ukrstat().saldo(), sort_keys=True, indent=4, separators=(',', ': '),
                     ensure_ascii=False, default=date_handler))

