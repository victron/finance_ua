from flask.ext.wtf import Form
from wtforms import StringField, SelectField, SubmitField, PasswordField, FormField, FieldList
from wtforms.validators import DataRequired, Optional

from mongo_collector.mongo_update import get_selection


# class LoginFormoid(Form):
#     openid = StringField('openid', validators = [DataRequired()])
#     remember_me = BooleanField('remember_me', default = False)


class Update_db(Form):
    # db_value = 'update'
    # db = HiddenField('db', validators=[AnyOf([db_value])], default=db_value)
    db = SubmitField('Update')


class SortForm(Form):
    sort_fields_set = {'time', 'rate', 'amount', 'phone'}
    sort_direction_set = {'ASCENDING', 'DESCENDING'}
    none = [('None', 'None')]
    sort_field = SelectField('field', choices=none + [(field, field) for field in sort_fields_set], default='None')
    sort_direction = SelectField('direction', choices=[(direct, direct) for direct in sort_direction_set],
                                 default='DESCENDING')

class FilterBase(Form):
    locations, operations, currencies, sources = get_selection()
    text = StringField('text', validators=[Optional()])
    all_options = [('all', 'all')]
    locations = SelectField('locations', choices=all_options + [(city, city) for city in locations], default='Киев')
    operations = SelectField('operations', choices=all_options +
                                                   [(operation, operation) for operation in operations], default='sell')
    currencies = SelectField('currencies', choices=all_options +
                                                   [(currency, currency) for currency in currencies], default='USD')
    sources = SelectField('sources', choices=all_options + [(source, source) for source in sources], default='all')



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
    sort_order = FieldList(FormField(SortForm), min_entries=2)

class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])