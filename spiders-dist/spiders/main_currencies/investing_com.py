import locale
import logging
from datetime import datetime, timezone

import requests
from lxml import html

from spiders.main_currencies.commons import mongo_multi_column, sympols, sympols_commodities
from spiders.mongo_start import main_currencies

logger = logging.getLogger(__name__)

def parse_investing(symbol: str) -> list:
    """

    :param symbol:
    :return: [{ "time": <datetime>,
                <symbol>: float}, ]
    """
    if sympols.get(symbol) is not None:
        site_symbol = sympols[symbol][1]
        url = "https://investing.com/currencies/" + site_symbol + "-historical-data"
    elif sympols_commodities.get(symbol) is not None:
        site_symbol = sympols_commodities[symbol][0]
        url = "https://www.investing.com/commodities/" + site_symbol + "-historical-data"
    else:
        site_symbol = None

    if site_symbol is None:
        logger.warning("no data for {} in INVESTING".format(symbol))
        return []

    headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'en-US;q=0.8,en;q=0.5;q=0.3',
               'Cache-Control': 'no-cache',
               'Connection': 'keep-alive',
               'Content-Length': '0',
               'DNT': '1',
               'Pragma': 'no-cache',
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0'}

    responce_get = requests.get(url, headers=headers)
    if responce_get.status_code != 200:
        logger.error("requested url= {}".format(url))
        logger.error("responce from investing.com = {}".format(responce_get.status_code))
        return []
    xpath = "/html/body/div[5]/section/div[9]/table[@id='curr_table']/tbody"
    tree = html.fromstring(responce_get.text)
    table = tree.xpath(xpath)

    locale.setlocale(locale.LC_ALL,'en_US.UTF-8')
    docs = []
    for row in table[0].xpath(".//tr"):
        doc = {}
        cells = [cell for cell in row.xpath(".//td")]
        doc["time"] = datetime.strptime(cells[0].text_content(), "%b %d, %Y").replace(tzinfo=timezone.utc)
        doc[symbol] = float(cells[1].text_content().replace(",", ""))
        docs.append(doc)

    return docs


def main_currencies_collect(currencies: list):
    """
    update main currencies according to input list
    :param currencies:
    :return:
    """
    #TODO: async io
    result_dict = {}
    for currency in currencies:
        result = mongo_multi_column(parse_investing(currency), main_currencies)
        logger.info("currency {}; new docs= {}, modif docs ={}"
                    .format(currency, result.new_doc_count, result.modified_count))

        result_dict[currency] = result
    return result_dict