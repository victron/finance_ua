from wtforms import StringField, SelectField, SubmitField, PasswordField, FormField, FieldList, \
    IntegerField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Optional, NumberRange
from wtforms import validators

from wtforms.fields.html5 import TelField

from flask_wtf import FlaskForm

from mongo_collector.mongo_update import get_selection


class Update_db(FlaskForm):
    # db_value = 'update'
    # db = HiddenField('db', validators=[AnyOf([db_value])], default=db_value)
    db = SubmitField('Update')



class SortForm(FlaskForm):
    sort_fields_set = {'time', 'rate', 'amount', 'phone'}
    sort_direction_set = {'ASCENDING', 'DESCENDING'}
    none = [('None', 'None')]
    sort_field = SelectField('field', choices=none + [(field, field) for field in sort_fields_set], default='None')
    sort_direction = SelectField('direction', choices=[(direct, direct) for direct in sort_direction_set],
                                 default='DESCENDING')

class FilterBase(FlaskForm):
    locations, operations, currencies, sources = get_selection()
    text = StringField('text', validators=[Optional()])
    top_limit = IntegerField('number in top to show', [NumberRange(min=1, max=10)], default=7)
    top_hours = IntegerField('number of hours to show', [NumberRange(min=1, max=5)], default=1)
    all_options = [('all', 'all')]
    locations = SelectField('locations', choices=all_options + [(city, city) for city in locations], default='Киев')
    operations = SelectField('operations', choices=all_options +
                                                   [(operation, operation) for operation in operations], default='sell')
    currencies = SelectField('currencies', choices=all_options +
                                                   [(currency, currency) for currency in currencies], default='USD')
    sources = SelectField('sources', choices=all_options + [(source, source) for source in sources], default='all')

# class Filter(Form):
# same as FilterBase, difference in sort_order. It fixed here.
# in above could be modify from view
#     locations, operations, currencies, sources = get_selection()
#     text = StringField('text', validators=[Optional()])
#     all_options = [('all', 'all')]
#     locations = SelectField('locations', choices=all_options + [(city, city) for city in locations], default='Киев')
#     operations = SelectField('operations', choices=all_options +
#                                                    [(operation, operation) for operation in operations], default='sell')
#     currencies = SelectField('currencies', choices=all_options +
#                                                    [(currency, currency) for currency in currencies], default='USD')
#     sources = SelectField('sources', choices=all_options + [(source, source) for source in sources], default='all')
#     sort_order = FieldList(FormField(SortForm), min_entries=2)




class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])