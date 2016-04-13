from importlib import reload
from time import sleep

from spiders import berlox, finance_ua, parameters, parse_minfin
from spiders.tables import print_table_as_is, reform_table_fix_columns_sizes

# constans, user settings
table_column_size = parameters.table_column_size


while True:

    table = finance_ua.table_api_finance_ua(finance_ua.fetch_data) + \
            parse_minfin.table_api_minfin(parse_minfin.get_triple_data, parse_minfin.get_contacts) + \
            berlox.table_api_berlox(berlox.fetch_data)
    table = reform_table_fix_columns_sizes(table, table_column_size)
    print_table_as_is(table)
    for i in range(parameters.sleep_time, 0, -1):
        # '\r' return caret but not go to new line '\n'
        print('update in {0} sec.\r'.format(i), end='')
        sleep(1)
    reload(finance_ua)
    reload(parse_minfin)
    reload(berlox)





