from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, StringField, HiddenField, FieldList, SelectField, SubmitField
from wtforms.validators import Required, DataRequired, AnyOf, Optional
from mongo_update import get_selection

class LoginForm(Form):
    openid = StringField('openid', validators = [DataRequired()])
    remember_me = BooleanField('remember_me', default = False)

class Update_db(Form):
    # db_value = 'update'
    # db = HiddenField('db', validators=[AnyOf([db_value])], default=db_value)
    db = SubmitField('Update')

class Filter(Form):
    locations, operations, currencies, sources = get_selection()
    text = StringField('text', validators=[Optional()])
    locations = SelectField('locations', choices=[(city, city) for city in locations.union({'all'})], default='Киев')
    operations = SelectField('operations', choices=[(operation, operation) for operation in operations.union({'all'})],
                             default='sell')
    currencies = SelectField('currencies', choices=[(currency, currency) for currency in currencies.union({'all'})],
                             default='USD')
    sources = SelectField('currencies', choices=[(source, source) for source in sources.union({'all'})], default='all')

