import pymongo
from wtforms.validators import Optional
import requests


from curs import app, web_logging
# TODO: replace flask.ext.login, flask.ext.wtf
# /home/vic/flask/lib/python3.5/site-packages/flask/exthook.py:71: ExtDeprecationWarning: Importing flask.ext.login is deprecated, use flask_login instead.
#   .format(x=modname), ExtDeprecationWarning
# no environment config, default used
# /home/vic/flask/lib/python3.5/site-packages/flask/exthook.py:71: ExtDeprecationWarning: Importing flask.ext.wtf is deprecated, use flask_wtf instead
from flask_login import login_user, logout_user, login_required
from flask import render_template, flash, redirect, url_for, abort, jsonify, request, make_response
from mongo_collector.mongo_start import DATABASE
from mongo_collector.mongo_start import data_active, bonds
from mongo_collector.mongo_start import news as news_db
from spiders.common_spider import  main_currencies
from curs.forms import LoginForm, Update_db, FilterBase, FormField, SortForm, FieldList
from curs.user import User
from curs.views_func import reformat_for_js, reformat_for_js_bonds, bonds_json_lite, bonds_json_lite2, stock_events
from mongo_collector.parallel import update_lists
from mongo_collector.parallel import update_news
from datetime import datetime, timedelta
from spiders.common_spider import local_tz
from spiders.parse_minfin import get_contacts, bid_to_payload
from curs.views_func import lists_fun
import json
from curs.rest_client import update, req_template
# web_logging.getLogger(__name__)


@app.route('/')
@app.route('/index')
@login_required
def index():
    user = { 'nickname': 'Miguel' } # выдуманный пользователь
    posts = [ # список выдуманных постов
        {
            'author': { 'nickname': 'John' },
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': { 'nickname': 'Susan' },
            'body': 'The Avengers movie was so cool!'
        }
    ]
    # result = data_active.find({'location': location, 'currency': currency, 'operation': operation,
    #                            '$text': {'$search': filter_or}})

    return render_template('index.html',
                           title='Home',
                           user=user,
                           posts=posts,
                           # result=result
                           )

@app.route('/lists', methods= ['GET', 'POST'])
@login_required
def lists():
    kwargs = {'hidden': {'$or': [{'hidden': {'$exists': False}}, {'hidden': False}]},
              'title': 'Lists'}
    return lists_fun(**kwargs)

@app.route('/lists_hidden', methods= ['GET', 'POST'])
@login_required
def lists_hidden():
    kwargs = {'hidden': {'hidden': True}, 'title': 'Hidden Lists'}
    return lists_fun(**kwargs)



@app.route('/news', methods=['GET', 'POST'])
@login_required
def news():
    form_update = Update_db()
    if form_update.db.data:
        flash(json.dumps(update('news')))
        # inserted_count, duplicate_count = update_news()
        # flash('inserted: {}, duplicated: {}'.format(inserted_count, duplicate_count))
    mongo_request = {}
    result = news_db.find(mongo_request, sort=([('time', pymongo.DESCENDING)]))
    return render_template('news.html',
                           title='News',
                           result=result,
                           form_update=form_update)

# ------- api POSTs methods ---------

@app.route('/api/mincontacts', methods=['POST'])
@login_required
def mincontacts():
    if request.method == 'POST':
        req_json = request.get_json()
        web_logging.debug('req_json= {}'.format(req_json))

        # -------- request to spiders -------
        url = 'http://localhost:9080/command'
        data = {**{'Mcontact': req_json}, **req_template}
        headers = {'content_type': 'application/json'}
        doc_json = requests.get(url, headers=headers, json=data, timeout=40).json()
        web_logging.debug('doc_json= {}'.format(doc_json))
        # ===================================

        resp = make_response(json.dumps(doc_json))
        resp.headers['Content-Type'] = 'application/json'

        phone = doc_json['contact']
        print('phone=', phone)
        # put real nuumber in DB
        data_active.update_one({'bid': req_json['bid'], 'source': 'm'}, {'$set': {'phone': phone}})
        return resp

