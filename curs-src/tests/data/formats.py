# test formats for
# USD collection
from datetime import datetime
from spiders.common_spider import local_tz

stat_format = [

    {"time": "2014-11-10T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 15.5, "rate_acc_min": 15.15, "rate_r_max": 15.73, "rate_r_min": 14.0,
                     "amount_accepted_all": 5.0, "operation": "sell", "amount_accepted_p_min_max": 15.9,
                     "amount_requested": 25.3, "rate_acc_med": 15.2242}, "buy": 15.4, "sell": 15.65,
     "nbu_rate": 14.804225, "source": "d_ext_stat"},
    {"time": "2014-11-24T14:00:00.000Z", "buy": 16.0, "sell": 16.1, "nbu_rate": 15.060794, "source": "d_ext_stat"},
    {"time": "2014-12-05T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 15.409, "rate_acc_min": 15.4, "rate_r_max": 16.62, "rate_r_min": 15.3,
                     "amount_accepted_all": 3.0, "operation": "sell", "amount_accepted_p_min_max": 36.5,
                     "amount_requested": 13.2, "rate_acc_med": 15.4021}, "buy": 16.82, "sell": 17.0,
     "nbu_rate": 15.415499, "source": "d_ext_stat"},
    {"time": "2014-12-15T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 15.7549, "rate_acc_min": 15.75, "rate_r_max": 15.992, "rate_r_min": 15.3,
                     "amount_accepted_all": 3.0, "operation": "sell", "amount_accepted_p_min_max": 3.3,
                     "amount_requested": 13.2, "rate_acc_med": 15.7521}, "buy": 18.5, "sell": 18.79,
     "nbu_rate": 15.760382, "source": "d_ext_stat"},
    {"time": "2015-10-06T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 21.3525, "rate_acc_min": 21.259, "rate_r_max": 21.45, "rate_r_min": 21.259,
                     "amount_accepted_all": 19.3, "operation": "buy", "amount_accepted_p_min_max": 0.5,
                     "amount_requested": 20.6, "rate_acc_med": 21.2778}, "buy": 22.41, "sell": 22.5,
     "nbu_rate": 21.21564, "source": "d_ext_stat"},

    {"time": "2015-10-09T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 21.69, "rate_acc_min": 21.69, "rate_r_max": 22.0, "rate_r_min": 21.69,
                     "amount_accepted_all": 3.3, "operation": "buy", "amount_accepted_p_min_max": 100.0,
                     "amount_requested": 7.3, "rate_acc_med": 21.69}, "buy": 22.67, "sell": 22.75,
     "nbu_rate": 21.299291, "source": "d_ext_stat"},
    {"time": "2015-10-23T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 22.61, "rate_acc_min": 22.5999, "rate_r_max": 22.7, "rate_r_min": 22.5999,
                     "amount_accepted_all": 2.2, "operation": "buy", "amount_accepted_p_min_max": 31.8,
                     "amount_requested": 7.2, "rate_acc_med": 22.6031}, "buy": 24.0, "sell": 24.11,
     "nbu_rate": 22.280585, "source": "d_ext_stat"},
    {"time": "2015-12-23T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 23.0, "rate_acc_min": 22.85, "rate_r_max": 23.5, "rate_r_min": 22.85,
                     "amount_accepted_all": 5.4, "operation": "buy", "amount_accepted_p_min_max": 35.2,
                     "amount_requested": 8.2, "rate_acc_med": 22.9847}, "buy": 25.0, "sell": 25.05,
     "nbu_rate": 23.146841, "source": "d_ext_stat"},

    {"time": "2016-01-06T14:00:00.000Z", "buy": 25.7, "sell": 25.85, "source": "d_ext_stat"},


    {"time": "2016-02-12T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 26.16, "rate_acc_min": 26.13, "rate_r_max": 26.16, "rate_r_min": 25.8,
                     "amount_accepted_all": 14.3, "operation": "sell", "amount_accepted_p_min_max": 12.0,
                     "amount_requested": 47.3, "rate_acc_med": 26.1491}, "buy": 27.0, "sell": 27.1,
     "nbu_rate": 26.083668, "source": "d_ext_stat"},
    {"time": "2016-03-10T14:00:00.000Z",
     "nbu_auction": {"rate_acc_max": 25.6, "rate_acc_min": 25.48, "rate_r_max": 26.2, "rate_r_min": 25.48,
                     "amount_accepted_all": 55.1, "operation": "buy", "amount_accepted_p_min_max": 0.9,
                     "amount_requested": 59.0, "rate_acc_med": 25.5315}, "buy": 26.35, "sell": 26.45,
     "nbu_rate": 26.182756, "source": "d_ext_stat"}

]

