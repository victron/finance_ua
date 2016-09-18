from mongo_collector.mongo_start import aware_times
import pymongo
from flask import jsonify
import json
from datetime import datetime
from spiders.common_spider import local_tz

octothorpe = lambda x, dictionary: x * -1 if dictionary['nbu_auction']['operation'] == 'buy' else x
octothorpe2 = lambda doc: dict(doc, amount_accepted_all=doc['amount_accepted_all'] * -1,
                               amount_requested=doc['amount_requested'] * -1) \
                            if doc.get('nbu_auction_operation') == 'buy' else doc

def reformat_for_js_bonds(doc: dict) -> dict:
    # add in doc coupon pay
    # ----- could delete ----
    if 'bonds' in doc:
        sum_amount = 0
        for bond in doc.pop('bonds'):
            bond_doc = aware_times(bond.collection).find_one({'_id': bond.id})
            try:
                sum_amount += bond_doc['amount'] / 100 * bond_doc['incomelevel']
            except TypeError:
                print(bond_doc)
                print('!!! check if $ref inside \'bonds\' exists !!!')
        doc['sum_coupon'] = sum_amount
    # ==========================
    doc['time'] = doc['time'].strftime('%Y-%m-%d_%H')
    return octothorpe2(doc)


def reformat_for_js(doc):
    if 'nbu_auction' in doc:
        doc['amount_requested'] = octothorpe(doc['nbu_auction'].pop('amount_requested'), doc)
        doc['amount_accepted_all'] = octothorpe(doc['nbu_auction'].pop('amount_accepted_all'), doc)
        del doc['nbu_auction']
    doc['time'] = doc['time'].strftime('%Y-%m-%d_%H')
    return doc


def bonds_json_lite():
    bond_currencies = ['UAH', 'USD', 'EUR']
    # currency = 'USD'
    # bond_currency = 'UAH'
    def create_lookup(bond_currency: str) -> list:
        return [{'$lookup': {'from': 'bonds_' + bond_currency, 'localField': 'time', 'foreignField': 'repaydate',
                             'as': 'repay_' + bond_currency}},
                {'$lookup': {'from': 'bonds_' + bond_currency, 'localField': 'time', 'foreignField': 'paydate',
                             'as': 'pay_' + bond_currency}}]

    def create_project(currencies: list) -> dict:
        project = {}
        for currency in currencies:
            project.update({'repay_amount_' + currency: {'$sum': '$repay_' + currency + '.amount'},
                            'repay_amountn_' + currency: { '$sum': '$repay_' + currency + '.amountn'},
                            'pay_amount_' + currency: {'$sum': '$pay_' + currency + '.amount'},
                            'pay_amountn_' + currency: {'$sum': '$pay_' + currency + '.amountn'}})

        project.update({'_id': False, 'buy': True, 'sell': True, 'bonds': True,
                        'amount_accepted_all': '$nbu_auction.amount_accepted_all',
                        'amount_requested': '$nbu_auction.amount_requested',
                        'nbu_auction_operation': '$nbu_auction.operation', 'nbu_rate': True, 'time': True})
        return {'$project': project}

    # min_date = aware_times(currency).find_one(sort=[('time', pymongo.ASCENDING)])['time']
    min_date = datetime(year=2014, month=8, day=1, hour=17, minute=0, second=0, microsecond=0, tzinfo=local_tz)
    match = [{'$match': {'$or': [{'repaydate': {'$gte' : min_date}}, {'time': {'$gte' : min_date}}],
                         'source': {'$ne': 'h_int_stat'}}}] # not put on chart 'h_int_stat'
    pipeline = match + [elem for _currency in bond_currencies for elem in create_lookup(_currency)] \
               + [{'$sort': {'time': pymongo.ASCENDING}}] + [create_project(bond_currencies)]
    # print(pipeline)
    data = {}
    for currency in ['USD', 'EUR', 'RUB']:

        command_cursor = aware_times(currency).aggregate(pipeline)
    # {k: v for k, v in doc.items() if v != 0} delete fields with 0 from result
        data.update({currency:[reformat_for_js_bonds({k: v for k, v in doc.items() if v != 0})
                               for doc in command_cursor]})

    file = jsonify(data)
    file.headers['Content-Disposition'] = 'attachment;filename=' + 'int_bonds2' + '.json'
    return file

