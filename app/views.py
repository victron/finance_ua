from app import app
from flask import render_template, flash, redirect, url_for, request, abort, jsonify
from .forms import LoginForm, Update_db, Filter
from mongo_start import data_active, history
from mongo_start import news as news_db
from mongo_start import db, aware_times
from mongo_update import update_db, mongo_insert_history
from filters import location, currency, operation, filter_or
from flask.ext.login import login_user, logout_user, login_required
from .user import User, load_user
from news_minfin import minfin_headlines
import pymongo
from datetime import datetime
from common_spider import  main_currencies
import json



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
    result = data_active.find({'location': location, 'currency': currency, 'operation': operation,
                               '$text': {'$search': filter_or}})

    return render_template('index.html',
                           title='Home',
                           user=user,
                           posts=posts,
                           result=result)

@app.route('/lists', methods= ['GET', 'POST'])
@login_required
def lists():
    form_update = Update_db()
    form_filter = Filter()
    filter_recieved = {'location': form_filter.locations.data, 'operation': form_filter.operations.data,
                        'currency': form_filter.currencies.data, 'source': form_filter.sources.data,
                        '$text': {'$search': form_filter.text.data}}
    mongo_request = dict(filter_recieved)
    for key, val in filter_recieved.items():
        if (val == 'None' or val == 'all') and key != '$text':
            del mongo_request[key]
        elif key == '$text' and (val == {'$search': ''} or val == {'$search': None}):
            del mongo_request[key]

    if form_update.db.data:
        active_deleted = update_db()
        flash('recived db= {}, deleted docs={}'.format(str(form_update.db.data), active_deleted))
        result = data_active.find(mongo_request)
    elif form_filter.validate_on_submit():
        flash('filter: City={city}, currency={currency},  Operation={operation}, source={source},<br>'
              'text={text}'.format(text=filter_recieved['$text'], city=filter_recieved['location'],
                                   operation=filter_recieved['operation'], currency=filter_recieved['currency'],
                                   source=filter_recieved['source']))
        result = data_active.find(mongo_request, sort=([('time', pymongo.DESCENDING)]))
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
    # TODO: load data to js via api
    # from mongo_start import history
    out_dict = {}
    projection = {'_id': False, 'time': True, 'sell': True, 'buy': True, 'nbu_rate': True,
                  'nbu_auction.amount_requested': True, 'nbu_auction.amount_accepted_all': True,
                  'nbu_auction.operation': True}
    octothorpe = lambda x, dictionary: x * -1 if dictionary['nbu_auction']['operation'] == 'buy' else x

    def reformat_for_js(doc):
        if 'nbu_auction' in doc:
            doc['amount_requested'] = octothorpe(doc['nbu_auction'].pop('amount_requested'), doc)
            doc['amount_accepted_all'] = octothorpe(doc['nbu_auction'].pop('amount_accepted_all'), doc)
            del doc['nbu_auction']
        doc['time'] = doc['time'].strftime('%Y-%m-%d_%H')
        return doc

    for currency in main_currencies:
        mongo_request = {}
        # TODO: create universal way for access to collections
        cursor = aware_times(currency).find(mongo_request, projection, sort=([('time', pymongo.ASCENDING)]))
        out_dict[currency] = [reformat_for_js(doc) for doc in cursor]
    return render_template('charts.html',
                           usd=json.dumps(out_dict.get('USD')),
                           eur=json.dumps(out_dict.get('EUR')),
                           rub=json.dumps(out_dict.get('RUB')),
                           title='Charts')

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
    return redirect(url_for('login'))


# json output
@app.route('/api/history/<currency>')
@login_required
def history_json(currency):
    currency = currency.upper()
    if currency in ['USD', 'EUR', 'RUB']:
        mongo_request = {}
        db_request = db[currency]
        cursor = db_request.find(mongo_request, {'_id': 0}, sort=([('time', pymongo.DESCENDING)]))
        # return file
        # data = {currency: [{'time': data['time'].strftime('%Y-%m-%d'),
        #                     'value': data.get(currency, {}).get('buy', None)}
        #                    for data in cursor]}
        data = {currency: [ time_string(doc) for doc in cursor]} # dict for transfere parameter currency in json
        file = jsonify(data)
        file.headers['Content-Disposition'] = 'attachment;filename=' + currency + '.json'
        return file
        #return in HTTP
        # return jsonify(USD=[{'time': data['time'].strftime('%Y-%m-%d'),
        #                          'value': data.get('USD', {}).get('buy', None)}
        #                         for data in cursor])
    else:
        abort(404)