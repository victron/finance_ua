# test formats for
# USD collection
from datetime import datetime
from spiders.common_spider import local_tz

stat_format = [

    {"time": "2014-11-10T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 15.5, "rate_acc_min": 15.15, "rate_r_max": 15.73, "rate_r_min": 14.0,
                     "amount_accepted_all": 5.0, "operation": "sell", "amount_accepted_p_min_max": 15.9,
                     "amount_requested": 25.3, "rate_acc_med": 15.2242}, "buy": 15.4, "sell": 15.65,
     "nbu_rate": 14.804225},
    {"time": "2014-11-24T14:00:00.000Z", "buy": 16.0, "sell": 16.1, "nbu_rate": 15.060794},
    {"time": "2014-12-05T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 15.409, "rate_acc_min": 15.4, "rate_r_max": 16.62, "rate_r_min": 15.3,
                     "amount_accepted_all": 3.0, "operation": "sell", "amount_accepted_p_min_max": 36.5,
                     "amount_requested": 13.2, "rate_acc_med": 15.4021}, "buy": 16.82, "sell": 17.0,
     "nbu_rate": 15.415499},
    {"time": "2014-12-15T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 15.7549, "rate_acc_min": 15.75, "rate_r_max": 15.992, "rate_r_min": 15.3,
                     "amount_accepted_all": 3.0, "operation": "sell", "amount_accepted_p_min_max": 3.3,
                     "amount_requested": 13.2, "rate_acc_med": 15.7521}, "buy": 18.5, "sell": 18.79,
     "nbu_rate": 15.760382},
    {"time": "2015-10-06T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 21.3525, "rate_acc_min": 21.259, "rate_r_max": 21.45, "rate_r_min": 21.259,
                     "amount_accepted_all": 19.3, "operation": "buy", "amount_accepted_p_min_max": 0.5,
                     "amount_requested": 20.6, "rate_acc_med": 21.2778}, "buy": 22.41, "sell": 22.5,
     "nbu_rate": 21.21564},

    {"time": "2015-10-09T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 21.69, "rate_acc_min": 21.69, "rate_r_max": 22.0, "rate_r_min": 21.69,
                     "amount_accepted_all": 3.3, "operation": "buy", "amount_accepted_p_min_max": 100.0,
                     "amount_requested": 7.3, "rate_acc_med": 21.69}, "buy": 22.67, "sell": 22.75,
     "nbu_rate": 21.299291},
    {"time": "2015-10-23T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 22.61, "rate_acc_min": 22.5999, "rate_r_max": 22.7, "rate_r_min": 22.5999,
                     "amount_accepted_all": 2.2, "operation": "buy", "amount_accepted_p_min_max": 31.8,
                     "amount_requested": 7.2, "rate_acc_med": 22.6031}, "buy": 24.0, "sell": 24.11,
     "nbu_rate": 22.280585},
    {"time": "2015-12-23T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 23.0, "rate_acc_min": 22.85, "rate_r_max": 23.5, "rate_r_min": 22.85,
                     "amount_accepted_all": 5.4, "operation": "buy", "amount_accepted_p_min_max": 35.2,
                     "amount_requested": 8.2, "rate_acc_med": 22.9847}, "buy": 25.0, "sell": 25.05,
     "nbu_rate": 23.146841},

    {"time": "2016-01-06T14:00:00.000Z", "buy": 25.7, "sell": 25.85},


    {"time": "2016-02-12T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 26.16, "rate_acc_min": 26.13, "rate_r_max": 26.16, "rate_r_min": 25.8,
                     "amount_accepted_all": 14.3, "operation": "sell", "amount_accepted_p_min_max": 12.0,
                     "amount_requested": 47.3, "rate_acc_med": 26.1491}, "buy": 27.0, "sell": 27.1,
     "nbu_rate": 26.083668},
    {"time": "2016-03-10T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 25.6, "rate_acc_min": 25.48, "rate_r_max": 26.2, "rate_r_min": 25.48,
                     "amount_accepted_all": 55.1, "operation": "buy", "amount_accepted_p_min_max": 0.9,
                     "amount_requested": 59.0, "rate_acc_med": 25.5315}, "buy": 26.35, "sell": 26.45,
     "nbu_rate": 26.182756},

]
def reformat_date(doc):
    doc['time'] = datetime.strptime(doc['time'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=local_tz)
    return doc

stat_format = [reformat_date(doc) for doc in stat_format]
