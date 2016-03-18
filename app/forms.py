from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, StringField
from wtforms.validators import Required, DataRequired

class LoginForm(Form):
    openid = StringField('openid', validators = [DataRequired()])
    remember_me = BooleanField('remember_me', default = False)