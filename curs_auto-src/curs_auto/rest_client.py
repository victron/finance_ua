import requests
import logging

logger = logging.getLogger('curs_auto')
# logging.basicConfig(level=logging.DEBUG)
simple_rest_secret = 'temp_secret'
req_template = {'secret': simple_rest_secret,
              'responce': ['ok', 'nok'],
              }
update_allowed = {'news', 'lists', 'commodities'}
url = 'http://localhost:9080/command'


def update(object: str) -> dict :
    logger.debug('update arg= {}'.format(object))
    if object not in update_allowed:
        msg = 'not allowed update ' + object
        logger.error(msg)
        return {'msg': msg, 'responce': req_template['responce'][1]}
    logger.debug('request template= {}'.format(req_template))
    # payload = dict(req_template)
    payload = req_template.copy()
    payload.update({'update': object})
    logger.debug('send payload = {}'.format(payload))
    try:
        r = requests.post(url, json=payload)
    except requests.exceptions.ConnectionError as ConnectionErr:
        logger.error('tcp rst; {}'.format(ConnectionErr))
        resp = {'msg': str(ConnectionErr)}
    except Exception as any_exception:
        logger.error('requests return unfixed error; {}'.format(any_exception))
        resp = {'msg': str(any_exception)}
    else:
        resp = r.json()
    finally:
        result = {'request': payload,
                  'responce': resp}
        logger.info('request result= {}'.format(result))
        return result


def update_dict(doc: dict) -> dict:
    logger.debug('update arg= {}'.format(doc))
    if doc['update'] not in update_allowed:
        msg = 'not allowed update ' + doc
        logger.error(msg)
        return {'msg': msg, 'responce': req_template['responce'][1]}
    logger.debug('request template= {}'.format(req_template))
    # payload = dict(req_template)
    payload = req_template.copy()
    payload.update(doc)
    logger.debug('send payload = {}'.format(payload))
    try:
        r = requests.post(url, json=payload)
    except requests.exceptions.ConnectionError as ConnectionErr:
        logger.error('tcp rst; {}'.format(ConnectionErr))
        resp = {'msg': str(ConnectionErr)}
    except Exception as any_exception:
        logger.error('requests return unfixed error; {}'.format(any_exception))
        resp = {'msg': str(any_exception)}
    else:
        resp = r.json()
    finally:
        result = {'request': payload,
                  'responce': resp}
        logger.info('request result= {}'.format(result))
        return result
