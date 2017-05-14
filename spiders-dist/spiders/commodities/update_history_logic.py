from datetime import datetime, timezone, date, time, timedelta
from collections import namedtuple
from pymongo import collection
import logging


from spiders.mongo_start import commodities
from spiders.commodities import START_HISTORY_DATE
from spiders.commodities.businessinsider import available_commodities, history_commodity
from spiders.commodities.common_dict import businessinsder_key


logger = logging.getLogger(__name__)

def convert_bushel_tonn(key: str, val: float) -> float:
    """
    on businessinsider some data in USc per Bushel; check if need convert in tons, and convert it
     
    :param key: 
    :param val: 
    :return: 
    """
    multiplires = {'corn': 39.3680, 'oats': 64.8420, 'soybean': 36.7440,
                   'soybeans_oil': 2204.622621848776, 'sugar': 2204.622621848776, 'rice': 19.6841305522}
    if key in multiplires.keys():
        return round(val * multiplires[key], 2)
    else:
        return val


def get_previous_value(commodity: str, current_time: datetime, collection_: collection) -> dict:
    """
    
    :param commodity: 
    :param current_time: 
    :param collection_: 
    :return: dict of previous data for  commodity
    { "_id" : datetime,  'commodity': 185.66 }
    """
    doc = collection_.find_one({commodity: {'$exists': True}, '_id': {'$lt': current_time}},
                               projection={commodity: True},
                               sort=[('_id', -1)], limit=1)
    logger.debug('previous data for {} = {}'.format(commodity, doc))
    return doc


def allowed_to_insert(input_doc: dict, collection_: collection) -> bool:
    """
    There is logic to decide insert or not value in DB
    compare curent value with previous, if current lower or bigger then previous in 'k' 
    times - don't insert
    :param input_doc: {'rhodium': 1015.0, 'time': datetime}; received data for commodity
    :param collection_: 
    :return: allowed to insert or not True / False
    """
    k = 2   # multiplier for top and down edge
    if len(input_doc) > 2:
        raise IndexError('more then 2 elements in dict= {}'.format(input_doc))
    doc = dict(input_doc)
    current_time = doc.pop('time')
    keys = list(doc.keys())
    commodity = keys[0]
    # convert in tonns if val in bushel
    doc[commodity] = convert_bushel_tonn(commodity, doc[commodity])
    previous_doc = get_previous_value(commodity, current_time, collection_)
    if previous_doc is None:
        logger.warning('data for commodity= {}, early then= {} - not found; '
                       'suspecting new data correct'.format(commodity, current_time))
        return True
    if previous_doc[commodity] / k < doc[commodity] < previous_doc[commodity] * k:
        logger.debug('current value= {} of commodity= {} - in OK range'.format(doc[commodity], commodity))
        return True
    else:
        logger.warning('current value= {} of commodity= {} - in Nok range'.format(doc[commodity], commodity))
        logger.warning('currentcommodity= {}; previous commodity= {}'.format(doc, previous_doc))
        return False


def update_history(docs: list, collection_: collection) -> namedtuple:
    """
    input like:
    [{'rhodium': 1015.0, 'time': datetime.datetime(2017, 3, 24, 0, 0, tzinfo=<UTC>)}, 
    {'iron-ore-price': 88.35, 'time': datetime.datetime(2017, 3, 24, 0, 0, tzinfo=<UTC>)}, 
    {'copper-price': 5804.76, 'time': datetime.datetime(2017, 3, 24, 0, 0, tzinfo=<UTC>)}]
    collection like timeseries DB, modify or add field in collection for time (which is _id in DB) 
    :param docs: list({'time': datetime, <commodity_name>: float})
    :param collection_: DATABASE['commodities']
    :return: namedtuple('update_history', ['matched_count', 'modified_count', 'upserted'])
    """
    result_obj = namedtuple('update_history', ['matched_count', 'modified_count', 'upserted'])
    matched_count, modified_count, upserted = 0, 0, 0
    for doc in docs:
        if not allowed_to_insert(doc, collection_):
            continue
        _id = doc.pop('time')   # remove key 'time', and set value to _id
        keys = list(doc.keys())
        # convert into metric
        doc[keys[0]] = convert_bushel_tonn(keys[0], doc[keys[0]])
        update_result = collection_.update_one({'_id': _id}, {'$set': doc}, upsert=True)
        matched_count += update_result.matched_count
        modified_count += update_result.modified_count
        logger.debug('updating in DB doc= {}'.format(doc))
        if update_result.upserted_id is not None:
            upserted += 1
    result = result_obj(matched_count=matched_count, modified_count=modified_count, upserted=upserted)
    logger.info('"update_history" result= {}'.format(result))
    return result

def check_commodities_collection(commudities_list: list) -> dict:
    """ help function for update_commudities_collection
    checks collection state,
    :param commudities_list: 
    :return: dict with date or None of last update for every commodity from list
    """
    current_date = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)
    collection_state = {}   # key= commodity_field, val= last present date
    for commodity in commudities_list:
        day = current_date
        while day >= current_date - timedelta(days=10):
            day -= timedelta(days=1)
            result_find = commodities.find_one({'_id': day, available_commodities()[commodity]: {'$exists': True}})
            if result_find is not None:
                logger.info('found data in DB {}'.format(result_find))
                collection_state[commodity] = day
                break
            logger.debug('no data for {} in DB on {}'.format(commodity, day))
            collection_state[commodity] = None
        logger.info('no data for {} in collection for last 10 days'.format(commodity))
    return collection_state


def update_commudities_collection(commudities_list: list) -> list:
    try:
        commudities_site = [businessinsder_key[c] for c in commudities_list]
    except KeyError as e:
        logger.error('commodity {} not in businessinsder_key dict'.format(e))
        raise e
    current_date = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)
    start_10_days = current_date - timedelta(10)
    sum_result = namedtuple('commodities_update', 'commodity result')
    results = []
    for commodity, update_date in check_commodities_collection(commudities_site).items():
        if update_date is None:
            logger.info('trying to get ALL BUSINESSINSIDER history for {}, starting {} till {}'
                        .format(commodity, START_HISTORY_DATE, current_date))
            result = update_history(history_commodity(commodity, START_HISTORY_DATE, current_date), commodities)
        else:
            logger.info('trying to get 10-days BUSINESSINSIDER history for {}, starting {} till {}'
                        .format(commodity, start_10_days, current_date))
            result = update_history(history_commodity(commodity, start_10_days, current_date), commodities)
        results.append(sum_result(commodity=commodity, result=result))
    return results