def bonds_json_lite2():
    usd = aware_times('USD')
    eur = aware_times('EUR')
    rub = aware_times('RUB')
    bonds_payments = aware_times('bonds_payments')
    min_date = datetime(year=2014, month=8, day=1, hour=17, minute=0, second=0, microsecond=0, tzinfo=local_tz)
    match_currencyf = {'time': {'$gte': min_date}, 'source': {'$ne': 'h_int_stat'}}
    all_dates = set([doc['time'] for doc in usd.find(match_currencyf, {'_id': False, 'time': True})])
    all_dates.update([doc['time'] for doc in eur.find(match_currencyf, {'_id': False, 'time': True})])
    all_dates.update([doc['time'] for doc in rub.find(match_currencyf, {'_id': False, 'time': True})])
    all_dates.update([doc['time'] for doc in bonds_payments.find({'time': {'$gte': min_date}},
                                                                 {'_id': False, 'time': True})])
    # lookup = [{'$lookup': {'from': 'bonds_payments', 'localField': 'time', 'foreignField': 'time', 'as': 'payments'}}]
    # --------- colect all bonds --------
    group_bonds = {'$group': {'_id': {'time' : '$time', 'currency': '$currency', 'pay_type': '$pay_type'},
                              'cash': {'$sum': '$cash'}}}
    project_bonds = {'$project': {'_id': False, 'currency': '$_id.currency', 'pay_type': '$_id.pay_type',
                                  'time': '$_id.time', 'cash': '$cash'}}
    command_cursor = bonds_payments.aggregate([group_bonds, project_bonds])
    bonds = {}
    # put bonds in dict
    # { time: {currency<1>_pay_type<1>: cash<1>,
    #          currency<2>_pay_type<1>: cash<2>,}}
    for doc in command_cursor:
        bonds[doc['time']] = {}
        if doc['pay_type'] == 'income':
            multiply = -1000000
        else:
            # (doc['pay_type'] == 'coupon') or (doc['pay_type'] == 'return'):
            multiply = 1000000
        bonds[doc['time']][doc['currency'] + '_' + doc['pay_type']] = round(doc['cash'] / multiply, 2)

    #     ------- collect all currencies ----------

    project_currency = {'$project': {'_id': False, 'buy': True, 'sell': True,
                        'amount_accepted_all': '$nbu_auction.amount_accepted_all',
                        'amount_requested': '$nbu_auction.amount_requested',
                        'nbu_auction_operation': '$nbu_auction.operation', 'nbu_rate': True, 'time': True}}
    match_currency = {'$match': {'source': {'$ne': 'h_int_stat'}}}
    project_currencyf = {'_id': False, 'buy': True, 'sell': True,
                        'nbu_auction.amount_accepted_all': True,
                        'nbu_auction.amount_requested': True,
                        'nbu_auction.operation': True, 'nbu_rate': True, 'time': True}

    data = {}
    data_out = {}
    # ---- create dict data with key time -------
    for currency in ['USD', 'EUR', 'RUB']:
        cursor = aware_times(currency).find(match_currencyf, project_currencyf)
        data[currency] = {}
        for doc in cursor:
            data[currency][doc['time']] = {}
            data[currency][doc['time']].update(reformat_for_js(doc))
    # ----- create doc with data from currencies and bonds, and put in a out_data[currency] sorted list
        data_out[currency] = []
        for date in sorted(all_dates):
            doc1 = data[currency].get(date, {})
            doc1.update(bonds.get(date, {}))
            doc1['time'] = date.strftime('%Y-%m-%d_%H')
            data_out[currency].append(doc1)
            print(data_out[currency][-1:])
    del data
    file = jsonify(data_out)
    file.headers['Content-Disposition'] = 'attachment;filename=' + 'bonds_curr' + '.json'
    return file


def stock_events():
    # time_auction is exists (not null)
    ovdp_match_find = {'source': 'mf', 'time_auction': {'$ne': None}}
    ovdp_project_find = {'_id': False, 'time_auction': True, 'headline': True}
    command_cursor = aware_times('news').find(ovdp_match_find, ovdp_project_find,
                                              sort=[('time_auction', pymongo.ASCENDING)])
    data = []
    for doc in command_cursor:
        doc['date'] = doc.pop('time_auction').strftime('%Y-%m-%d_%H')
        doc['text'] = 'A'
        doc['description'] = doc.pop('headline')
        doc['graph'] = 'sell'
        doc['showOnAxis'] = True
        doc['type'] = 'pin'
        data.append(doc)
    file = jsonify(data)
    file.headers['Content-Disposition'] = 'attachment;filename=' + 'events' + '.json'
    return file

if __name__ == '__main__':
    bonds_json_lite2()
    # print(stock_events())