from time import sleep
from .mongo_update import update_lists

records_update_time = 300

while True:
    update_lists()
    sleep(records_update_time)