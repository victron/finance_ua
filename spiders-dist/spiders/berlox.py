# -*- coding: utf-8 -*-

import json
import os
import zlib
from datetime import datetime

import requests
from Crypto.Cipher import AES

from spiders import filters
from spiders import parameters
from spiders.check_proxy import proxy_is_used
from spiders.simple_encrypt_import import secret
from spiders.common_spider import current_datetime_tz, date_handler, kyiv_tz
from spiders.tables import reform_table_fix_columns_sizes, print_table_as_is

# user settings
currency = filters.currency
conv_operation = {'buy' : 0,
                  'sell' : 1}
conv_operation_orig = {0 : 'buy',
                       1 : 'sell'}
operation = conv_operation[filters.operation]
location = filters.location
################  filter data  ################

baseKey = secret.baseKey
Vector = secret.Vector
current_key = secret.current_key

conv_dict = {'d' : 'd',
            'bid' :'did',
            'uid': 'uid',
            'sid':  'sid',
            'time': 't',
            'operation': 'x',
            'currency': 'c',
            'location': 'l',
            'amount': 'a',
            'rate': 'r',
            'phone': 'p',
            'pr': 'pr',
            'comment': 'cm'}

conv_dict_orig = {'d' : 'd',
                'did' :'bid',
                'uid': 'uid',
                'sid':  'sid',
                't': 'time',
                'x': 'operation',
                'c': 'currency',
                'l': 'location',
                'a': 'amount',
                'r': 'rate',
                'p': 'phone',
                'pr': 'pr',
                'cm': 'comment'}

# @timer()
def fetch_data():
    def decrypt_file(key, iv, in_file, out_file=None, chunksize=24*1024):
        """
        Function not in use, just for reference
        http://eli.thegreenplace.net/2010/06/25/aes-encryption-of-files-in-python-with-pycrypto
        :param key:
        :param iv:  initialization vector (IV), For maximal security, the IV should be randomly generated for every new
                    encryption and can be stored together with the ciphertext. Knowledge of the IV won't help the attacker
                    crack your encryption. What can help him, however, is your reusing the same IV with the same
                    encryption key for multiple encryptions.
        :param in_file: ecrypted file
        :param out_file: decrypted file
        :param chunksize:Sets the size of the chunk which the function
                        uses to read and encrypt the file. Larger chunk
                        sizes can be faster for some files and machines.
                        chunksize must be divisible by 16.
        :return: decrypted file
        """
        if not out_file:
            out_file = os.path.splitext(in_file)[0]

        decryptor = AES.new(key, AES.MODE_CBC, iv)
        with open(in_file, 'rb') as infile:
            # data = infile.read()

            with open(out_file, 'wb') as outfile:
                while True:
                    chunk = infile.read(chunksize)
                    if len(chunk) == 0:
                        break
                    outfile.write(decryptor.decrypt(chunk))

    def get_belox_data(proxy_is_used: bool = False) -> requests:
        url = 'http://berlox.com/finance/listz.bin'
        # print('--------------- berlox fetch -------------')
        resp = requests.get(url).content
        return resp
            # return requests.get(url, proxies=proxies)


    def decrypt_data(key, iv, data, decompress = True):
        """
        decrypt data
        :param key: bytes key
        :param iv: bytes initialization vector
        :param data: bytes
        :return: byyes decrypted data
        """
        decryptor = AES.new(key, AES.MODE_CBC, iv)
        data = decryptor.decrypt(data)
        if decompress:
            decompress = zlib.decompressobj(16+zlib.MAX_WBITS)
            return decompress.decompress(data)
        else:
            return data

    return json.loads(decrypt_data(current_key(), Vector, get_belox_data(proxy_is_used)).decode())

# @timer()
def data_api_berlox(fn_fetch):
    def convertor_berlox(id: int, dic: dict, current_date: datetime) -> dict:
        out_dic = {}
        for key, item in dic.items():
            out_dic[conv_dict_orig[key]] = item
        out_dic['operation'] = conv_operation_orig[out_dic['operation']]
        # out_dic['id'] = id
        out_dic['source'] = 'b'
        try:
            out_dic['time'] = datetime.strptime(out_dic['time'], '%Y-%m-%dT%H:%M:%S')
            out_dic['time'] = kyiv_tz.localize(out_dic['time'])
        except ValueError:
            try:
                out_dic['time'] = datetime.strptime(out_dic['time'], '%Y-%m-%dT%H:%M:%S.%f%z')
            except ValueError:
                out_dic['time'] = datetime.strptime(out_dic['time'][:19], '%Y-%m-%dT%H:%M:%S')
                out_dic['time'] = kyiv_tz.localize(out_dic['time'])
        return out_dic
    data = fn_fetch()
    current_date = current_datetime_tz()
    # print(len(data['Deals']))
    return [convertor_berlox(index, dic, current_date) for index, dic in enumerate(data['Deals'])]


def table_api_berlox(fn_fetch):
    def filter_data_json(data: dict, keyword: str) -> list:
        """
        :type data: {"Timestamp":"2016-03-02T13:00:10.852488+02:00",
                    "Cities":["Бровары","Винница","Киев"],
                    "Deals":[
                    {"d":false,
                    "did":"6d14236297b947aca9f43dc7c0883f9b",
                    "uid":"960-600-195",
                    "sid":1,
                    "t":"2016-03-02T13:00:00",
                    "x":0,
                    "c":"USD",
                    "l":'Киев',
                    "a":10000,
                    "r":27.0,
                    "p":"+380664529055",
                    "pr":null,
                    "cm":"Ленинградская площадь (военторг), от 100"},
        """
        # return [dic[conv_dict['bid']] for dic in data['Deals']
        #         if dic[conv_dict['comment']].lower().find(keyword) != -1 and dic[conv_dict['location']] == location
        #             and dic[conv_dict['operation']] == operation and dic[conv_dict['currency']] == currency]

        return [index for index, dic in enumerate(data['Deals'])
                if dic[conv_dict['comment']].lower().find(keyword) != -1 and dic[conv_dict['location']] == location
                    and dic[conv_dict['operation']] == operation and dic[conv_dict['currency']] == currency]
    data = fn_fetch()
    filter_or = filters.filter_or.lower()
    filter_or = filter_or.split()
    filtered_set = set()
    for filter_ in filter_or:
        filtered_set = filtered_set.union(set(filter_data_json(data, filter_)))

    return [(data['Deals'][list_id][conv_dict['time']][11:-3], data['Deals'][list_id][conv_dict['currency']],
              conv_operation_orig[operation], str(data['Deals'][list_id][conv_dict['rate']]),
              str(data['Deals'][list_id][conv_dict['amount']]), location,
              data['Deals'][list_id][conv_dict['comment']], data['Deals'][list_id][conv_dict['phone']], 'b')
               for list_id in filtered_set]


if __name__ == '__main__':
    table = reform_table_fix_columns_sizes(table_api_berlox(fetch_data), parameters.table_column_size)
    print(json.dumps(data_api_berlox(fetch_data), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False,
                     default=date_handler))
    print_table_as_is(table)