@app.route('/api/hide', methods=['POST'])
@login_required
def hide_in_list():
    req_json = request.get_json()
    hide = req_json.pop('hide')
    if hide:
        result = data_active.update_one(req_json,
                                        {'$set': {'hidden': True}})
    else:
        result = data_active.update_one(req_json,
                                        {'$set': {'hidden': False}})
    if result.modified_count == 1:
        responce = {'code': 0, 'message': 'OK'}
    else:
        responce = {'code': 1, 'message': 'NOK'}
    resp = make_response(json.dumps(responce))
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route('/charts')
@login_required
def charts():
    return render_template('charts.html', title='Charts')
    # --------------- not needed because now data loaded via api ----------
    # out_dict = {}
    # projection = {'_id': False, 'time': True, 'sell': True, 'buy': True, 'nbu_rate': True,
    #               'nbu_auction.amount_requested': True, 'nbu_auction.amount_accepted_all': True,
    #               'nbu_auction.operation': True}
    # for currency in main_currencies:
    #     mongo_request = {}
    #     cursor = aware_times(currency).find(mongo_request, projection, sort=([('time', pymongo.ASCENDING)]))
    #     out_dict[currency] = [reformat_for_js(doc) for doc in cursor]
    # return render_template('charts.html',
    #                        usd=json.dumps(out_dict.get('USD')),
    #                        eur=json.dumps(out_dict.get('EUR')),
    #                        rub=json.dumps(out_dict.get('RUB')),
    #                        title='Charts')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = app.config['USERS_COLLECTION'].find_one({"_id": form.username.data})
        if user and User.validate_login(user['password'], form.password.data):
            user_obj = User(user['_id'])
            login_user(user_obj)
            flash("Logged in successfully", category='success')
            # next = request.args.get('next')
            # if not next_is_valid(next):
            #     return abort(400)
            return redirect('/index')
        flash("Wrong username or password", category='error')
    return render_template('login.html', title='login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash("You were logged out", category='success')
    return redirect(url_for('login'))


# json output
@app.route('/api/history/<currency>')
@login_required
def history_json(currency):
    currency = currency.upper()


    if currency in main_currencies:
        mongo_request = {"$or": [{"source": "d_int_stat"}, {"source": "d_ext_stat"}]}
        projection = {'_id': False, 'time': True, 'sell': True, 'buy': True, 'nbu_rate': True,
                      'nbu_auction.amount_requested': True, 'nbu_auction.amount_accepted_all': True,
                      'nbu_auction.operation': True, 'source': True}
        cursor = DATABASE[currency].find(mongo_request, projection, sort=([('time', pymongo.ASCENDING)]))
        data = {currency: [reformat_for_js(doc) for doc in cursor]} # dict for transfere parameter currency in json
        file = jsonify(data)
        file.headers['Content-Disposition'] = 'attachment;filename=' + currency + '.json'
        return file
        #return in HTTP
        # return jsonify(USD=[{'time': data['time'].strftime('%Y-%m-%d'),
        #                          'value': data.get('USD', {}).get('buy', None)}
        #                         for data in cursor])
    else:
        abort(404)


@app.route('/api/bonds')
@login_required
def bonds_json():
    data = {}
    for key in ('auctiondate', 'paydate', 'repaydate'):
        mongo_request = {}
        projection = {'_id': False, key: True, 'avglevel' : True , 'amount' : True , 'amountn' : True ,
                      'auctionnum' : True , 'incomelevel' : True, 'attraction' : True , 'stockrestrict' : True ,
                      'valcode' : True , 'stockcode' : True , 'stockrestrictn': True}
        cursor = bonds.find(mongo_request, projection, sort=([(key, pymongo.ASCENDING)]))
        data.update({key: [doc for doc in cursor]})
    file = jsonify(data)
    file.headers['Content-Disposition'] = 'attachment;filename=' + 'int_bonds' + '.json'
    return file

@app.route('/api/ukrstat')
@login_required
def ukrstat_json():
    data = {}
    mongo_request = {}
    projection = {'$time': '$id', 'import': True, 'export': True}
    cursor = DATABASE['ukrstat'].find(mongo_request, projection, sort=([('_id', pymongo.ASCENDING)]))

    # data.update({'ukrstat': cursor})
    data.update({'ukrstat': []})
    # previous_doc = None
    for doc in cursor:
        doc['time'] = doc['_id']
        del doc['_id']

    # below commented for import_stat(date) function, currently migrated to ukrstat().saldo()
    #     if previous_doc is not None:
    #         month = doc['time'].month
    #         if month != 1:
    #             if month == previous_doc['time'].month + 1:
    #                 doc['_import'] = round((doc['import'] - previous_doc['import'])/1000000, 2)
    #                 doc['_export'] = round((doc['export'] - previous_doc['export'])/1000000, 2)
        doc['saldo'] = doc['import'] - doc['export']
    #                 previous_doc = dict(doc)
    #         else:
    #             previous_doc = dict(doc)
    #             doc['import'] = round(doc['import']/1000000, 2)
    #             doc['export'] = round(doc['export']/1000000, 2)
    #             doc['saldo'] = doc['import'] - doc['export']
    #     else:
    #         previous_doc = dict(doc)
    #         doc['import'] = round(doc['import'] / 1000000, 2)
    #         doc['export'] = round(doc['export'] / 1000000, 2)
    #         doc['saldo'] = doc['import'] - doc['export']
    #
        data['ukrstat'].append(doc)
    # for doc in data['ukrstat']:
    #     if '_import' in doc:
    #         doc['import'] = doc.pop('_import')
    #         doc['export'] = doc.pop('_export')
    file = jsonify(data)
    file.headers['Content-Disposition'] = 'attachment;filename=' + 'ukrstat' + '.json'
    return file

@app.route('/api/bonds2')
@login_required
def bonds_json2():
    bond_currencies = ['UAH', 'USD', 'EUR']
    currency = 'USD'
    # bond_currency = 'UAH'
    def create_lookup(bond_currency: str) -> list:
        return [{'$lookup': {'from': 'bonds_' + bond_currency, 'localField': 'time', 'foreignField': 'repaydate',
                             'as': 'repay_' + bond_currency}},
                {'$lookup': {'from': 'bonds_' + bond_currency, 'localField': 'time', 'foreignField': 'paydate',
                             'as': 'pay_' + bond_currency}},
                {'$lookup': {'from': 'bonds_' + bond_currency, 'localField': 'time', 'foreignField': 'auctiondate',
                             'as': 'auctiondate_' + bond_currency}}]

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

    pipeline = [elem for _currency in bond_currencies for elem in create_lookup(_currency)] \
               + [{'$sort': {'time': pymongo.ASCENDING}}] + [create_project(bond_currencies)]
    # print(pipeline)
    command_cursor = DATABASE[currency].aggregate(pipeline)
    # {k: v for k, v in doc.items() if v != 0} delete fields with 0 from result
    data = {currency:[reformat_for_js_bonds({k: v for k, v in doc.items() if v != 0}) for doc in command_cursor]}

    file = jsonify(data)
    file.headers['Content-Disposition'] = 'attachment;filename=' + 'int_bonds2' + '.json'
    return file

@app.route('/api/bonds3')
@login_required
def bonds_json3():
    return bonds_json_lite2()


@app.route('/api/ovdp')
@login_required
def ovdp():
    return stock_events()
