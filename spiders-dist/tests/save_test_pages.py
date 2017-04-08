import requests
from collections import namedtuple
from os import path
import pickle
from spiders import parameters


data_path = path.join('data', 'pages', '')
location = 'kiev'
user_agent = parameters.user_agent
headers = {'user-agent': user_agent}
operations = ('sell', 'buy')
currencies = ('USD', 'EUR', 'RUB')



# dictionary (operation, currency) maping to filenames
files = {}
filemap = namedtuple('filemap', 'operation currency source')
files_res = namedtuple('files', 'page cookie parse_data parse_session')
source = 'm'
for operation in operations:
    for currency in currencies:
        key = filemap(operation=operation, currency=currency, source=source)
        page = ''.join([data_path,
                        key.source, '_', key.operation, '_', key.currency, '.bin'])
        cookie = ''.join([data_path,
                        key.source, '_', key.operation, '_', key.currency, '.cook'])
        data = ''.join([data_path,
                        key.source, '_', key.operation, '_', key.currency, '.json'])
        session = ''.join([data_path,
                        key.source, '_', key.operation, '_', key.currency, '.sesion'])
        files[key] = files_res(page=page, cookie=cookie, parse_data=data, parse_session=session)

def gen_files_del() -> dict:
    """
    generate filemaping with deleted records
    :return:
    """
    files_del = {}
    filemap = namedtuple('filemap', 'operation currency source')
    files_res = namedtuple('files', 'page cookie parse_data parse_session')
    source = 'm'
    for operation in operations:
        for currency in currencies:
            key = filemap(operation=operation, currency=currency, source=source)
            page = ''.join([data_path,
                            key.source, '_', key.operation, '_', key.currency, '.bin.del'])
            cookie = ''.join([data_path,
                            key.source, '_', key.operation, '_', key.currency, '.cook'])
            data = ''.join([data_path,
                            key.source, '_', key.operation, '_', key.currency, '.json'])
            session = ''.join([data_path,
                            key.source, '_', key.operation, '_', key.currency, '.sesion'])
            files_del[key] = files_res(page=page, cookie=cookie, parse_data=data, parse_session=session)
    return files_del


def minfin_pages():
    for operation in operations:
        for currency in currencies:
            url = 'http://minfin.com.ua/currency/auction/' + currency + '/' + operation + '/' + location + \
                    '/?presort=&sort=time&order=desc'
            responce_get = requests.get(url, headers=headers)
            key = filemap(currency=currency, operation=operation, source='m')
            filename = files[key]
            with open(filename.page, mode='wb') as f:
                f.write(responce_get.content)           # save page in file
            with open(filename.cookie, 'wb') as f:
                pickle.dump(responce_get.cookies, f)    # save cookies in file

if __name__ == '__main__':
    minfin_pages()
