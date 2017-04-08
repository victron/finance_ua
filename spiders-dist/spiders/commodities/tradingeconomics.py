# http://www.tradingeconomics.com/commodities
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import pytz
import logging

logger = logging.getLogger(__name__)

def available_commodities() -> dict:
    url = 'http://www.tradingeconomics.com/commodities'
    response_get = requests.get(url)
    soup = BeautifulSoup(response_get.text, 'html.parser')
    result = {}
    for row in soup.find_all('tr', attrs={'class': 'datatable-row', 'data-symbol': True}):
        result[row.b.get_text()] = row.a['href']
    return result


