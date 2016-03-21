from app import app
from flask import render_template, flash, redirect
from .forms import LoginForm, Update_db, Filter
from mongo_start import data_active
from mongo_update import update_db
from filters import location, currency, operation, filter_or

@app.route('/')
@app.route('/index')
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
        result = data_active.find(mongo_request)
    else:
        result = data_active.find(mongo_request)

    return render_template('lists.html',
                           title='Lists',
                           form_update=form_update,
                           form_filter=form_filter,
                           result=result)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for OpenID="' + form.openid.data + '", remember_me=' + str(form.remember_me.data))
        return redirect('/index')
    return render_template('login.html',
                            title = 'Sign In',
                            form = form,
                            providers = app.config['OPENID_PROVIDERS'])