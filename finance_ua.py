
# from sh import curl
# import sh
import requests
from ast import literal_eval
import parameters, filters
import json
from tables import print_table_as_is, reform_table_fix_columns_sizes
# constants and vars
# USD, EUR, PLN, GBP, RUB
currency = filters.currency.upper()
# buy -> 0
# sell -> 1
conv_operation = {'buy' : 0,
                  'sell' : 1}
contract_type = conv_operation[filters.operation]
conv_operation_orig = {0 : 'buy',
                       1 : 'sell',}

# city 
# Київ, Рівне, Львів
#city = u'Київ'
# change in API:
# key 'city' changed on 'location'
# locations looks like:
# Київ -> [2, {}]
# location = (u'Київ', [2, {}])
location = filters.location
location_dict = {'kiev' : 2}


filter_or = filters.filter_or

proxies = parameters.proxies
user_agent = parameters.user_agent
headers = {'user-agent': user_agent}

# old url
# url = 'http://tables.finance.ua/ua/currency/order/data?for=grid'
url = "http://miniaylo.finance.ua/data/for-table"

########## functions 
def filter_data(id_list, data_list, keyword, strict=False):
  result = []
  for Id in id_list:
    if data_list[Id].find(keyword) != -1:
      result.append(Id)
  return result

def print_result(id_list):
  # prety output curently not needed
  contract_dict = { 0 : 'buy',
                  1 : 'sell',}
  print (u'----- results for {currency} {contract} ------'.format(contract=contract_dict[contract_type], currency=currency))
  print (u'=== filter: location= {location}, filter= {filtered}'.format(location=location, filtered=u' '.join(filter_or)))
  print (u''.join([ '-' for i in range(70)]))
  for Id in id_list:
    print(u'{0} {1} {contract} {2} {amount:7.0f} {3} {4:30} {5}'.format(data['time'][Id], data['currency'][Id],
                                                                        data['rate'][Id], data['location'][Id],
                                                                        data['comment'][Id], data['phone'][Id],
                                                                        contract=contract_dict[data['type'][Id]],
                                                                        amount=data['amount'][Id]))

    
######## main block ############
# ---------- fetch via curl  ------------
# raw_data_file = 'finance_ua.txt'
# try:
#   curl(url, '-o', raw_data_file, '--user-agent', user_agent, '-m', '3')
# except sh.ErrorReturnCode_7:
#   curl(url, '-o', raw_data_file, '--user-agent', user_agent, '-x', proxy)
#
# with open(raw_data_file, 'r') as input_data:
#   raw_data = input_data.read()
#
# ------ fetch via requests ---------
try:
    responce_get = requests.get(url, headers=headers, timeout=3)
    proxy_is_used = False
except requests.exceptions.ConnectTimeout:
    responce_get = requests.get(url, headers=headers, timeout = 3,proxies=proxies)
  

start_dict = responce_get.text.find('({')
end_dict = responce_get.text.find('})')
data = responce_get.text[start_dict+1 : end_dict+1]

# data = eval(data)
data = literal_eval(data)
data_len = len(data['location'])

# -------- convert in general format --------
conv_dict_orig = {'id':'bid',
                  'location': 'location',
                  'time': 'time',
                  'currency': 'currency',
                  'type': 'operation',
                  'rate': 'rate',
                  'amount': 'amount',
                  'phone': 'phone',
                  'comment': 'comment',
                  'priority' : 'priority',}
location_dict_orig = {2 : 'Киев'}

def convertor_finance_ua(id: int) -> dict:
    out_dic = {conv_dict_orig[key] : data[key][id] for key in conv_dict_orig}
    out_dic['operation'] = conv_operation_orig[out_dic['operation']]
    # out_dic['id'] = id
    out_dic['location'] = location_dict_orig.get(out_dic['location'], 'None')
    out_dic['source'] = 'f'
    return out_dic

data_conv = [ convertor_finance_ua(i) for i in range(data_len)]
# ============================================================

# corect new data format to old
for index, val in  enumerate(data['location']):
  if val == location_dict[location]:
    data['location'][index] = location
  else:
    data['location'][index] = u'other'


# for python2
#decoder from escape to unicode and 'comment' in lower case
# for key in [ 'comment']:
#   for i in range(data_len):
#     data[key][i] = data[key][i].decode('unicode-escape')
#     if key == 'comment':
#       data[key][i] = data[key][i].lower()

for i in range(data_len):
  data['amount'][i] = data['amount'][i].replace(' ', '')
  data['amount'][i] = float(data['amount'][i])
# ---------------------------------
# filter by contract contract_type
contract_list = []
for i in range(data_len):
  if data['type'][i] == contract_type:
    contract_list.append(i)
    
# filter by currency
filtered_list = filter_data(contract_list, data['currency'],  currency)
filtered_list = filter_data(filtered_list, data['location'],  location)

# filter by keywords
filter_or = filter_or.lower()
filter_or = filter_or.split()
filtered_set = set()
for filter_  in  filter_or:
  filtered_set = filtered_set.union(set(filter_data(filtered_list, data['comment'],  filter_)))


table = [ (data['time'][Id], data['currency'][Id], conv_operation_orig[data['type'][Id]], data['rate'][Id],
           data['amount'][Id], data['location'][Id], data['comment'][Id], data['phone'][Id], 'f' ) for Id in filtered_set ]



if __name__ == '__main__':
    table = reform_table_fix_columns_sizes(table, parameters.table_column_size)
    print(json.dumps(data_conv, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False))
    print_table_as_is(table)




    
    




