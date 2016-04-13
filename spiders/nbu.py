import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from bs4.element import Comment

from spiders.common_spider import local_tz
from spiders.parameters import proxy_is_used, headers, proxies


# from check_proxy import proxy_requests

# TODO:
# - correct offten call current_datetime_tz
# + check nbu_rate in weekend

# from http://www.bank.gov.ua/control/uk/publish/article?art_id=25327817&cat_id=25365601
#  Розміщення облігацій по валюті (можливі значення UAH / USD / EUR, регістр значення не має):
# http://bank.gov.ua/NBUStatService/v1/statdirectory/ovdp?valcode=usd&json
# Індекс міжбанківських ставок за період
# (можливі значення для періоду OVERNIGHT / 1WEEK / 2WEEKS / 1MONTH / 3MONTHS, регістр значення не має):
# http://bank.gov.ua/NBUStatService/v1/statdirectory/uiir?period=1WEEK&date=YYYYMMDD
# Основні показники діяльності банків України
# http://www.bank.gov.ua/control/uk/publish/article?art_id=36807&cat_id=36798
# Оперативний стан міжбанківського валютного ринку України
# http://www.bank.gov.ua/control/uk/publish/article?art_id=9628619&cat_id=9628618


# Загальні результати валютного аукціону з продажу/купівлі валюти, проведеного Національним банком України
#  http://www.bank.gov.ua/control/uk/auction/details?date=23.03.2016&year=2016
# http://www.bank.gov.ua/control/uk/auction/details


def auction_get_dates(year: datetime) -> set:
    year = year.strftime('%Y')
    url = 'http://www.bank.gov.ua/control/uk/auction/details?date=25.03.2016&year=' + year
    if not proxy_is_used:
        responce_get = requests.get(url, headers=headers)
    else:
        responce_get = requests.get(url, headers=headers, timeout = 3, proxies=proxies)
    soup = BeautifulSoup(responce_get.text, "html.parser")
    # if year == soup.body.table.find(attrs={'name': 'year', 'onchange': 'this.form.submit();'}).find('option', attrs={'selected': ''})['value']:
    dates = set()
    for date in soup.body.table.find('select',attrs={'name': 'date'}).find_all('option'):
        dates.add(datetime.strptime(date['value'], '%d.%m.%Y')
                  .replace(hour=17, minute=0, microsecond=0, tzinfo=local_tz))
    return dates
    # else:
    #     return None


def auction_results(date: datetime) -> dict:
    date = date.strftime('%d.%m.%Y')
    year = date.split('.')[2]
    url = 'http://www.bank.gov.ua/control/uk/auction/details?date=' + date + '&year=' + year
    if not proxy_is_used:
        responce_get = requests.get(url, headers=headers)
    else:
        responce_get = requests.get(url, headers=headers, timeout = 3, proxies=proxies)
    soup = BeautifulSoup(responce_get.text, "html.parser")
    # if date != soup.body.table.find('option', attrs={'selected': ''})['value']:
    #     return None
    document = {}
    get_float = lambda tag: float(tag.find('td', attrs={'class': 'cell_c'}).get_text(strip=True))
    document['time'] = datetime.strptime(date, '%d.%m.%Y')\
        .replace(hour=17, minute=0, microsecond=0, tzinfo=local_tz)
    document['source'] = 'nbu_auction'
    for field in soup.body.table.find('table', attrs={'border': '0', 'width': '650px'}).find_all('tr'):
        if isinstance(field.td, type(None)):
            continue
        if field.td.string == 'Валюта аукціону':
            if field.td.next_sibling.next_sibling.get_text(strip=True) == 'Долар США':
                document['currency'] = 'USD'
            else:
                document['currency'] = None
        elif type(field.next_element) == Comment:
            if field.next_element == ' 1 # 1.0.1 || 1.0.2 ':
                if field.td.get_text(strip=True) == 'КУПІВЛЯ':
                    document['operation'] = 'buy'
                elif field.td.get_text(strip=True) == 'ПРОДАЖ':
                    document['operation'] = 'sell'
            elif field.next_element == ' 2 # 1.1 ':
                # Загальний обсяг заявок суб'єктів ринку, прийнятих на аукціон відповідно до умов його проведення (млн. од. валюти)
                document['amount_requested'] = get_float(field)
            elif field.next_element == ' 6 # 1.2.1 ':
                # Курси гривні, заявлені учасниками аукціону (грн. за 1 од. валюти)
                document['rate_r_max'] = get_float(field)
            elif field.next_element == ' 7 # 1.2.2 ':
                document['rate_r_min'] = get_float(field)
            elif field.next_element == ' 9 # 1.3.1 ':
                document['rate_acc_med'] = get_float(field)
            elif field.next_element == ' 10 # 1.3.2 ':
                document['rate_acc_max'] = get_float(field)
            elif field.next_element ==  ' 11 # 1.3.3 ':
                document['rate_acc_min'] = get_float(field)
            elif field.next_element == ' 12 # 1.4 ':
                # Загальний обсяг задоволених заявок учасників аукціону (млн. од. валюти)
                document['amount_accepted_all'] = get_float(field)
            elif field.next_element == ' 13 - 1.5 || 1.6 ':
                # Частка задоволених заявок за максимальним курсом аукціону в загальному обсязі задоволених заявок (%)
                document['amount_accepted_p_min_max'] = get_float(field)

    return document


class NbuJson():
    """
    http://www.bank.gov.ua/control/uk/publish/article?art_id=25327817&cat_id=25365601
    """
    def __init__(self):
        self.url = 'http://bank.gov.ua/NBUStatService/v1/statdirectory/exchange'

    def rates_current(self) -> json:
        return requests.get(self.url, params='json').json()

    def rates_date(self,date: datetime) -> json:
        params = {'date': date.strftime('%Y%m%d'), 'json': ''}
        return requests.get(self.url, params=params).json()

    def rate_currency_date(self, currency: str, date: datetime) -> dict:
        params = {'valcode': currency, 'date': date.strftime('%Y%m%d'), 'json': ''}
        document = {}
        try:
            recieved_doc = requests.get(self.url, params=params).json()[0]
        except IndexError:
            return {}
        document['currency'] = recieved_doc['cc']
        document['time'] = datetime.strptime(recieved_doc['exchangedate'], '%d.%m.%Y')\
            .replace(hour=17, minute=0, microsecond=0, tzinfo=local_tz)
        document['nbu_rate'] = recieved_doc['rate']
        document['source'] = 'nbu'
        return document


if __name__ == '__main__':
    year = '2016'
    # for i in auction_get_dates(datetime.strptime(year, '%Y')):
    #     print(json.dumps(auction_results(i), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False,
    #                      default=date_handler))
    #     sleep(10)
    # print(json.dumps(auction_results(datetime.strptime('23.03.2016', '%d.%m.%Y')), sort_keys=True, indent=4,
    #                  separators=(',', ': '), ensure_ascii=False, default=date_handler))
    # print(json.dumps(NbuJson().rate_currency_date('USD', datetime.strptime('27.03.2016', '%d.%m.%Y')),
    #                  sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False, default=date_handler))
    print(NbuJson().rate_currency_date('USD', datetime.strptime('27.03.2016', '%d.%m.%Y')))


