import json
import logging

import falcon
import pymongo

from spiders.parallel import update_news, update_lists
from spiders.parameters import client, simple_rest_secret

logger = logging.getLogger()



def check_mongo(req, resp, resource, params):
    """
http GET localhost:9080/command
HTTP/1.1 503 Service Unavailable
content-length: 84
content-type: application/json; charset=UTF-8
vary: Accept

{
    "code": 15,
    "description": "DB down",
    "title": "Service Unavailable"
}

    :param req:
    :param resp:
    :param resource:
    :param params:
    :return:
    """
    logger.debug('def check_mongo: req.stream= {}'.format(req.stream))
    try:
        client.server_info()
    except pymongo.errors.ServerSelectionTimeoutError:
        msg = 'DB down'
        code = 15
        logger.error('{}, error code={}'.format(msg, code))
        raise falcon.HTTPServiceUnavailable('Service Unavailable', msg, code=code)


def validate_json_content(req, resp, resource, params):
    input_dict = req.content_type
    logger.debug('content_type = {}'.format(input_dict))
    # if req.content_type != 'application/json':
    logger.debug('def validate_json_content: req.stream= {}'.format(req.stream))
    try:
        if 'application/json' not in req.content_type:
            msg = 'not JSON'
            logger.info(msg)
            raise falcon.HTTPBadRequest('Bad request', msg)
    except:
        msg = 'not JSON'
        logger.info(msg)
        raise falcon.HTTPBadRequest('Bad request', msg)


def simple_authentication(doc: dict):
    """
    check secret in requests. In reason req.stream (wsgi.input) couldn't read twice,
    it's not posible to use in falcon.before
    :param doc:
    :return:
    """
    secret = {'secret': simple_rest_secret,
              'responce': ['ok', 'nok'],
              }
    logger.debug('simple_authentication >> doc = {}'.format(doc))
    for key, val in secret.items():
        if val != doc.get(key, None):
            msg = 'wrong secret, body= {}'.format(doc)
            logger.info(msg)
            raise falcon.HTTPBadRequest('Bad request', msg)
    return True


class Commands(object):
    @falcon.before(validate_json_content)
    # @falcon.before(simple_authentication)
    @falcon.before(check_mongo)
    def on_get(self, req, resp):
        """

[vic@dell ~]$ http -j GET localhost:9080/command secret=temp_secret  responce:='["ok", "nok"]'
HTTP/1.1 200 OK
content-length: 14
content-type: application/json; charset=UTF-8

{
    "answ": "ok"
}

        :param req:
        :param resp:
        :return:
        """
        logger.debug('on_get>>> request = {}'.format(req.stream))
        try:
            doc = json.load(req.stream)
        except json.JSONDecodeError:
            raise falcon.HTTPBadRequest('Bad request', 'JSONDecodeError')
        logger.debug('body= {}'.format(doc))

        if simple_authentication(doc):
            logger.debug('method == GET')
            logger.debug('content type == {}'.format(req.content_type))
            info = {'answ': 'ok'}
            resp.body = json.dumps(info)
            logger.debug('answer = {}'.format(info))
            resp.status = falcon.HTTP_200

    @falcon.before(validate_json_content)
    # @falcon.before(simple_authentication)
    @falcon.before(check_mongo)
    def on_post(self, req, resp):
        """
[vic@dell ~]$ http -j POST localhost:9080/command secret=temp_secret  responce:='["ok", "nok"]' update=news
HTTP/1.1 202 Accepted
content-length: 60
content-type: application/json; charset=UTF-8

{
    "duplicate_count": 22,
    "inserted_count": 170,
    "resp": "ok"
}

        :param req: content_type: application/json
        :param resp:
        :return:
        """
        update_allowed = {'news', 'lists'}

        logger.debug('on_post>>> request = {}'.format(req.stream))
        try:
            doc = json.load(req.stream)
        except json.JSONDecodeError:
            raise falcon.HTTPBadRequest('Bad request', 'JSONDecodeError')
        logger.debug('doc = {}'.format(doc))

        if simple_authentication(doc):
            update = doc.get('update')
            if update is None or update not in update_allowed:
                msg = 'wrong value in \"update\",  update= {}'.format(update)
                logger.info(msg)
                raise falcon.HTTPBadRequest('Bad request', msg)

            responce_ok = {'resp': 'ok'}
            responce = {'resp': 'Nok'}
            if update == 'news':
                logger.info('updating news')
                responce['inserted_count'], responce['duplicate_count'] = update_news()
                responce['update'] = 'news'

            if update == 'lists':
                logger.info('updating lists')
                responce['inserted_count'], responce['deleted_count'] = update_lists()
                responce['update'] = 'lists'

            responce.update(responce_ok)
            logger.debug('responce = {}'.format(responce))

            resp.body = json.dumps(responce)
            resp.status = falcon.HTTP_202
