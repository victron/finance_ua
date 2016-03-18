# https://habrahabr.ru/post/196810/
# http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iii-web-forms
# ---- mongo docs ----
# https://docs.mongodb.org/ecosystem/tutorial/write-a-tumblelog-application-with-flask-mongoengine/
# https://www.zharenkov.ru/post/write-a-tumblelog-application-with-flask-mongoenginev

from flask import Flask
from flask.ext.mongoengine import MongoEngine

app = Flask(__name__)
app.config.from_object('config')
db = MongoEngine(app)

from app import views

