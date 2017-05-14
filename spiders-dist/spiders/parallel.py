import logging
import multiprocessing
from functools import reduce
from multiprocessing.connection import wait
from datetime import datetime

from spiders import berlox
from spiders import finance_ua
from spiders import minfin
from spiders import news_minfin
from spiders.parameters import DB_NAME

from spiders.mongo_update import mongo_insert_history
from spiders import parse_minfin
from spiders.common_spider import current_datetime_tz

logger = logging.getLogger(__name__)

class writer_news():
    def __init__(self, db_name, *funs):
        # TODO: put import outside
        # from pymongo import MongoClient
        # client = MongoClient(connect=False)
        # self.DATABASE = client[db_name]
        from spiders.parameters import DATABASE
        self.DATABASE = DATABASE
        self.docs = []
        self.funs = funs

    def fetch(self):
        if len(self.funs) < 2:
            self.docs = self.funs[0]()
        else:
            # convert tuple into list and put in order from low level to high level functions
            fun_list = list(self.funs)
            fun_list.reverse()
            # docs = fun_list[1](fun_list[0]) #test string
            self.docs = reduce(lambda x, y: y(x), fun_list)
            logger.debug('functions= {} gave docs num= {}'.format(fun_list, len(self.docs)))
        return self.docs

    def update(self, collection, update_time):
        """
        :self.update_result: tuple: inserted_count, duplicate_count
        :param collection:
        :return:
        """
        collection = self.DATABASE[collection]
        named_tuple = mongo_insert_history(self.fetch(), collection)
        logger.debug('inserted into= {} result= {}'.format(collection, named_tuple))
        self.update_result = (named_tuple.inserted_count, named_tuple.duplicate_count)

    def send(self, connector):
        connector.send(self.update_result)
        connector.close()


class writer_lists(writer_news):
    def __init__(self, db_name, *funs):
        super().__init__(db_name, *funs)
        from bson.codec_options import CodecOptions
        from spiders.common_spider import local_tz
        # aware_times = lambda collection: db_name[collection].with_options(codec_options=CodecOptions(tz_aware=True,
        #
        # TODO: replace hardcoded   'data_active'                                                                                           tzinfo=local_tz))
        self.data_active = self.DATABASE['data_active'].with_options(codec_options=CodecOptions(tz_aware=True,
                                                                                          tzinfo=local_tz))

    def update(self, collection, update_time):
        """

        :param collection:
        :param update_time:
        :return: tuple inserted_count, deleted_count.
        """
        super().update(collection, update_time)
        for document in self.docs:
            document['time_update'] = update_time
            # TODO: replace somehow
            # 'source' need in self.result_delete, in another case process could delete data
            # witch anothe process will add later
            source = document['source']

            if document.get('session', False) is False:
                key = {'bid': document['bid'], 'source': document['source']}
                try:
                    original_doc = self.data_active.find_one_and_update(key, {'$set': {'time_update': update_time}})
                    if original_doc is None:
                        self.data_active.insert_one(document)
                        logger.debug('inserted doc ={}'.format(document))
                    elif original_doc['time'] != document['time']:
                        result_active = self.data_active.update_one(key, {'$set': {'time': document['time'],
                                                                                   'hidden': False},
                                                                          '$inc': {'time_up_count': 1}})
                        logger.debug('updated doc and time_up_count with key = {}'.format(key))
                    else:
                        logger.debug('updated doc with key= {}'.format(key))
                except:
                    logger.error('error in inserting doc= {}'.format(document))
                    logger.error('original doc= {}'.format(self.docs))
                    raise
            else:
                # insert document with cookies, (new cookies need to insert any way)
                key = {'currency': document['currency'], 'operation': document['operation'], 'session': True}
                self.data_active.replace_one(key, document, upsert=True)
                logger.debug('REPLACE doc {}'.format(document))

        # delete old bids
        self.result_delete = self.data_active.delete_many({'$or': [{'time_update': {'$lt': update_time}},
                                                                   {'time_update': None}],
                                                           # 'source': source
                                                           })
        self.result_delete = self.result_delete.deleted_count
        self.update_result = (self.update_result[0], self.result_delete)
        return self.update_result


def workerANDconnector(funs, **kargs):
    # from mongo_collector import DB_NAME
    logger.debug('worker called = {}'.format(funs))
    if kargs['collection'] == 'records':
        writer = writer_lists(DB_NAME, *funs)
    elif kargs['collection'] == 'news':
        writer = writer_news(DB_NAME, *funs)
    else:
        raise ValueError('wrong collection {}'.format(kargs['collection']))
    logger.debug('start calling writer with args= {}, {}'.format(kargs['collection'], kargs['update_time']))
    writer.update(kargs['collection'], kargs['update_time'])
    logger.debug('called writer with args= {}, {}'.format(kargs['collection'], kargs['update_time']))
    writer.send(kargs['connector'])



# @timer(logging=logger)
def parent(funcs: list, collection) -> tuple:
    """create workers and colect result via pipes
    :return list of results from chields
    """

    # pipe is a tuple (parent , chield)
    update_time = datetime.utcnow()
    pipes = [multiprocessing.Pipe(duplex=False) for _ in funcs]
    processes_news = [multiprocessing.Process(target=workerANDconnector, args=(params[0],),
                                              kwargs={'connector': params[1][1], 'collection': collection,
                                                      'update_time': update_time})
                      for params in zip(funcs, pipes)]
    logger.debug('created process num= {}'.format(len(processes_news)))
    for process, pipe in zip(processes_news, pipes):
        process.start()
        pipe[1].close()

    readers = [r for r, w in pipes]
    result = []
    while readers:
        for r in wait(readers):
            try:
                result_r = r.recv()
            except EOFError:
                readers.remove(r)
            else:
                result.append(result_r)

    for process in processes_news:
        process.join()
    return reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]), result)


def update_news():
    """

    :return: tuple (inserted_count, duplicate_count)
    """
    spiders_news = [(news_minfin.parse_minfin_headlines,),
                    (minfin.minfin_headlines,),
                    (minfin.announcement_ovdp,)]
    result = parent(spiders_news, 'news')
    # return reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]), result)
    return result

# TODO: migrate from mongo_update on func below
def update_lists():
    """

    :return: tuple inserted_count, ddeleted_count
    """
    spiders_lists = [
                    (parse_minfin.data_api_minfin, parse_minfin.get_triple_data),
                     (finance_ua.data_api_finance_ua, finance_ua.fetch_data),
                     (berlox.data_api_berlox, berlox.fetch_data), ]
    logger.debug('spiders_lists len= {}'.format(len(spiders_lists)))
    result = parent(spiders_lists, 'records')
    return result


if __name__ == '__main__':
    update_news()
