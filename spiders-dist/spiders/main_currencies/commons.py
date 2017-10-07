from pymongo import collection
from collections import namedtuple
import logging

logger = logging.getLogger(__name__)

# symbols mapper to different sources

                    # symbols converter
                    #   (GOOGLE, investing.com, YAHOO)
sympols = {"USDCHF": ("USDCHF", None,       "CHF=X"),
           "EURUSD": ("EURUSD", None,       "EUR=X"),
           "USDJPY": ("USDJPY", None,       None),
           "USDCAD": ("USDCAD", None,       None),
           "NZDUSD": ("NZDUSD", None,       None),
           "AUDUSD": ("AUDUSD", None,       None),
           "GBPUSD": ("GBPUSD", None,       None),
           "XAUUSD": (None,     "xau-usd",  "XAUUSD=X"),
           "XAGUSD": (None,     "xag-usd",  "XAGUSD=X"),
           }

# symbols converter
#   (investing.com, YAHOO)
sympols_commodities = {"IRONORE":("iron-ore-62-cfr-futures", None)
                       }

def mongo_multi_column(docs: list, collect: collection) -> namedtuple:
    """
    docs == [{  "time": datetime,
                <symbol>: float}, ]
    :param docs:
    :param collection:
    :return:
    """
    duplicate_count = 0     # not used at that moment, need additional find before update
    new_doc_count = 0
    modified_count = 0
    result = namedtuple('result', ['new_doc_count', 'modified_count', 'duplicate_count'])
    if docs == []:
        logger.warning("empty docs list")
        return result(new_doc_count, modified_count, duplicate_count)
    for doc in docs:
        time = doc["time"]
        document = dict(doc)
        logger.debug("time= {}, document= {}".format(time, document))
        update_result = collect.update_one({'time': time}, {'$set': document}, upsert=True)
        if update_result.upserted_id is not None:
            new_doc_count += 1
        modified_count += update_result.modified_count
    return result(new_doc_count, modified_count, duplicate_count)