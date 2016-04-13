from bson import json_util
import pytz
from datetime import datetime, timezone, timedelta




def current_datetime_tz() -> datetime:
    """
    :return: curent time with local time zone
    """
    kiev_tz = pytz.timezone('Europe/Kiev')
    return datetime.now(timezone.utc).astimezone(kiev_tz)
    # below variant get timezone from diff between utc and local time
    # return datetime.now(timezone(timedelta(hours=(datetime.now().hour - datetime.utcnow().hour))))

def get_tzinfo() -> timedelta:
    # http://pytz.sourceforge.net/#tzinfo-api
    currnt_tz = pytz.timezone('Europe/Kiev')
    curent_time = datetime.now()
    return timezone(currnt_tz.utcoffset(curent_time))



def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj

def flatten(dictionary):
    stack = [((), dictionary)]
    result = {}
    while stack:
        path, current = stack.pop()
        if isinstance(current, dict):
            if len(current) != 0:
                for k, v in current.items():
                    stack.append((path + (k,), v))
            else:
                result["/".join(path )] = ""
        else:
            result["/".join(path )] = current
    return result




# global variables
main_currencies = ['USD', 'EUR', 'RUB']
operations = ['sell', 'buy']
# local_tz = current_datetime_tz().tzinfo # gives wrong tzinfo, difference in one hour, reason in dst
# local_tz = datetime.now(timezone(timedelta(hours=(datetime.now().hour - datetime.utcnow().hour)))).tzinfo
local_tz = get_tzinfo()