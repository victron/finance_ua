import logging
from collections import namedtuple
from datetime import datetime, timedelta

from curs_auto.mongo_worker.mongo_update import mongo_insert_history

from curs_auto.mongo_worker.mongo_start import DATABASE
from curs_auto.mongo_worker.mongo_start import bonds_auction, bonds_payments, bonds
from curs_auto.spiders_legacy.external_bonds import external_bonds
from curs_auto.spiders_legacy.nbu import NbuJson

logger = logging.getLogger('curs.mongo_collector.bonds')

def colection_meta(collection, time_delta: timedelta = timedelta(hours=3),
                   default_date: datetime =datetime(year=2008, month=9, day=29)) -> namedtuple:
    """
    in collection there is some meta info in document with _id == 'update'
    {'_id': 'update',
     'update_time': datetime,   # time of last check to external source
     'insert_time': datetime,   # time of last insert in collection
      }
    :param collection:
    :param time_delta:
    :param default_date:
    :return:
    """
    current_time = datetime.now()
    collection_info = collection.find_one({'_id': 'update'})
    result = namedtuple('result', ['actual', 'update_time', 'insert_time', 'current_time'])
    if collection_info is not None:
        last_update_time = collection_info.get('update_time', default_date)
        if current_time < last_update_time - time_delta:
            logger.debug('collection {} in actual state, last update on = {}'.format(collection.name, last_update_time))
            return result(True, collection_info.get('update_time', default_date),
                          collection_info.get('insert_time', default_date), current_time)
        else:
            logger.info('{} last update on = {}'.format(collection.name, last_update_time))
            return result(False, collection_info.get('update_time', default_date),
                          collection_info.get('insert_time', default_date), current_time)
    else:
        logger.info('{} last update,  = Unknown'.format(collection.name))
        return result(False, default_date, default_date, current_time)


def bonds_summary(auction_result: dict):
    """
    based on auction data update number of active bonds
    :param auction_result: auction result on bond
    income fields:
'stockrestrict' Обмеження на обсяг розміщення облігацій (шт.)
'stockrestrictn'  У т.ч. за неконкурентними заявками (шт.)
'amount'  Кількість проданих облігацій (шт.)
'amountn' У т.ч. за неконкурентними заявками (шт.)
'auctiondate' Дата розміщення облігацій
'paydate' Дата оплати за придбані облігації
'repaydate' Термін погашення облігацій
'incomelevel' Граничний рівень дохідності облігацій (%)
'avglevel'  Середньозважений рівень дохідності облігацій (%)
'attraction'  Залучено коштів від розміщення облігацій (грн.)
    :return:
    """
    def guess_nominal_cost(amount, attraction, bond_code, bond_date):
        low_k = 0.4
        hight_k = 2.0
        nominal = 1000
        try:
            avarage_cost = attraction / amount
        except ZeroDivisionError:
            return nominal
        if (avarage_cost * low_k < nominal) and (avarage_cost * hight_k > nominal):
            return nominal
        else:
            logger.info('problem with nominal value {} on {}'.format(bond_code, bond_date))
            return avarage_cost

    current_time = datetime.now()
    collection = DATABASE['bonds']
    document = dict(auction_result)
    currency = document.pop('valcode').upper()
    document['currency'] = currency
    auctiondate = document.pop('auctiondate')
    auctionnum= document.pop('auctionnum')
    paydate = document.pop('paydate')
    document.pop('stockrestrict')
    document.pop('stockrestrictn')
    document['nominal'] = guess_nominal_cost(document['amount'], document['attraction'],
                                             document['_id'], auctiondate)
    # bond_code = document.pop('_id').strip()
    bond_code = document['stockcode']
    del document['stockcode']
    exist_document = collection.find_one({'_id': bond_code})
    if exist_document:
        # in case bond in db
        if auctiondate not in exist_document['auction_dates']:
            # set incomelevel as max from all auctions
            # reason - there are no data about nominal incomelevel in json from NBU
            if exist_document['incomelevel'] > document['incomelevel']:
                document.pop('incomelevel')

            document['amount'] += exist_document['amount']
            document['amountn'] += exist_document['amountn']
            document['attraction'] += exist_document['attraction']
            del document['_id']
            collection.update_one({'_id': bond_code}, {'$set': document})
            # workaround
            bond_update = collection.update_one({'_id': bond_code}, {'$push': {'auction_dates': auctiondate,
                                                                                'auctionnums': auctionnum,
                                                                                'paydates': paydate}})
        else:
            logger.debug('nothing to update, date= {}, bond= {}'.format(auctiondate, bond_code))
            logger.debug('document = {}'.format(document))
            return None

    else:
        # workaround
        # currently I don't know reason why it's not posible to inser or update document with array in field
        del document['_id']
        collection.update_one({'_id': bond_code}, {'$set': document}, upsert=True)
        bond_update = collection.update_one({'_id': bond_code}, {'$push': {'auction_dates': auctiondate,
                                                                            'auctionnums': auctionnum,
                                                                            'paydates': paydate}})
        # collection.update_one({'_id': bond_code}, {'$push': {'auctionnums': auctionnum}})
        # collection.update_one({'_id': bond_code}, {'$push': {'paydates': paydate}})
    return bond_update.modified_count


