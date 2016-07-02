from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor, BasePoolExecutor
import pytz
import sys
import os
import yaml
from mongo_collector.parallel import update_lists

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
                'max_instances': 1}

# BackgroundScheduler: use when you’re not using any of the frameworks,
# and want the scheduler to run in the background inside your application
# scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=kiev_tz)
# BlockingScheduler: use when the scheduler is the only thing running in your process
scheduler = BlockingScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=kiev_tz)


auto_list_update = scheduler.add_job(update_lists, 'interval', name='auto_list_update', minutes=1)
scheduler.start()

