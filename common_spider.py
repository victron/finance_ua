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


def time_string(doc):
    doc['time'] = doc['time'].strftime('%Y-%m-%d')
    return doc

# global variables
main_currencies = ['USD', 'UER', 'RUB']
operations = ['sell', 'buy']
local_tz = current_datetime_tz().tzinfo