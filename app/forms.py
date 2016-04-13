from flask.ext.wtf import Form
from wtforms import StringField, SelectField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Optional

from mongo_collector.mongo_update import get_selection


# class LoginFormoid(Form):
#     openid = StringField('openid', validators = [DataRequired()])
#     remember_me = BooleanField('remember_me', default = False)


class Update_db(Form):
    # db_value = 'update'
    # db = HiddenField('db', validators=[AnyOf([db_value])], default=db_value)
    db = SubmitField('Update')


class Filter(Form):
    locations, operations, currencies, sources = get_selection()
    text = StringField('text', validators=[Optional()])
    all_options = [('all', 'all')]
    locations = SelectField('locations', choices=all_options + [(city, city) for city in locations], default='Киев')
    operations = SelectField('operations', choices=all_options +
                                                   [(operation, operation) for operation in operations], default='sell')
    currencies = SelectField('currencies', choices=all_options +
                                                   [(currency, currency) for currency in currencies], default='USD')
    sources = SelectField('sources', choices=all_options + [(source, source) for source in sources], default='all')


class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])