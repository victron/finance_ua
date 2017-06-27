from wtforms import StringField, SelectField, SubmitField, PasswordField, FormField, FieldList, \
    IntegerField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Optional, NumberRange
from wtforms import validators

from wtforms.fields.html5 import TelField

from flask_wtf import Form
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


class SortNumbers(Form):
    sort_fields_set = {'number', 'time_update', 'time_create'}
    sort_direction_set = {'ASCENDING', 'DESCENDING'}
    none = [('None', 'None')]
    sort_field = SelectField('field', choices=none + [(field, field) for field in sort_fields_set], default='None')
    sort_direction = SelectField('direction', choices=[(direct, direct) for direct in sort_direction_set],
                                 default='DESCENDING')


class FilterNumbers(Form):
    all_options = [('all', 'all')]
    contact_type = {'white', 'black', 'grey'}
    contact_type = SelectField('list_type', choices=all_options + [(type, type) for type in contact_type], default='white')
    number = StringField('number', validators=[Optional()])
    comment = StringField('comment', validators=[Optional()])
    # add SortNumbers
    sort_order = FieldList(FormField(SortNumbers), min_entries=3, validators=[Optional()])
    filter = SubmitField('Filter')


class DeleteNumber(Form):
    record_id = HiddenField('record_id', [validators.InputRequired()])
    # added FilterNumbers
    filters = HiddenField(FormField(FilterNumbers), [Optional()])
    # https://stackoverflow.com/questions/16849117/html-how-to-do-a-confirmation-popup-to-a-submit-button-and-then-send-the-reque
    # https://www.w3schools.com/jsref/met_win_confirm.asp
    # with simple confirm window
    delete = SubmitField('delete', render_kw={'onclick': 'return confirm(\'Are you sure?\')'})

class SaveNumber(Form):
    nic = StringField('nic', validators=[Optional(), validators.Length(min=4, max=30),
                                         validators.input_required()],
                      render_kw={'placeholder': u'Лукьяновка ТЦ Призма'})
    org_type = {'person', 'exchange', 'operator'}
    org_type = SelectField('Org type', choices=[(org, org) for org in org_type],
                           validators=[validators.input_required()], default='exchange')
    contact_type = {'white', 'black', 'grey'}
    contact_type = SelectField('Contact Type', choices=[(type, type) for type in contact_type],
                               validators=[validators.input_required()],
                               default='grey')
    names = StringField('Name(s)', validators=[Optional(), validators.Length(max=30)],
                        render_kw={'placeholder': u'Вероника, Алена'})
    numbers = TelField('Number(s)', validators=[validators.InputRequired(), validators.Regexp('^(0(\d\s*){9},?\s*)*$'),
                                             validators.Length(min=10, max=100)],
                       description='numbers with 10 digits separated by \',\'; field required; '
                                   '(format: 0XXXXXXXXX or 0XX XXX XX XX)',
                       render_kw={'placeholder': '0XXXXXXXXX or 0XX XXX XX XX'})

    gen_comments = TextAreaField('Comments about contact', [Optional(), validators.Length(max=200)],
                                 render_kw={'placeholder': u'висока и сиськаста блондинка'})
    city = StringField('City', validators=[Optional(), validators.Length(max=30)], default=u'Київ')
    street = StringField('Str.', validators=[Optional(), validators.Length(max=40)])
    building = StringField('bld.', validators=[Optional(), validators.Length(max=3)])
    loc_comment = TextAreaField('Location comments', validators=[Optional(), validators.Length(max=250)],
                                render_kw={'placeholder': u'далеко від метро, але чувак може під\'їхати '
                                                          '(мермедес АА1234фф)'})

class Transaction(Form):
    time_to_meet = StringField('time_to_meet', validators=[Optional()]) # TODO: should present
    rate = StringField('rate', validators=[Optional()])
    amount = StringField('amount', validators=[Optional()])
    my_comments = StringField('my_comments', validators=[Optional()])
    time_to_finished = StringField('time_to_finished', validators=[Optional()])


class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])