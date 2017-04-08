from collections import namedtuple
from time import sleep
import logging

from spiders.commodities.update_history_logic import update_commudities_collection
from spiders.commodities.graintrade import update_mongo
from spiders.commodities.common_dict import businessinsder_key, graintrade_key

logger = logging.getLogger(__name__)

def update_all(commodities: list):
    unknown_commodities = set(commodities).difference(set(businessinsder_key).union(graintrade_key))
    if unknown_commodities != set():
        logger.error('unknown commodities: {}'.format(unknown_commodities))
        raise NameError(unknown_commodities)
    businessinsder_set = set(businessinsder_key).intersection(commodities)  # set only for available commodities
    graintrade_set = set(graintrade_key).intersection(commodities)
    graintrade_result = update_mongo(graintrade_set)    # insert firstly from EURONEXT
    businessinsder_result = update_commudities_collection(businessinsder_set)
    # graintrade_result = []
    # all_fields = set(businessinsder_result._fields).union(graintrade_result._fields)
    # sum_dict = {k: businessinsder_result._asdict().get(k, 0) + graintrade_result._asdict().get(k, 0)
    #             for k in all_fields}
    sum_dict = {'businessinsder': businessinsder_result, 'graintrade': graintrade_result}
    # return namedtuple('update_all', **sum_dict)
    return sum_dict

