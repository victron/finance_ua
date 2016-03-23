
import parameters
from tables import print_table_as_is, reform_table_fix_columns_sizes
import finance_ua
import parse_minfin
import berlox
from time import sleep
from importlib import reload


# constans, user settings
table_column_size = parameters.table_column_size


while True:
    fin_ua = finance_ua.table_api_finance_ua(finance_ua.fetch_data)
    table = fin_ua + parse_minfin.table + berlox.table
    table = reform_table_fix_columns_sizes(table, table_column_size)
    print_table_as_is(table)
    for i in range(parameters.sleep_time, 0, -1):
        # '\r' return caret but not go to new line '\n'
        print('update in {0} sec.\r'.format(i), end='')
        sleep(1)
    reload(finance_ua)
    reload(parse_minfin)
    reload(berlox)





