import json
import logging
from importlib import reload


import falcon
import pymongo

from spiders.parallel import update_news, update_lists
import spiders.parameters as parameters
from spiders.parameters import simple_rest_secret
from spiders.commodities.update_all import update_all
from spiders.main_currencies.google_fin import main_currencies_collect
from spiders.minfinua_contact import prepare_request, get_contacts
from spiders.simple_encrypt_import import secret
from spiders.minfinua_contact import return_contact

bid_to_payload = secret.bid_to_payload

logger = logging.getLogger(__name__)

UPDATE_ALLOWED = {'news', 'lists', 'commodities', 'main_currencies'}

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
        reload(parameters)
        parameters.client.server_info()
    except pymongo.errors.WriteError as e:
        logger.error('write error; check DB size; {}'.format(e))
        msg = 'DB write problem, check DB size'
        code = 14
        raise falcon.HTTPServiceUnavailable('Service Unavailable', msg, code=code)
    except Exception as e:
        msg = 'DB down; exception= {}'.format(e)
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
            logger.error('poblem to decoder; JSONDecodeError')
            raise falcon.HTTPBadRequest('Bad request', 'JSONDecodeError')
        logger.debug('body= {}'.format(doc))

        if simple_authentication(doc):
            logger.debug('method == GET')
            logger.debug('content type == {}'.format(req.content_type))
            info = {'answ': 'ok'}
            get_contact = doc.get('Mcontact')
            if get_contact is not None:
                # http  --timeout=40 -j GET http://localhost:9080/command secret=temp_secret  responce:='["ok", "nok"]'
                # Mcontact:='{"currency": "EUR", "operation": "sell", "bid": "35795343"}'
                if not {'currency', 'operation', 'bid'}.issubset(set(get_contact.keys())): #in req should present min fields
                    msg = 'request error; request {}'.format(get_contact)
                    logger.error(msg)
                    raise falcon.HTTPBadRequest('Bad request', msg)
                contact = return_contact(get_contact['bid'], get_contact['currency'],
                                         get_contact['operation'], get_contact.get('city', 'kiev'))
                doc_resp = {'contact': contact}
                # doc_resp = get_contacts(get_contact['bid'], bid_to_payload, prepare_request(get_contact))
                info.update(doc_resp)
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


        logger.debug('on_post>>> request = {}'.format(req.stream))
        try:
            doc = json.load(req.stream)
        except json.JSONDecodeError:
            raise falcon.HTTPBadRequest('Bad request', 'JSONDecodeError')
        logger.debug('doc = {}'.format(doc))

        if simple_authentication(doc):
            update = doc.get('update')
            if update is None or update not in UPDATE_ALLOWED:
                msg = 'wrong value in \"update\",  update= {}'.format(update)
                logger.info(msg)
                raise falcon.HTTPBadRequest('Bad request', msg)

            responce_ok = {'resp': 'ok'}
            responce = {'resp': 'Nok'}
            if update == 'news':
                logger.info('updating news')
                responce['inserted_count'], responce['duplicate_count'] = update_news()
                responce['update'] = 'news'

            elif update == 'lists':
                logger.info('updating lists')
                responce['inserted_count'], responce['deleted_count'] = update_lists()
                responce['update'] = 'lists'

            elif update == 'commodities':
                logger.info('updating commodities')
                try:
                    lists = doc['list']
                except KeyError as e:
                    msg = 'request error; list is empty {}'.format(e)
                    logger.error(msg)
                    raise falcon.HTTPBadRequest('Bad request', msg)
                except Exception as e:
                    msg = 'unknown error; error= {}'.format(e)
                    logger.error(msg)
                    raise falcon.HTTPBadRequest('Bad request', msg)

                try:
                    for k, v in update_all(lists).items():
                        responce[k] = str(v)        # convert nametuple in str, for more information in REST
                    responce['update'] = update
                except NameError as e:
                    msg = 'commodities: {} not in available list'.format(e)
                    logger.error(msg)
                    raise falcon.HTTPBadRequest('Bad request', msg)

            elif update == 'main_currencies':
                logger.info('updating {}'.format(update))
                try:
                    lists = doc['list']
                except KeyError as e:
                    msg = 'request error; list is empty {}'.format(e)
                    logger.error(msg)
                    raise falcon.HTTPBadRequest('Bad request', msg)
                except Exception as e:
                    msg = 'unknown error; error= {}'.format(e)
                    logger.error(msg)
                    raise falcon.HTTPBadRequest('Bad request', msg)

                try:
                    for k, v in main_currencies_collect(lists).items():
                        responce[k] = str(v)  # convert nametuple in str, for more information in REST
                    responce['update'] = update
                except NameError as e:
                    msg = 'main_currensies: {} not in available list'.format(e)
                    logger.error(msg)
                    raise falcon.HTTPBadRequest('Bad request', msg)

            responce.update(responce_ok)
            logger.debug('responce = {}'.format(responce))

            resp.body = json.dumps(responce)
            resp.status = falcon.HTTP_202
