import pymongo
from flask import render_template, flash, redirect, url_for, abort, jsonify
from flask.ext.login import login_user, logout_user, login_required
from mongo_collector.mongo_update import update_db, mongo_insert_history

from app import app, web_logging
from mongo_collector.mongo_start import aware_times
from mongo_collector.mongo_start import data_active, bonds
from mongo_collector.mongo_start import news as news_db
from spiders.common_spider import  main_currencies
from spiders.filters import location, currency, operation, filter_or
from spiders.news_minfin import minfin_headlines
from .forms import LoginForm, Update_db, FilterBase, FormField, SortForm, FieldList
from wtforms.validators import DataRequired, Optional
from .user import User
from .views_func import reformat_for_js, octothorpe2

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
    mongo_request = dict(filter_recieved)
    direction_dict = {'ASCENDING': pymongo.ASCENDING, 'DESCENDING': pymongo.DESCENDING}
    sort_list = [(group_order.form.sort_field.data, direction_dict[group_order.form.sort_direction.data])
                 for group_order in form_filter.sort_order if group_order.form.sort_field.data != 'None']
    print(sort_list)
    # sort_list = [('time', pymongo.DESCENDING)]
    for key, val in filter_recieved.items():
        if (val == 'None' or val == 'all') and key != '$text':
            del mongo_request[key]
        elif key == '$text' and (val == {'$search': ''} or val == {'$search': None}):
            del mongo_request[key]

    if form_update.db.data:
        web_logging.debug('update db pushed')
        active_deleted = update_db()
        flash('recived db= {}, deleted docs={}'.format(str(form_update.db.data), active_deleted))
        result = data_active.find(mongo_request)
        # replace validate_on_submit to is_submitted in reason sort_order in class Filter
        # TODO: form validation !!!, currently buldin form validators=[Optional()]
    elif form_filter.validate_on_submit():
        web_logging.debug('filter pushed')
        flash('filter: City={city}, currency={currency},  Operation={operation}, source={source},<br>'
              'text={text}'.format(text=filter_recieved['$text'], city=filter_recieved['location'],
                                   operation=filter_recieved['operation'], currency=filter_recieved['currency'],
                                   source=filter_recieved['source']))
        flash('Sort: {sort_list}'.format(sort_list=sort_list))
        result = data_active.find(mongo_request, sort=(sort_list))
    else:
        result = data_active.find(mongo_request, sort=([('time', pymongo.DESCENDING)]))

    return render_template('lists.html',
                           title='Lists',
                           form_update=form_update,
                           form_filter=form_filter,
                           result=result)


@app.route('/news', methods=['GET', 'POST'])
@login_required
def news():
    form_update = Update_db()
    if form_update.db.data:
        inserted_count, duplicate_count = mongo_insert_history(minfin_headlines(), news_db)
        flash('inserted: {}, duplicated: {}'.format(inserted_count, duplicate_count))
    mongo_request = {}
    result = news_db.find(mongo_request, sort=([('time', pymongo.DESCENDING)]))
    return render_template('news.html',
                           title='News',
                           result=result,
                           form_update=form_update)

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
        mongo_request = {}
        projection = {'_id': False, 'time': True, 'sell': True, 'buy': True, 'nbu_rate': True,
                      'nbu_auction.amount_requested': True, 'nbu_auction.amount_accepted_all': True,
                      'nbu_auction.operation': True}
        cursor = aware_times(currency).find(mongo_request, projection, sort=([('time', pymongo.ASCENDING)]))
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
        project.update({'_id': False, 'buy': True, 'sell': True,
                        'amount_accepted_all': '$nbu_auction.amount_accepted_all',
                        'amount_requested': '$nbu_auction.amount_requested',
                        'nbu_auction_operation': '$nbu_auction.operation', 'nbu_rate': True, 'time': True})
        return {'$project': project}

    pipeline = [elem for _currency in bond_currencies for elem in create_lookup(_currency)] \
               + [{ '$sort' : { 'time' : pymongo.ASCENDING}}] + [create_project(bond_currencies)]
    # print(pipeline)
    command_cursor = aware_times(currency).aggregate(pipeline)
    data = {currency:[octothorpe2(doc) for doc in command_cursor]}
    file = jsonify(data)
    file.headers['Content-Disposition'] = 'attachment;filename=' + 'int_bonds2' + '.json'
    return file


