import pymongo
from flask import jsonify
import json
from datetime import datetime, timedelta
from spiders.common_spider import local_tz

import pymongo
from wtforms.validators import Optional
from collections import defaultdict

from app import web_logging
# TODO: replace flask.ext.login, flask.ext.wtf
# /home/vic/flask/lib/python3.5/site-packages/flask/exthook.py:71: ExtDeprecationWarning: Importing flask.ext.login is deprecated, use flask_login instead.
#   .format(x=modname), ExtDeprecationWarning
# no environment config, default used
# /home/vic/flask/lib/python3.5/site-packages/flask/exthook.py:71: ExtDeprecationWarning: Importing flask.ext.wtf is deprecated, use flask_wtf instead
from flask import render_template, flash, redirect, url_for, abort, jsonify, request, make_response
from mongo_collector.mongo_start import DATABASE
from mongo_collector.mongo_start import data_active
from app.forms import LoginForm, Update_db, FilterBase, FormField, SortForm, FieldList
from mongo_collector.parallel import update_lists
import logging



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
            bond_doc = DATABASE[bond.collection].find_one({'_id': bond.id})
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
    doc['time'] = doc['time'].strftime('%Y-%m-%d')
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
    min_date = datetime(year=2014, month=8, day=1)
    match = [{'$match': {'$or': [{'repaydate': {'$gte' : min_date}}, {'time': {'$gte' : min_date}}],
                         'source': {'$ne': 'h_int_stat'}}}] # not put on chart 'h_int_stat'
    pipeline = match + [elem for _currency in bond_currencies for elem in create_lookup(_currency)] \
               + [{'$sort': {'time': pymongo.ASCENDING}}] + [create_project(bond_currencies)]
    # print(pipeline)
    data = {}
    for currency in ['USD', 'EUR', 'RUB']:

        command_cursor = DATABASE[currency].aggregate(pipeline)
    # {k: v for k, v in doc.items() if v != 0} delete fields with 0 from result
        data.update({currency:[reformat_for_js_bonds({k: v for k, v in doc.items() if v != 0})
                               for doc in command_cursor]})

    file = jsonify(data)
    file.headers['Content-Disposition'] = 'attachment;filename=' + 'int_bonds2' + '.json'
    return file

def bonds_json_lite2():
    usd = DATABASE['USD']
    eur = DATABASE['EUR']
    rub = DATABASE['RUB']
    ovdp = DATABASE['news']
    bonds_payments = DATABASE['bonds_payments']
    min_date = datetime(year=2014, month=8, day=1)
    match_currencyf = {'time': {'$gte': min_date}, 'source': {'$ne': 'h_int_stat'}}
    all_dates = set([doc['time'] for doc in usd.find(match_currencyf, {'_id': False, 'time': True})])
    all_dates.update([doc['time'] for doc in eur.find(match_currencyf, {'_id': False, 'time': True})])
    all_dates.update([doc['time'] for doc in rub.find(match_currencyf, {'_id': False, 'time': True})])
    all_dates.update([doc['time'] for doc in bonds_payments.find({'time': {'$gte': min_date}},
                                                                 {'_id': False, 'time': True})])
    # add dates of ovdp
    all_dates.update([doc['time_auction'] for doc in ovdp.find({'source': 'mf', 'time_auction': {'$ne': None}},
                                                       {'_id': False, 'time_auction': True})])
    # lookup = [{'$lookup': {'from': 'bonds_payments', 'localField': 'time', 'foreignField': 'time', 'as': 'payments'}}]
    # --------- colect all bonds --------
    # filter out document with metadata in _id==update
    match_bods = {'$match': {'_id': {'$ne': 'update'}}}
    group_bonds = {'$group': {'_id': {'time' : '$time', 'currency': '$currency', 'pay_type': '$pay_type'},
                              'cash': {'$sum': '$cash'}}}
    project_bonds = {'$project': {'_id': False, 'currency': '$_id.currency', 'pay_type': '$_id.pay_type',
                                  'time': '$_id.time', 'cash': '$cash'}}
    command_cursor = bonds_payments.aggregate([match_bods, group_bonds, project_bonds])
    bonds = defaultdict(dict)
    # put bonds in dict
    # { time: {currency<1>_pay_type<1>: cash<1>,
    #          currency<2>_pay_type<1>: cash<2>,}}
    for doc in command_cursor:
        # bonds[doc['time']] = {}
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
        cursor = DATABASE[currency].find(match_currencyf, project_currencyf)
        data[currency] = {}
        for doc in cursor:
            data[currency][doc['time']] = {}
            data[currency][doc['time']].update(reformat_for_js(doc))
    # ----- create doc with data from currencies and bonds, and put in a out_data[currency] sorted list
        data_out[currency] = []
        # workaround -delete dates with hours != 0
        all_dates = set([datetime(year=i.year, month=i.month, day=i.day) for i in all_dates])
        for date in sorted(all_dates):
            doc1 = data[currency].get(date, {})
            # add field for virtual line
            doc1['dummy'] = doc1.get('sell', 25)
            doc1.update(bonds.get(date, {}))
            doc1['time'] = date.strftime('%Y-%m-%d_%H')
            # doc1['time'] = doc1.get('time', date.strftime('%Y-%m-%d_%H'))
            data_out[currency].append(doc1)
            # print(data_out[currency][-1:])
    del data
    if __name__ == '__main__':
        # show data in console directly
        return data_out
    else:
        file = jsonify(data_out)
        file.headers['Content-Disposition'] = 'attachment;filename=' + 'bonds_curr' + '.json'
        return file


