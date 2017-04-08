import pickle
import requests
from bs4 import BeautifulSoup

from common import DATA_PATH, url_to_file

# for url, file_name in url_to_file.items():
#     with open(DATA_PATH + file_name, 'wb') as f:
#         data = requests.get(url)
#         pickle.dump(data, f)

headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Encoding': 'gzip, deflate',
           'Accept-Language': 'uk,en-US;q=0.8,en;q=0.5,ru;q=0.3',
           'Cache-Control': 'no-cache',
           'Connection': 'keep-alive',
           'Content-Length': '0',
           'DNT': '1',
           'Host': 'markets.businessinsider.com',
           'Pragma': 'no-cache',
           'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0',
           }
with open(DATA_PATH + 'history_post1_responce.pickle', 'wb') as f:

    url = 'http://markets.businessinsider.com/commodities/historical-prices/iron-ore-price/1.1.2014_28.3.2017'

    responce_post1 = requests.post(url, headers=headers)
    print(responce_post1)
    pickle.dump(responce_post1, f)

soup1 = BeautifulSoup(responce_post1.text, 'html.parser')
# modify headers for data collection
for key in ['__atts', '__ath', '__atcrv']:
    headers[key] = soup1.find('input', attrs={'name': key})['value']
    if key == '__atcrv':
        headers[key] = str(eval(headers[key]))

url2 = 'http://markets.businessinsider.com/Ajax/CommodityController_HistoricPriceList/iron-ore-price/USD/1.1.2014_28.3.2017'

params = {'type': 'Brent'}

responce_post2 = requests.post(url2, params=params, headers=headers)
print(responce_post2)
with open(DATA_PATH + 'history_post2_responce.pickle', 'wb') as f:
    pickle.dump(responce_post2, f)

