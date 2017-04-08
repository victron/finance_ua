from datetime import datetime

h_int_stat_lite = [
    {"time" : datetime.strptime("2016-11-27T20:59", "%Y-%m-%dT%H:%M"), "sell" : 27.1, "buy" : 27.05 , 'source': 'h_int_stat'},
    {"time" : datetime.strptime("2016-11-27T19:59", '%Y-%m-%dT%H:%M'), "sell" : 27.1, "buy" : 27.05 , 'source': 'h_int_stat'},
    {"time" : datetime.strptime("2016-11-27T18:59", '%Y-%m-%dT%H:%M'), "sell" : 27.1, "buy" : 27.05 , 'source': 'h_int_stat'},
    {"time" : datetime.strptime("2016-11-27T16:59", '%Y-%m-%dT%H:%M'), "sell" : 27.1, "buy" : 27.03 , 'source': 'h_int_stat'},
    {"time" : datetime.strptime("2016-11-27T15:59", '%Y-%m-%dT%H:%M'), "sell" : 27.1, "buy" : 27.05 , 'source': 'h_int_stat'},
    {"time" : datetime.strptime("2016-11-27T14:59", '%Y-%m-%dT%H:%M'), "sell" : 27.1, "buy" : 27.04 , 'source': 'h_int_stat'},
    {"time" : datetime.strptime("2016-11-27T13:59", '%Y-%m-%dT%H:%M'), "sell" : 27.1, "buy" : 27.03 , 'source': 'h_int_stat'},
    {"time" : datetime.strptime("2016-11-27T12:59", '%Y-%m-%dT%H:%M'), "sell" : 27.09, "buy" : 27.04, 'source': 'h_int_stat'},
    {"time" : datetime.strptime("2016-11-27T11:59", '%Y-%m-%dT%H:%M'), "sell" : 27.1, "buy" : 27.03 , 'source': 'h_int_stat'},
    {"time" : datetime.strptime("2016-11-27T10:59", '%Y-%m-%dT%H:%M'), "sell" : 27.1, "buy" : 27.03 , 'source': 'h_int_stat'},
    {"time" : datetime.strptime("2016-11-27T09:59", '%Y-%m-%dT%H:%M'), "buy" : 27.03, "sell" : 27.1 , 'source': 'h_int_stat'},
    {"time" : datetime.strptime("2016-11-27T08:59", '%Y-%m-%dT%H:%M'), "buy" : 27.03, "sell" : 27.1 , 'source': 'h_int_stat'},
                    ]

d_int_stat_result = {"time" : datetime.strptime("2016-11-27T00:00", '%Y-%m-%dT%H:%M'),
                     "source" : "d_int_stat", "buy" : 27.04, "sell" : 27.1,
                     "sell_rates" : [ 27.1, 27.1, 27.1, 27.1, 27.09, 27.1, 27.1, 27.1 ],
                     "buy_rates" : [ 27.03, 27.05, 27.04, 27.03, 27.04, 27.03, 27.03, 27.03 ] }