def stock_events():
    # time_auction is exists (not null)
    ovdp_match_find = {'source': 'mf', 'time_auction': {'$ne': None}}
    ovdp_project_find = {'_id': False, 'time_auction': True, 'headline': True}
    command_cursor = DATABASE['news'].find(ovdp_match_find, ovdp_project_find,
                                              sort=[('time_auction', pymongo.ASCENDING)])
    data = []
    for doc in command_cursor:
        doc['date'] = doc.pop('time_auction').strftime('%Y-%m-%d_%H')
        doc['text'] = 'A'
        doc['description'] = doc.pop('headline')
        doc['graph'] = 'dummy'
        doc['showOnAxis'] = True
        doc['type'] = 'pin'
        data.append(doc)
    file = jsonify(data)
    file.headers['Content-Disposition'] = 'attachment;filename=' + 'events' + '.json'
    return file


def lists_fun(**kwargs):

    # hidden_filter = kwargs.get('hidden', {'$or': [{'hidden': {'$exists': False}}, {'hidden': False}]})
    hidden_filter = kwargs.get('hidden', {})
    title = kwargs.get('title', '')
    # modify a form dynamically in your view. This is possible by creating internal subclasses
    # http://wtforms.simplecodes.com/docs/1.0.1/specific_problems.html#dynamic-form-composition
    class Filter(FilterBase):
        pass
    setattr(Filter, 'sort_order', FieldList(FormField(SortForm), min_entries=3, validators=[Optional()]))
    # ------------------------------
    form_update = Update_db()
    form_filter = Filter()
    filter_recieved = {'location': form_filter.locations.data, 'operation': form_filter.operations.data,
                        'currency': form_filter.currencies.data, 'source': form_filter.sources.data,
                        '$text': {'$search': form_filter.text.data}}
    filter_recieved.update(hidden_filter)
    direction_dict = {'ASCENDING': pymongo.ASCENDING, 'DESCENDING': pymongo.DESCENDING}
    # --- filter for top orders ---
    current_time = datetime.now(tz=local_tz)
    try:
        time_delta = timedelta(hours=form_filter.top_hours.data)
    except TypeError:
        time_delta = timedelta(hours=1)
    top_start_time = current_time - time_delta
    top_filter = {**filter_recieved, 'time': {'$gte': top_start_time}}
    top_limit = form_filter.top_limit.data
    if form_filter.operations.data == 'buy':
        top_sort = [('rate', pymongo.DESCENDING)]
    else:
        top_sort = [('rate', pymongo.ASCENDING)]


    sort_list = [(group_order.form.sort_field.data, direction_dict[group_order.form.sort_direction.data])
                 for group_order in form_filter.sort_order if group_order.form.sort_field.data != 'None']
    print(sort_list)
    # sort_list = [('time', pymongo.DESCENDING)]
    def mongo_request(original: dict) -> dict:

        mongo_dict = dict(original)
        for key, val in original.items():
            if (val == 'None' or val == 'all') and key != '$text':
                del mongo_dict[key]
            elif key == '$text' and (val == {'$search': ''} or val == {'$search': None}):
                del mongo_dict[key]
        return mongo_dict

    if form_update.db.data:
        web_logging.debug('update db pushed')
        active_deleted = update_lists()
        flash('recived db= {}, deleted docs={}'.format(str(form_update.db.data), active_deleted))
        flash('top_filter: {}, top_sort: {}, top_limit: {}'.format(top_filter, top_sort, top_limit))
        result = data_active.find(mongo_request(filter_recieved))
        result_top = data_active.find(mongo_request(top_filter), sort=top_sort, limit=top_limit)
        # replace validate_on_submit to is_submitted in reason sort_order in class Filter
        # TODO: form validation !!!, currently buldin form validators=[Optional()]
    elif form_filter.validate_on_submit():
        web_logging.debug('filter pushed')
        flash('filter: City={city}, currency={currency},  Operation={operation}, source={source},<br>'
              'text={text}'.format(text=filter_recieved['$text'], city=filter_recieved['location'],
                                   operation=filter_recieved['operation'], currency=filter_recieved['currency'],
                                   source=filter_recieved['source']))
        flash('Sort: {sort_list}'.format(sort_list=sort_list))
        flash('top_filter: {}, top_sort: {}, top_limit: {}'.format(top_filter, top_sort, top_limit))
        result = data_active.find(mongo_request(filter_recieved), sort=sort_list)
        result_top = data_active.find(mongo_request(top_filter), sort=top_sort, limit=top_limit)
    elif request.method == 'POST' and not form_filter.validate():
        result = []
        result_top = []
        # result = data_active.find(mongo_request(filter_recieved), sort=([('time', pymongo.DESCENDING)]))
        # result_top = data_active.find(mongo_request(top_filter), sort=top_sort, limit=top_limit)
    else:
        # default (initial) page
        result = data_active.find(mongo_request(filter_recieved), sort=([('time', pymongo.DESCENDING)]))
        result_top = data_active.find(mongo_request(top_filter), sort=top_sort, limit=top_limit)

    return render_template('lists.html',
                           title=title,
                           form_update=form_update,
                           form_filter=form_filter,
                           result=result,
                           result_top=result_top)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    from spiders.common_spider import date_handler
    print(json.dumps(bonds_json_lite2(), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False,
                     default=date_handler))
