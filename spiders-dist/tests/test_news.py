import unittest
import requests
import pickle
from datetime import datetime, timedelta
from time import sleep
from unittest.mock import patch
import importlib
import logging
# http://fgimian.github.io/blog/2014/04/10/using-the-python-mock-library-to-fake-regular-functions-during-tests/

from pymongo import MongoClient

from common import DATA_PATH, mock_requests
from spiders.news_minfin import parse_minfin_headlines
from spiders.minfin import minfin_headlines, minfin_headlines_url, announcement_ovdp
from spiders.common_spider import local_tz, kyiv_tz

from spiders.parallel import parent, update_news
import spiders.news_minfin as news_minfin
import spiders.minfin as minfin

from spiders.mongo_start import news
import spiders.mongo_start as mongo_start

DB_NAME = 'TEST'
client = MongoClient()
DATABASE = client[DB_NAME]

logger = logging.getLogger('test_news')
# logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)

class ParseNews(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        # http://stackoverflow.com/questions/19102203/overloading-unittest-testcase-in-python
        super(ParseNews, self).__init__(*args, **kwargs)
        # unittest.TestCase.__init__(self, *args, **kwargs)
        self.readFiles()

    def readFiles(self):
        with open(DATA_PATH + 'news_minfin.data', 'rb') as f:
            self.news_minfin_data = pickle.load(f)

        with open(DATA_PATH + 'minfin_headlines_ZSZ.data', 'rb') as f:
            self.minfin_headlines_ZSZ_data = pickle.load(f)
        with open(DATA_PATH + 'minfin_headlines_novini-ta-media.data', 'rb') as f:
            self.minfin_headlines_novini_ta_media_data = pickle.load(f)
        with open(DATA_PATH + 'minfin_headlines_all.data', 'rb') as f:
            self.minfin_headlines_all = pickle.load(f)

        with open(DATA_PATH + 'parse_announcement_ovdp.data', 'rb') as f:
            self.announcement_ovdp_data = pickle.load(f)


    def setUp(self):
        importlib.reload(mongo_start)   # reason to relad module, id to create idexes in collection
                                        # witch was deleted by tearDown

    def tearDown(self):
        client.drop_database(DB_NAME)

    # def test_news_minfin(self):
    #     self.assertEqual(parse_page(self.news_minfin_bin), self.news_minfin_data, 'wrong data after parser')
    @patch('spiders.news_minfin.requests.get', side_effect=mock_requests)
    def test_1news_minfinUA(self, requests_fun):
        self.assertEqual(parse_minfin_headlines(), self.news_minfin_data, 'wrong data after parser')

        result = parent([(news_minfin.parse_minfin_headlines, ), ], 'news')
        self.assertEqual(result, (len(self.news_minfin_data), 0), 'parse_minfin_headlines wrong return')
        self.assertEqual(news.find({}).count(), len(self.news_minfin_data), 'wrong news number in DB')
        test_doc = news.find_one({'href': 'http://minfin.com.ua/2017/03/17/26771826/'})
        self.assertEqual(test_doc['time'], datetime(2017, 3, 17, 17, 53), 'UTC time for doc error')

        # duplicate insert
        result = parent([(news_minfin.parse_minfin_headlines,), ], 'news')
        self.assertEqual(result, (0, len(self.news_minfin_data)), 'parse_minfin_headlines wrong return; '
                                                                  'error in duplicate insert')
        self.assertEqual(news.find({}).count(), len(self.news_minfin_data), 'wrong news number in DB')
        test_doc = news.find_one({'href': 'http://minfin.com.ua/2017/03/17/26771826/'})
        self.assertEqual(test_doc['time'], datetime(2017, 3, 17, 17, 53), 'UTC time for doc error')

    @patch('spiders.minfin.requests.get', side_effect=mock_requests)
    def test_2minfin_headlines(self, requests_fun):

        url = 'http://www.minfin.gov.ua/news/novini-ta-media'
        self.assertEqual(self.minfin_headlines_novini_ta_media_data,
                         minfin_headlines_url(url),
                         'error in parse_minfin_headlines')
        url = 'http://www.minfin.gov.ua/news/borg/zovnishni-suverenni-zobovjazannja'
        self.assertEqual(self.minfin_headlines_ZSZ_data,
                         minfin_headlines_url(url),
                         'error in parse_minfin_headlines')
        self.assertEqual(self.minfin_headlines_all, minfin_headlines(),
                         'error in parse_minfin_headlines')

        # mongo tests
        result = parent([(minfin.minfin_headlines, ), ], 'news')
        self.assertEqual(len(self.minfin_headlines_all),
                         len(self.minfin_headlines_novini_ta_media_data) + len(self.minfin_headlines_ZSZ_data),
                         'simple check; sum of first two list should be eq. to third')
        self.assertEqual(result, (len(self.minfin_headlines_all), 0), 'minfin_headlines_all return')
        self.assertEqual(news.find({}).count(), len(self.minfin_headlines_all), 'wrong news number in DB')
        test_doc = news.find_one({'href': 'http://www.minfin.gov.ua/news/view/ministerstvo-finansiv-ukrainy-zdiisnylo-vyplatu-kuponnoho-dokhodu-za-oblihatsiiamy-zovnishnoi-derzhavnoi-pozyky?category=borg&subcategory=zovnishni-suverenni-zobovjazannja'})
        self.assertEqual(test_doc['time'], datetime(2017, 2, 28, 22, 0), 'UTC time for doc error')

        # mongo duplicate test
        result = parent([(minfin.minfin_headlines,), ], 'news')
        self.assertEqual(result, (0, len(self.minfin_headlines_all)), 'minfin_headlines_all wrong return')
        self.assertEqual(news.find({}).count(), len(self.minfin_headlines_all), 'wrong news number in DB')
        test_doc = news.find_one({'href': 'http://www.minfin.gov.ua/news/view/ministerstvo-finansiv-ukrainy-zdiisnylo-vyplatu-kuponnoho-dokhodu-za-oblihatsiiamy-zovnishnoi-derzhavnoi-pozyky?category=borg&subcategory=zovnishni-suverenni-zobovjazannja'})
        self.assertEqual(test_doc['time'], datetime(2017, 2, 28, 22, 0), 'UTC time for doc error')

    @patch('spiders.minfin.requests.get', side_effect=mock_requests)
    def test_3parse_announcement_ovdp(self, requests_fun):
        result = announcement_ovdp()
        result = [{**doc, **{'time': kyiv_tz.localize(datetime(2017, 3, 19, 19, 32, 34, 319882))}}
                  for doc in result]                    # replace today date on date from etalon
        announcement_ovdp_data = [{**doc, **{'headline': doc['headline'] + ' in a same_date', 'flag': 'same_date'}}
                                  if doc['time_auction'].date() == datetime.today().date() else doc
                                  for doc in self.announcement_ovdp_data]
        # print(announcement_ovdp_data, result)
        self.assertEqual(announcement_ovdp_data, result,
                         'error in parse_announcement_ovdp')


        # mongo tests
        current_time = datetime.utcnow()
        mongo_result = parent([(minfin.announcement_ovdp, ), ], 'news')
        self.assertEqual(mongo_result, (len(self.announcement_ovdp_data), 0), 'announcement_ovdp wrong return')
        self.assertEqual(news.find({}).count(), len(self.announcement_ovdp_data), 'wrong news number in DB')
        test_doc = news.find_one({'href_announce': 'http://www.minfin.gov.ua/uploads/redactor/files/48-52%20оголошення-сайт.doc'})
        if datetime.today().date() != datetime(2017, 3, 21).date():
            self.assertEqual(test_doc['headline'], 'OVDP 21.03.2017', 'quick check NAME of doc')
        else:
            self.assertEqual(test_doc['headline'], 'OVDP 21.03.2017 in a same_date', 'quick check NAME of doc')
        self.assertEqual(test_doc['time_auction'], datetime(2017, 3, 21, 0, 0), 'time_auction should be same')
        self.assertAlmostEqual(test_doc['time'], current_time, delta=timedelta(seconds=1),
                               msg='time should be same as insert data')


        # mongo check duplicate
        mongo_result = parent([(minfin.announcement_ovdp, ), ], 'news')
        self.assertEqual(mongo_result, (0, len(self.announcement_ovdp_data)), 'announcement_ovdp wrong return')
        self.assertEqual(news.find({}).count(), len(self.announcement_ovdp_data), 'wrong news number in DB')
        test_doc = news.find_one({'href_announce': 'http://www.minfin.gov.ua/uploads/redactor/files/48-52%20оголошення-сайт.doc'})
        if datetime.today().date() != datetime(2017, 3, 21).date():
            self.assertEqual(test_doc['headline'], 'OVDP 21.03.2017', 'quick check NAME of doc')
        else:
            self.assertEqual(test_doc['headline'], 'OVDP 21.03.2017 in a same_date', 'quick check NAME of doc')
        self.assertEqual(test_doc['time_auction'], datetime(2017, 3, 21, 0, 0), 'time_auction should be same')
        self.assertAlmostEqual(test_doc['time'], current_time, delta=timedelta(seconds=1),
                               msg='time should be same as INSERT data')

    @patch('spiders.minfin.requests.get', side_effect=mock_requests)
    def test_4_news_all(self, requests_fun):
        result = update_news()
        logger.info('result= {}'.format(result))
        all_news_count = len(self.news_minfin_data) + len(self.minfin_headlines_all) + len(self.announcement_ovdp_data)
        self.assertEqual(result, (all_news_count, 0), 'update_news() return wrong data')
        self.assertEqual(news.find({}).count(), all_news_count, 'wrong news number in DB')

        # duplicate insert
        result = update_news()
        self.assertEqual(result, (0, all_news_count), 'update_news() - check duplicates')
        self.assertEqual(news.find({}).count(), all_news_count, 'wrong news number in DB')

if __name__ == '__main__':
    unittest.main()