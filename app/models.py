# -*- coding: utf-8 -*-
import datetime

from app import db
from flask import url_for


# class Records(db.Document):
#         bid = db.StringField(required=True)
#         phone = db.StringField(max_length=30, required=True)
#         location = db.StringField(required=True)
#         time = db.DateTimeField(default=datetime.datetime.now, required=True)
#         time_update = db.DateTimeField(default=datetime.datetime.now, required=True)
#         operation = db.StringField(max_length=3, required=True)
#         ammount = db.StringField(required=True)
#         rate = db.FloatField(required=True)
#         comment = db.StringField(required=True)
#         d = db.BooleanField(required=False)
#         sid = db.IntField(required=False)
#         currency = db.StringField(max_length=3, required=True)
#         source = db.StringField(max_length=1, required=True)
#         pr = db.BooleanField(required=False)
#         uid = db.StringField(required=False)
#
#
#         def get_absolute_url(self):
#             return url_for('post', kwargs={"slug": self.slug})
#
#         def __unicode__(self):
#             return self.title
#
#         meta = {
#             'allow_inheritance': True,
#             'indexes': ['-created_at', 'slug'],
#             'ordering': ['-created_at']
#         }


class Post(db.Document):
        created_at = db.DateTimeField(default=datetime.datetime.now(), required=True)
        title = db.StringField(max_length=255, required=True)
        slug = db.StringField(max_length=255, required=True)
        body = db.StringField(required=True)
        # comments = db.ListField(db.EmbeddedDocumentField('Comment'))

        def get_absolute_url(self):
            return url_for('post', kwargs={"slug": self.slug})

        def __unicode__(self):
            return self.title

        meta = {
            'allow_inheritance': True,
            'indexes': ['-created_at', 'slug'],
            'ordering': ['-created_at']
        }
