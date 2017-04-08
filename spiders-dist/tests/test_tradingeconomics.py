import unittest
from unittest.mock import patch
import requests
import pickle
import datetime
from datetime import date
import pytz
from pymongo import MongoClient

from common import DATA_PATH, mock_requests

from spiders.commodities.tradingeconomics import available_commodities


class Parser(unittest.TestCase):


    @patch('spiders.commodities.tradingeconomics.requests.get', side_effect=mock_requests)
    def test1_available_commodities(self, requests_fun):
        data = {'Crude Oil': '/commodity/crude-oil', 'Natural gas': '/commodity/natural-gas',
                'Heating oil': '/commodity/heating-oil', 'Naphtha': '/commodity/naphtha',
                'Gold': '/commodity/gold', 'Platinum': '/commodity/platinum',
                'Corn': '/commodity/corn', 'Wheat': '/commodity/wheat', 'Rice': '/commodity/rice',
                'Palm Oil': '/commodity/palm-oil', 'Rubber': '/commodity/rubber',
                'Coffee': '/commodity/coffee', 'Oat': '/commodity/oat', 'Cocoa': '/commodity/cocoa',
                'Sugar': '/commodity/sugar', 'Live Cattle': '/commodity/live-cattle',
                'Beef': '/commodity/beef', 'Copper': '/commodity/copper', 'Lead': '/commodity/lead',
                'Tin': '/commodity/tin', 'Nickel': '/commodity/nickel', 'Steel': '/commodity/steel',
                'Coal': '/commodity/coal', 'Baltic Dry': '/commodity/baltic',
                'LME Index': '/commodity/lme'}
        self.assertEqual(len(available_commodities()), len(data), 'lenght is not same')
        self.assertEqual(available_commodities(), data)