active_format = [
{"source" : "f" , "phone" : "380688731157" , "comment" : "Левый берег, Бровары" , "bid" : 436283 , "rate" : 26.0 , "time_update" : "2016-04-13T15:07:34.405Z", "operation" : "sell" , "currency" : "USD" , "amount" : "1 000" , "priority" : 0 , "location" : "Киев" , "time" : "2016-04-13T03:33:00.000Z"},
{"source" : "f" , "phone" : "380979650955" , "comment" : "Приеду частями" , "bid" : 436284 , "rate" : 25.5 , "time_update" : "2016-04-13T15:07:34.405Z", "operation" : "buy" , "currency" : "USD" , "amount" : "10 000" , "priority" : 2 , "location" : "Киев" , "time" : "2016-04-13T03:36:00.000Z"},
{"source" : "f" , "phone" : "380734162002" , "comment" : "Igor" , "bid" : 436319 , "rate" : 25.56 , "time_update" : "2016-04-13T15:07:34.405Z", "operation" : "buy" , "currency" : "USD" , "amount" : "13 750" , "priority" : 0 , "location" : "Киев" , "time" : "2016-04-13T04:50:00.000Z"},
{"source" : "m" , "operation" : "buy" , "phone" : "067xxx-x9-88" , "currency" : "EUR" , "location" : "Киев" , "time" : "2016-04-13T13:41:00.000Z", "bid" : "16107758" , "rate" : 29.1 , "comment" : "Оболонь, можно частями, могу подъехать" , "time_update" : "2016-04-13T15:07:34.405Z" , "amount" : "3600"},
{"source" : "m" , "operation" : "sell" , "phone" : "068xxx-x9-27" , "currency" : "EUR" , "location" : "Киев" , "time" : "2016-04-13T15:05:00.000Z" , "bid" : "16115207" , "rate" : 29.25 , "comment" : "Контрактовая площадь, можно частями, обменный пункт, проверка денег." , "time_update" : "2016-04-13T15:07:34.405Z" , "amount" : "7000"},
{"source" : "m" , "operation" : "sell" , "phone" : "063xxx-x7-58" , "currency" : "USD" , "location" : "Киев" , "time" : "2016-04-13T14:22:00.000Z" , "bid" : "16111529" , "rate" : 25.7 , "comment" : "Оболонь, целиком, могу подъехать" , "time_update" : "2016-04-13T15:07:34.405Z" , "amount" : "1100"},
{"source" : "b" , "phone" : "+380635673288" , "amount" : 1000 , "bid" : "b7bbb1e37da24373a9a1fdde0e2abe6e" , "rate" : 29.4 , "pr" :  None  , "sid" : 1 , "time_update" : "2016-04-13T15:07:34.405Z", "operation" : "sell" , "currency" : "EUR" , "d" : False , "location" : "Киев" , "comment" : "Любой подъеду" , "uid" : "734-461-184" , "time" : "2016-04-13T10:33:00.000Z"},
{"source" : "b" , "phone" : "+380958643413" , "amount" : 5000 , "bid" : "43483e9a353b46fd84ecbdcd018d2ddc" , "rate" : 25.7 , "pr" :  None  , "sid" : 1 , "time_update" : "2016-04-13T15:07:34.405Z" , "operation" : "sell" , "currency" : "USD" , "d" : False , "location" : "Днепропетровск" , "comment" : "Правда-Калиновая, безопасность, Угол Калиновой и пр. Правда, обмен валют, круглосуточно" , "uid" : "819-435-602" , "time" : "2016-04-13T10:33:00.000Z"},
{"source" : "b" , "phone" : "+380936253114" , "amount" : 500000 , "bid" : "23e259ef91a2461f954889d4e638e1d0" , "rate" : 0.389 , "pr" : True , "sid" : 1 , "time_update" : "2016-04-13T15:07:34.405Z" , "operation" : "buy" , "currency" : "RUB" , "d" : False , "location" : "Донецк" , "comment" : "северный, Р-он салона\"Донна\"по Артема, можно частями. за доллары-66, обменка" , "uid" : "830-465-519" , "time" : "2016-04-13T10:33:00.000Z"}
]

time_keys = lambda field: field in ('time', 'time_update')

def reformat_date(doc):
    for key in filter(time_keys, doc):
        doc[key] = datetime.strptime(doc[key], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=local_tz)
    return doc

stat_format = [reformat_date(doc) for doc in stat_format]
active_format = [reformat_date(doc) for doc in active_format]
