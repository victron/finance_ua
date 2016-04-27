from datetime import datetime
from spiders.common_spider import local_tz


external_loans_USD = [
{'incomelevel': 7.75 , 'repaydate': datetime.strptime('01.09.2019', '%d.%m.%Y').replace(hour=17, tzinfo=local_tz), 'coupon_date': ['1.03', '1.09'],  '_id':	'XS1303918269',	'CUSIP': '903724AV4', 'amount':	1330472000,},
{'incomelevel': 7.75 , 'repaydate': datetime.strptime('01.09.2020', '%d.%m.%Y').replace(hour=17, tzinfo=local_tz), 'coupon_date': ['1.03', '1.09'],  '_id':	'XS1303918939',	'CUSIP': '903724AM4', 'amount':	1706530000,},
{'incomelevel': 7.75 , 'repaydate': datetime.strptime('01.09.2021', '%d.%m.%Y').replace(hour=17, tzinfo=local_tz), 'coupon_date': ['1.03', '1.09'],  '_id':	'XS1303920083',	'CUSIP': '903724AN2', 'amount':	1377761000,},
{'incomelevel': 7.75 , 'repaydate': datetime.strptime('01.09.2022', '%d.%m.%Y').replace(hour=17, tzinfo=local_tz), 'coupon_date': ['1.03', '1.09'],  '_id':	'XS1303921214',	'CUSIP': '903724AP7', 'amount':	1354820000,},
{'incomelevel': 7.75 , 'repaydate': datetime.strptime('01.09.2023', '%d.%m.%Y').replace(hour=17, tzinfo=local_tz), 'coupon_date': ['1.03', '1.09'],  '_id':	'XS1303921487',	'CUSIP': '903724AQ5', 'amount':	1330114000,},
{'incomelevel': 7.75 , 'repaydate': datetime.strptime('01.09.2024', '%d.%m.%Y').replace(hour=17, tzinfo=local_tz), 'coupon_date': ['1.03', '1.09'],  '_id':	'XS1303925041',	'CUSIP': '903724AR3', 'amount':	1315072000,},
{'incomelevel': 7.75 , 'repaydate': datetime.strptime('01.09.2025', '%d.%m.%Y').replace(hour=17, tzinfo=local_tz), 'coupon_date': ['1.03', '1.09'],  '_id':	'XS1303925470',	'CUSIP': '903724AS1', 'amount':	1306032000,},
{'incomelevel': 7.75 , 'repaydate': datetime.strptime('01.09.2026', '%d.%m.%Y').replace(hour=17, tzinfo=local_tz), 'coupon_date': ['1.03', '1.09'],  '_id':	'XS1303926528',	'CUSIP': '903724AT9', 'amount':	1295404000,},
{'incomelevel': 7.75 , 'repaydate': datetime.strptime('01.09.2027', '%d.%m.%Y').replace(hour=17, tzinfo=local_tz), 'coupon_date': ['1.03', '1.09'],  '_id':	'XS1303927179',	'CUSIP': '903724AU6', 'amount':	1286228000,},
{'incomelevel': 3.4,   'repaydate': datetime.strptime('01.09.2020', '%d.%m.%Y').replace(hour=17, tzinfo=local_tz), 'coupon_date': ['31.05'],         '_id': 'XS1303929894', 'comments': 'flexi incomelevel, not cleare repadate', 	'CUSIP': '903724AW2',	  'amount':   3027815000, },
{'incomelevel': 1.847 ,'repaydate': datetime.strptime('29.05.2020', '%d.%m.%Y').replace(hour=17, tzinfo=local_tz), 'coupon_date': ['29.11', '29.05'],'_id':	'US903724АL62',	 'amount':	1000000000,},
{'incomelevel': 1.844 ,'repaydate': datetime.strptime('16.05.2019', '%d.%m.%Y').replace(hour=17, tzinfo=local_tz), 'coupon_date': ['16.11', '16.05'],'_id':	'US903724АК89',	 'amount':	1000000000,},
]