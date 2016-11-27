from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor, BasePoolExecutor
from datetime import datetime, timedelta
import pytz
import sys
import os
import yaml
from mongo_collector.parallel import update_lists, update_news
from mongo_collector.mongo_periodic import ukrstat_shadow
from mongo_collector.mongo_collect_history import hourly_history
from mongo_collector.mongo_collect_history import agg_daily_stat, update_bonds
from mongo_collector.bonds import manual_bonds_insert, update_bonds
from mongo_collector.money_aggregators import collect_nbu_aggregators
from mongo_collector.swaps import collect_nbu_swaps

import logging.config
logging_config = os.path.join(sys.prefix, '.curs', 'logging.yml')
# get 'logging.yml' file from 'config' folder when running on dev machine
if not os.path.isfile(logging_config):
    logging_config = os.path.join('config', 'logging.yml')
logging.config.dictConfig(yaml.load(open(logging_config, 'r')))

logger = logging.getLogger('curs.mongo_collector.auto_update')


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

auto_list_update = scheduler.add_job(update_lists, 'interval', name='auto_list_update', minutes=5,
                                     id='auto_list_update',
                                     next_run_time=datetime.now(kiev_tz) + timedelta(minutes=1)) # initial update in 1m
auto_news_update = scheduler.add_job(update_news, 'interval', name='auto_news_update', minutes=30,
                                     id='auto_news_update',
                                     next_run_time=datetime.now(kiev_tz) + timedelta(minutes=1, seconds=30))
hour_stat = scheduler.add_job(hourly_history, 'cron', name='hour_stat', minute=55, id='hour_stat',
                              replace_existing=True, jobstore='longTerm')
daily_stat = scheduler.add_job(agg_daily_stat, 'cron', name='daily_stat', hour=18, minute=58, id='daily_stat',
                               replace_existing=True, jobstore='longTerm')
daily_bonds = scheduler.add_job(update_bonds, 'cron', name='daily_bonds', hour=18, minute=50, id='daily_bonds',
                                replace_existing=True, jobstore='longTerm', args=[True])
daily_swaps = scheduler.add_job(collect_nbu_swaps, 'cron', name='daily_swaps', hour=17, minute=45, id='daily_swaps',
                                replace_existing=True, jobstore='longTerm')

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




