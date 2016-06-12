from spiders import news_minfin, minfin, parse_minfin, finance_ua, berlox
import multiprocessing
from multiprocessing.connection import wait
from functools import reduce
from tools.mytools import timer

def worker(news_fun: tuple, **kargs):
    if len(news_fun) == 1:
        docs = news_fun[0]()
    else:
        # convert tuple into list and put in order from low level to high level functions
        fun_list = list(news_fun)
        fun_list.reverse()
        # docs = fun_list[1](fun_list[0]) #test string
        docs = reduce(lambda x, y: y(x), fun_list)
    from mongo_collector.mongo_update import mongo_insert_history
    from pymongo import MongoClient
    from mongo_collector import DB_NAME
    client = MongoClient()
    DATABASE = client[DB_NAME]
    news = DATABASE[kargs['collection']]
    kargs['connection'].send(mongo_insert_history(docs, news))
    kargs['connection'].close()


@timer()
def update(funcs: list, collection) -> tuple:
    """create workers and colect result via pipes"""

    # pipe is a tuple (parent , chield)
    pipes = [ multiprocessing.Pipe(duplex=False) for _ in funcs]
    processes_news = [multiprocessing.Process(target=worker, args=(process[0],),
                                              kwargs={'connection': process[1][1], 'collection': collection})
                      for process in zip(funcs, pipes)]
    for process, pipe in zip(processes_news, pipes):
        process.start()
        pipe[1].close()

    readers = [r for r, w in pipes]
    result = []
    while readers:
        for r in wait(readers):
            try:
                result_r  = r.recv()
            except EOFError:
                readers.remove(r)
            else:
                result.append(result_r)

    for process in processes_news:
        process.join()
    # in return inserted_count, duplicate_count
    return reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]), result)

def update_news():
    spiders_news = [(news_minfin.parse_minfin_headlines,),
                    (minfin.minfin_headlines,)]
    return update(spiders_news, 'news')

# TODO: migrate from mongo_update on func below
def update_lists():
    spiders_lists = [(parse_minfin.data_api_minfin, parse_minfin.get_triple_data),
                     (finance_ua.data_api_finance_ua, finance_ua.fetch_data),
                     (berlox.data_api_berlox, berlox.fetch_data),]
    return update(spiders_lists, 'records')