def bonds_match(collection_to_update, field, time_frame: timedelta = timedelta(days=3)):
    collection_to_update_state = colection_meta(collection_to_update)
    bonds_auction_state = colection_meta(bonds_auction)
    result = namedtuple('result', ['update', 'match'])
    match_exclude = {'_id': {'$ne': 'update'}}
    try:
        field_state = collection_to_update.find_one({'_id': 'update'})
        field_state = field_state[field]
    except:
        match_bonds_auction = {}
        logger.debug('updated "bonds_payments" ALL PERIODS')
        match_bonds_auction.update(match_exclude)
        result = result(True, match_bonds_auction)
        logger.debug('match={}'.format(result.match))
        return result
    if bonds_auction_state.insert_time > field_state:
        start_date = bonds_auction_state.insert_time - time_frame
        match_bonds_auction = {'paydate': {'$gte': start_date}}
        logger.debug('updated {} starting {}'.format(collection_to_update.name, start_date))
    elif bonds_auction_state.insert_time == field_state:
        # collection_meta return default value, need to update all
        match_bonds_auction = {}
        logger.debug('updated "bonds_payments" ALL PERIODS')
    elif bonds_auction_state.insert_time < field_state:
        logger.debug('"bonds_auction_state.insert_time"= {}, field_state= {}'
                     .format(bonds_auction_state.insert_time, field_state ))
        logger.debug('nothing to update in {}'.format(collection_to_update.name))
        return result(False, None)
    # exclude meta data from search
    logger.debug('match_bonds_auction= {}'.format(match_bonds_auction))
    match_bonds_auction.update(match_exclude)
    logger.debug('match_bonds_auction after exclude= {}'.format(match_bonds_auction))
    result = result(True, match_bonds_auction)
    logger.debug('match={}'.format(result.match))
    return result


def bonds_income():
    """
    based on auctions ('bonds_auction' collection), generate in 'collection_payments' documents
    about income (attraction)
    :return:
    """
    match = bonds_match(bonds_payments, 'income_update')
    logger.info('updating "incomes" in bonds_payments')
    if match.update:
        docs_income = []
        for doc in bonds_auction.find(match.match):
            doc_income = {}
            try:
                doc_income['bond'] = doc['stockcode']
            except KeyError:
                logger.debug('doc= {}'.format(doc))
                raise
            doc_income['time'] = doc['paydate']
            doc_income['currency'] = doc['valcode']
            doc_income['cash'] = doc['attraction']
            doc_income['auctionnum'] = doc['auctionnum']
            doc_income['pay_type'] = 'income'
            docs_income.append(doc_income)
        insert_result = mongo_insert_history(docs_income, bonds_payments)
        logger.debug('inserted in collection_payments = {}'.format(insert_result.inserted_count))
        logger.debug('duplicated in collection_payments = {}'.format(insert_result.duplicate_count))
        if insert_result.inserted_count > 0:
            current_time = datetime.now()
            bonds_payments.update_one({'_id': 'update'}, {'$set': {'income_update': current_time}}, upsert=True)
        return insert_result
    else:
        logger.info('no update for "incomes" in bonds_payments')


