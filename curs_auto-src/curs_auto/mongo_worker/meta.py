import logging
from datetime import datetime, timedelta

from curs_auto.mongo_worker.mongo_start import meta
from collections import namedtuple
import pymongo

logger = logging.getLogger('curs.mongo_collector.meta')


def collection_state(collection: pymongo.collection, time_triger: timedelta) -> namedtuple:
    """
    in case there are no info about collection, return
    result(False, None, None, current_time)
    :param collection:
    :param time_triger:
    :return: namedtuple('result', ['actual', 'update_time', 'create_time', 'current_time']
    """
    current_time = datetime.now()
    collection_info = meta.find_one({'_id': collection.name})
    result = namedtuple('result', ['actual', 'update_time', 'create_time', 'current_time'])
    if collection_info is not None:
        update_time = collection_info.get('update_time', current_time).replace(tzinfo=None)
        time_diff = current_time - update_time
        if time_diff >= time_triger:
            logger.info('collection: {} last update at = {} may updated'.format(collection.name, update_time))
            logger.debug('collection: {} last update {} ago, time_triger == {}'
                         .format(collection.name, time_diff.seconds, time_triger))
            return result(False, update_time, collection_info.get('create_time'), current_time)
        else:
            logger.info('collection: {} in actual state, last update at = {}'.format(collection.name, update_time))
            logger.debug('collection: {} last update {} ago, time_triger == {}'
                         .format(collection.name, time_diff.seconds, time_triger))
            return result(True, update_time, collection_info.get('create_time'), current_time)
    else:
        # in case there are no info about collection
        logger.info('collection: {} in UNKNOWN state'.format(collection.name))
        return result(False, None, None, current_time)


def update_meta(state: collection_state, collection: pymongo.collection):
    """
    update meta data about collection
    :param state: namedtuple, result of collection_state
    :param collection: collection name
    :param set_create_time: update  create_time or not
    :return:
    """
    current_time = datetime.now()
    if state.create_time is None:
        meta.update_one({'_id': collection.name}, {'$set': {'create_time': current_time}}, upsert=True)
    meta.update_one({'_id': collection.name}, {'$set': {'update_time': current_time}}, upsert=True)
