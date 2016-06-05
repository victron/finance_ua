#!__VENV_PYTHON__
# https://habrahabr.ru/post/196810/
# http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iii-web-forms
# ---- mongo docs ----
# https://docs.mongodb.org/ecosystem/tutorial/write-a-tumblelog-application-with-flask-mongoengine/
# https://www.zharenkov.ru/post/write-a-tumblelog-application-with-flask-mongoenginev

from flask import Flask
from flask.ext.login import LoginManager
import os
import sys

# from flask.ext.mongoengine import MongoEngine
import logging
import yaml
import logging.config
logging_config = os.path.join(sys.prefix, '.curs', 'logging.yml')
if not os.path.isfile(logging_config):
    logging_config = os.path.join('config', 'logging.yml')

logging.config.dictConfig(yaml.load(open(logging_config, 'r')))

web_logging = logging.getLogger('curs')
mongo_logging = logging.getLogger('curs.mongo')
# web_logging = logging.getLogger(__name__)

# web_logging.setLevel(logging.DEBUG)
# log_format = logging.Formatter('{asctime} {levelname:5s} {filename} LINE: {lineno} {message}', style='{')
# root_handler = logging.StreamHandler()
# root_handler.setFormatter(log_format)
# web_logging.addHandler(root_handler)


app = Flask(__name__)
app.config.from_object('app.default_config')
try:
    app.config.from_envvar('env_config')
except RuntimeError:
    print('no environment config, default used')
# db = MongoEngine(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


from app import views

if __name__ == "__main__":
    app.run()

