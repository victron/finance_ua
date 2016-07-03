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
from mongo_collector.mongo_update import mongo_add_fields
from spiders.ukrstat import ukrstat, ukrstat_o

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



logger.info('initial update')

auto_list_update = scheduler.add_job(update_lists, 'interval', name='auto_list_update', minutes=5,
                                     id='auto_list_update',
                                     next_run_time=datetime.now(kiev_tz) + timedelta(minutes=1)) # initial update in 1m
auto_news_update = scheduler.add_job(update_news, 'interval', name='auto_news_update', minutes=30,
                                     id='auto_news_update',
                                     next_run_time=datetime.now(kiev_tz) + timedelta(minutes=1, seconds=30))
def ukrstat_shadow():
    mongo_add_fields(ukrstat().saldo())
    mongo_add_fields(ukrstat_o().building_index())
    mongo_add_fields([ukrstat_o().housing_meters()])

auto_ukrstat_month = scheduler.add_job(ukrstat_shadow, 'interval', id='auto_ukrstat_update', replace_existing=True,
                                       name='auto_ukrstat_update', days=10, jobstore='longTerm')
logger.info('start auto update')
scheduler.start()

