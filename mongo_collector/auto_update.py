from time import sleep
from .mongo_update import update_db

records_update_time = 300

while True:
    update_db()
    sleep(records_update_time)