def internal_payments(in_doc: dict):
    """
    "amount": 4247000
    "nominal": 1000
    "repaydate": "9/28/11 2:00:00 PM UTC"
    "incomelevel": 17.0
    "attraction": 3.81558757E9
    "currency": "UAH"
    "_id": "UA3B00022509"
    "auction_dates" : [ { "$date" : "2008-09-29T14:00:00.000Z"} , { "$date" : "2008-10-06T14:00:00.000Z"} ,
    :param document:
    :return:
    """
    # currently ignore all bonds with field coupon_type
    if (in_doc['amount'] > 0) and (in_doc.get('coupon_type') is None):
        def calc_coupon_dates(open_date: datetime, close_date: datetime, period=0.5) -> set():
            """

            :param open_date: datetime: should be min date in auction dates
            :param close_date: datetime
            :param period: curently only 0.5
            :return: set of datetime oblects
            """
            pay_dates = set()
            pay_dates.add(close_date)
            if (close_date - open_date).days > 170:
                while close_date > open_date:
                    # calc month and year in half year
                    if period == 0.5:
                        pay_month = (close_date.month - 6) % 12
                    elif period == 1:
                        pay_month = (close_date.month - 12) % 12
                    if pay_month == 0:
                        pay_month = 1
                    if pay_month >= close_date.month:
                        pay_year = close_date.year - 1
                    else:
                        pay_year = close_date.year
                    # --- To set exists date ----
                    while True:
                        try:
                            pay_date = close_date.replace(month=pay_month, year=pay_year)
                        except ValueError:
                            close_date += timedelta(days=1)
                            continue
                        break
                    # --------------------------
                    if (pay_date - open_date).days > 150:
                        pay_dates.add(pay_date)
                        close_date = pay_date
                    else:
                        return pay_dates
            else:
                return pay_dates

        collection = DATABASE['bonds_payments']
        try:
            bond_open = min(in_doc['auction_dates'])
        except TypeError:
            logger.debug('in_doc= {}'.format(in_doc))
            raise
        bond_close = in_doc['repaydate']
        exist_return = collection.find_one({'bond': in_doc['_id'], 'time': bond_close, 'pay_type': 'return'})
        if exist_return is None:
        # calc and put in db return value
            doc = {}
            doc['bond'] = in_doc['_id']
            doc['time'] = bond_close
            doc['pay_type'] = 'return'
            doc['currency'] = in_doc['currency']
            doc['cash'] = in_doc['amount'] * in_doc['nominal']
            collection.insert_one(doc)
        for date in calc_coupon_dates(bond_open, bond_close):
        # calc and put in db coupon values, every half year
            exist_coupon = collection.find_one({'bond': in_doc['_id'], 'time': date, 'pay_type': 'coupon'})
            if exist_coupon is None:
                doc = {}
                doc['bond'] = in_doc['_id']
                doc['time'] = date
                doc['pay_type'] = 'coupon'
                doc['currency'] = in_doc['currency']
                try:
                    doc['cash'] = in_doc['amount'] * in_doc['nominal'] / 100 * in_doc['incomelevel']/2
                except ZeroDivisionError:
                    doc['cash'] = 0
                collection.insert_one(doc)


def manual_bonds_insert():
    external_update = mongo_insert_history(external_bonds, bonds)
    logger.debug('external bonds inserted= {} duplicated= {}'.format(external_update.inserted_count,
                                                                     external_update.duplicate_count))
    #  'insert_time' when new data was inserted
    if external_update.inserted_count > 0:
        current_time = datetime.now()
        bonds.update_one({'_id': 'update'}, {'$set': {'insert_time': current_time}}, upsert=True)
    return external_update


def update_auctions(nbu_ovdp):
    # nbu_ovdp = NbuJson().ovdp_all()
    auctions_update = mongo_insert_history(nbu_ovdp, bonds_auction)
    logger.debug('nbu_ovdp insertted {}'.format(auctions_update.inserted_count))
    # 'update_time' when db compared with NBU data and in actual state
    current_time = datetime.now()
    bonds_auction.update_one({'_id': 'update'}, {'$set': {'update_time': current_time}}, upsert=True)
    #  'insert_time' when new data was inserted
    if auctions_update.inserted_count > 0:
        bonds_auction.update_one({'_id': 'update'}, {'$set': {'insert_time': current_time}}, upsert=True)
    return auctions_update


def generate_bonds(match_bonds):
    modified_bonds = 0
    for doc in bonds_auction.find(match_bonds.match):
        bonds_summary(doc)
        modified_bonds += 1
    if modified_bonds > 0:
        current_time = datetime.now()
        bonds.update_one({'_id': 'update'}, {'$set': {'update_time': current_time}}, upsert=True)


def update_bonds(triger=False):
    """
    in bonds_auction present source data
    in bonds information per bond, generated for bonds_auction
    in bonds_payments payment information, generated by bonds_income from bonds_auction
    and internal_payments from bonds
    :param triger:
    :return:
    """
    if triger:
        # update information about bonds (check my info to external source)
        bonds_auction_state = colection_meta(bonds_auction)
        if not bonds_auction_state.actual:
            update_auctions(NbuJson().ovdp_all())
        # update income information
        income_result = bonds_income()

        manual_bonds_insert()

        match_bonds = bonds_match(bonds, 'update_time')
        if match_bonds.update:
            generate_bonds(match_bonds)

            # generate payments information
            for doc in bonds.find({'_id': {'$ne': 'update'}}):
                logger.debug('generate payments for={}'.format(doc['_id']))
                internal_payments(doc)
        else:
            logger.info('skip update "bonds" and "bonds_payments" collection, actual data')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    update_bonds(True)