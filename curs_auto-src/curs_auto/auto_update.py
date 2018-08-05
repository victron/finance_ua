import logging.config
import os
import sys
from datetime import datetime, timedelta

import pytz
import yaml
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.blocking import BlockingScheduler
from curs_auto.mongo_worker.mongo_collect_history import agg_daily_stat, move_old_records
from curs_auto.mongo_worker.mongo_collect_history import hourly_history

from curs_auto import rest_client
from curs_auto.bonds import update_bonds
from curs_auto.money_aggregators import collect_nbu_aggregators
from curs_auto.mongo_worker.mongo_periodic import ukrstat_shadow
from curs_auto.swaps import collect_nbu_swaps

logging_config = os.path.join(sys.prefix, '.curs_auto', 'logging.yml')
# get 'logging.yml' file from 'config' folder when running on dev machine
if not os.path.isfile(logging_config):
    logging_config = os.path.join('config', 'logging.yml')
logging.config.dictConfig(yaml.load(open(logging_config, 'r')))

logger = logging.getLogger('curs_auto')

UPDATE_COMMODITIES = ['corn', 'iron_ore', 'oats', 'oil_brent', 'soybean_meal', 'soybeans_oil', 'soybeans',
                      'sugar', 'wheat', 'sunflower_oil']
MAIN_CURRENCIES = ["EURUSD", "USDJPY", "USDCHF", "USDCAD", "NZDUSD", "AUDUSD", "GBPUSD"]
INVESTING_COM = ["XAUUSD", "XAGUSD", "IRONORE"]

kiev_tz = pytz.timezone('Europe/Kiev')
jobstores = {'longTerm': MongoDBJobStore(),
             'default': MemoryJobStore()}

executors = {
    'default': ThreadPoolExecutor(),

}

job_defaults = {'coalesce': True,
                'max_instances': 1,
                'next_run_time': datetime.now(kiev_tz) + timedelta(minutes=1), # currently not working
                'replace_existing': True}

# BackgroundScheduler: use when you’re not using any of the frameworks,
# and want the scheduler to run in the background inside your application
# scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=kiev_tz)
# BlockingScheduler: use when the scheduler is the only thing running in your process
scheduler = BlockingScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=kiev_tz)

auto_list_update = scheduler.add_job(rest_client.update, 'interval', args=['lists'], name='auto_list_update',
                                     minutes=5, id='auto_list_update',
                                     next_run_time=datetime.now(kiev_tz) + timedelta(minutes=1)) # initial update in 1m
auto_news_update = scheduler.add_job(rest_client.update, 'interval', args=['news'], name='auto_news_update',
                                     #TODO: for test minutes=1
                                     minutes=30, id='auto_news_update',
                                     next_run_time=datetime.now(kiev_tz) + timedelta(minutes=1, seconds=30))
hour_stat = scheduler.add_job(hourly_history, 'cron', name='hour_stat', minute=55, id='hour_stat',
                              replace_existing=True, jobstore='longTerm')
daily_stat = scheduler.add_job(agg_daily_stat, 'cron', name='daily_stat', hour=18, minute=53, id='daily_stat',
                               replace_existing=True, jobstore='longTerm')
daily_bonds = scheduler.add_job(update_bonds, 'cron', name='daily_bonds', hour=18, minute=50, id='daily_bonds',
                                replace_existing=True, jobstore='longTerm', args=[True])
daily_swaps = scheduler.add_job(collect_nbu_swaps, 'cron', name='daily_swaps', hour=18, minute=5, id='daily_swaps',
                                replace_existing=True, jobstore='longTerm')
i = 0
for commodity in UPDATE_COMMODITIES:
    scheduler.add_job(rest_client.update_dict, 'interval',
                                      args=[{**{'update': 'commodities'}, **{'list': [commodity]}}],
                                      name='auto_' + commodity, hours=4, id='auto_' + commodity,
                                      next_run_time=datetime.now(kiev_tz) + timedelta(minutes=10 + i))
    i += 1

main_currencies = scheduler.add_job(rest_client.update_dict, 'interval',
                                    args=[{**{'update': 'main_currencies'}, **{'list': MAIN_CURRENCIES}}],
                                    name='auto_' + 'main_currencies', hours=4, id='auto_' + 'main_currencies',
                                    next_run_time=datetime.now(kiev_tz) + timedelta(minutes=45))  # for debug minutes=45
main_currencies2 = scheduler.add_job(rest_client.update_dict, 'interval',
                                    args=[{**{'update': 'investing'}, **{'list': INVESTING_COM}}],
                                    name='auto_' + 'investing', hours=4, id='auto_' + 'investing',
                                    next_run_time=datetime.now(kiev_tz) + timedelta(minutes=48))


# Todo: aspscheduler problem
# problem with aspscheduler, try to move to another module
auto_ukrstat_month = scheduler.add_job(ukrstat_shadow, 'cron', id='auto_ukrstat_update', replace_existing=True,
                                       name='auto_ukrstat_update', hour=16, minute=15, jobstore='longTerm')
monthly_aggregators = scheduler.add_job(collect_nbu_aggregators, 'cron', name='monthly_aggregators', hour=13, minute=45,
                                        id='monthly_aggregators', replace_existing=True, jobstore='longTerm')
def main():
    logger.debug('start auto update')
    # For BlockingScheduler, you will only want to call start() after you’re done with any initialization steps.
    scheduler.start()


if __name__ == '__main__':
    main()




