from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor, BasePoolExecutor
import pytz
from app import app
from mongo_collector.parallel import update_lists

kiev_tz = pytz.timezone('Europe/Kiev')
jobstores = {'longTerm': MongoDBJobStore(),
             'default': MemoryJobStore()}

executors = {
    'default': ThreadPoolExecutor(),

}

job_defaults = {'coalesce': True,
                'max_instances': 1}

# scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=kiev_tz)
scheduler = BlockingScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=kiev_tz)


auto_list_update = scheduler.add_job(update_lists, 'interval', name='auto_list_update', seconds=30)
scheduler.start()

