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

if __name__ == '__main__':
    pass