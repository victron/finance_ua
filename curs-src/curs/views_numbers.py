import json
from datetime import datetime, timedelta, timezone

import pymongo
from bson.objectid import ObjectId

from curs import web_logging
from flask import render_template, flash, redirect, url_for, abort, jsonify, request, make_response
from flask_login import login_user, logout_user, login_required
from curs import app, web_logging
from mongo_collector.mongo_start import data_active, numbers, contracts
from curs.forms_numbers import FilterNumbers, SaveNumber, Transaction, DeleteNumber, Contracts, DeleteContract, \
    SaveContract
from spiders.common_spider import kyiv_tz


class Contract:
    def __init__(self):
        self._mandatory = {'contract_time': datetime, 'contract_rate': float, 'contract_currency': str,
                           'contract_amount': int, 'contract_phones': list}
        self._optional = {'done_time': datetime, 'contract_comments': str}
        self.contract_time: datetime = None
        self.contract_rate: float = None
        self.contract_currency: str = None
        self.contract_amount: int = None
        self.contract_phones: list = None
        self.done_time: datetime = None
        self.contract_comments: str = None

    def from_form(self, in_doc: dict):
        for key in self._mandatory:
            try:
                setattr(self, key, in_doc[key])
            except KeyError as e:
                setattr(self, key, None)
        for key in self._optional:
            if in_doc.get(key) not in ('', 'None', None):
                setattr(self, key, in_doc[key])

        # specific keys handling
        # add tz to naive datetime
        all_attrs = {**self._mandatory, **self._optional}
        for key in [i for i in all_attrs if all_attrs[i] == datetime]:
            if getattr(self, key, None) is not None:
                try:
                    # expected recive naive time in Kyiv tz
                    setattr(self, key, kyiv_tz.localize(self.__dict__[key]))
                except ValueError:
                    # Not naive datetime (tzinfo is already set)
                    setattr(self, key, self.__dict__[key].astimezone(kyiv_tz))

        # convert string to list
        for key in [i for i in all_attrs if all_attrs[i] == list]:
            if getattr(self, key, None) is not None:
                setattr(self, key, self.__dict__[key].replace(' ', '').split(','))
                setattr(self, key, list(set(self.__dict__[key])))

        return {key: val for key, val in self.__dict__.items()
                if not key.startswith('_') and val is not None and val != ''}

    def to_form(self, in_doc: dict):
        for key in in_doc:
            setattr(self, key, in_doc[key])
        doc: dict = {key: val for key, val in self.__dict__.items() if not key.startswith('_') and val is not None}

        # specific keys handling
        # convert into local tz
        all_attrs = {**self._mandatory, **self._optional}
        for key in [key for key, val in all_attrs.items() if val == datetime]:
            if doc.get(key) is not None:
                doc[key] = doc[key].astimezone(kyiv_tz)

        # convert list to string
        doc['contract_phones'] = ', '.join(doc['contract_phones'])

        return doc

    def from_lists(self, doc: dict):
        self.contract_currency = doc['currency']
        self.contract_rate = doc['rate']
        self.contract_phones = doc['phone']
        self.contract_time = kyiv_tz.localize(datetime.now())
        self.contract_comments = doc['comment']

        return self.as_dict()

    def as_dict(self):
        return {key: val for key, val in self.__dict__.items()
                if not key.startswith('_') and val is not None and val != ''}


class Contact(Contract):
    def __init__(self):
        self._mandatory = {'contact_type': str, 'nic': str, 'org_type': str, 'numbers': list, 'create_time': datetime,
                           'update_time': datetime}
        self._optional = {'comment': str, 'loc_comments': str, 'names': list, 'city': str, 'street': str,
                          'building': str, 'contact_id': str}
        self.contact_type, self.nic, self.org_type = None, None, None
        self.numbers: list = None
        self.create_time: datetime = None
        self.update_time: datetime = None
        self.comment, self.loc_comments = None, None
        self.names: list = None
        self.city: str = u'Киев'
        self.street, self.building = None, None
        self.contact_id: ObjectId = None



def mongo_request(original: dict) -> dict:
    """
    help function for sort forms, prepare dict for mongo
    :param original:
    :return:
    """
    mongo_dict = dict(original)
    for key, val in original.items():
        if (val == 'None' or val == 'all' or val == '' or val is None) and not key.startswith('$'):
            del mongo_dict[key]
        elif key.startswith('$') and (val == {'$search': ''} or val == {'$search': None}):
            del mongo_dict[key]
        elif type(val) == dict:
            if '$eq' in val:
                if val['$eq'] is None or val['$eq'] == '' or val['$eq'] == 'None':
                    del mongo_dict[key]
    return mongo_dict

@app.route('/numbers', methods=['GET', 'POST'])
@login_required
def add_edit_number():
    # TODO: correct sorting
    # ---------- initial settings for GET
    title = 'Numbers'
    form_filter = FilterNumbers()
    del_number = DeleteNumber()
    # ===================================
    filter_mongo_req = {'contact_type': form_filter.contact_type.data,
                        #  for serch more then one number, need correction in mongo_request function
                        # 'number': {'$in': [form_filter.number.data.split(',')]},
                        'numbers': {'$eq': form_filter.number.data},
                        '$text': {'$search': form_filter.comment.data}}
    # filter_recieved.update(hidden_filter)
    direction_dict = {'ASCENDING': pymongo.ASCENDING, 'DESCENDING': pymongo.DESCENDING}
    sort_mongo = [(group_order.form.sort_field.data, direction_dict[group_order.form.sort_direction.data])
                  for group_order in form_filter.sort_order if group_order.form.sort_field.data != 'None']

    if del_number.delete.data and del_number.validate_on_submit():
        # don't forget about csrf - validate_on_submit not working without it
        web_logging.debug('pushed delete number id= {}'.format(del_number.record_id.data))
        del_mongo_req = {'_id': ObjectId(del_number.record_id.data)}
        flash('saved filter= {}'.format(del_number.filters.data))

        deleted_count = 0
        deleted_count = numbers.delete_one(del_mongo_req).deleted_count
        flash('deleleted id= {}, count= {}'.format(del_mongo_req, deleted_count))

        # put saved in del_number form value into form_filter
        for key, val in json.loads(del_number.filters.data).items():
            if key == 'sort_order':
                sort_mongo = [(group_order['sort_field'], direction_dict[group_order['sort_direction']])
                             for group_order in val if group_order != 'None']
                # put sort_field values into form_filter
                for index, sort_field in enumerate(val):
                    for k, v in sort_field.items():
                        getattr(form_filter.sort_order[index], k).data = v
                continue
            if key == 'csrf_token':
                # ignore csrf_token inside form_filter object
                continue
            getattr(form_filter, key).data = val

        filter_mongo_req = {'contact_type': form_filter.contact_type.data,
                            'numbers': {'$eq': form_filter.number.data},
                            '$text': {'$search': form_filter.comment.data}}
        result = numbers.find(mongo_request(filter_mongo_req), sort=sort_mongo)
    elif form_filter.filter.data and form_filter.validate_on_submit():
        web_logging.debug('filter pushed')
        flash('filter: number={number}, contact_typ={contact_type}, text={comment}'
              .format(number=filter_mongo_req['numbers'],
                      contact_type=filter_mongo_req['contact_type'],
                      comment=filter_mongo_req['$text']))
        flash('Sort: {sort_list}'.format(sort_list=sort_mongo))
        flash('filter_received={}'.format(filter_mongo_req))
        flash('find req= {}'.format(mongo_request(filter_mongo_req)))
        del_number.filters.data = json.dumps(form_filter.data)
        result = numbers.find(mongo_request(filter_mongo_req), sort=sort_mongo)
    else:
        del_number.filters.data = json.dumps(form_filter.data)
        result = numbers.find(mongo_request(filter_mongo_req), sort=(('time', pymongo.DESCENDING),))
    flash('found count={}'.format(result.count()))
    return render_template('numbers.html', title=title, form_filter=form_filter, result=result,
                           form_del_number=del_number)


@app.route('/save_contact', methods=['GET', 'POST'])
@login_required
def save_contact():
    # hidden_filter = kwargs.get('hidden', {})
    title = 'Save contacts'
    form = SaveNumber()

    form_recieved = Contact()
    form_recieved.from_form(form.data)

    if form.validate_on_submit():
        web_logging.debug('request to save number')
        flash('nic= {nic}; contact_typ= {contact_type}; org_type= {org_type}; names= {names}; numbers= {numbers};'
              'comment= {comment};'
              'city= {city}; street= {street}, building={building}, loc_comments={loc_comments}'
              .format(nic=form_recieved.nic, contact_type=form_recieved.contact_type,
                      org_type=form_recieved.org_type, names=form_recieved.names,
                      numbers=form_recieved.numbers, city=form_recieved.city, street=form_recieved.street,
                      building=form_recieved.building, loc_comments=form_recieved.loc_comments,
                      comment=form_recieved.comment))
        form_recieved.create_time = datetime.utcnow()
        form_recieved.update_time = form_recieved.create_time

        result = numbers.insert_one(form_recieved.as_dict())
        flash('_id= {}'.format(result))
        # return list_numbers()
        return redirect(url_for('add_edit_number'))
    return render_template('save_contact.html', title=title, form=form)


@app.route('/edit_contact/<_id>', methods=['GET', 'POST'])
@login_required
def edit_contact(_id: str):
    """
    edit created early contact info
    :param _id: in DB
    :return:
    """
    # ------- GET ------------
    title = 'Edit contact -- ' + _id
    doc = numbers.find_one(ObjectId(_id), projection={'_id': False, 'create_time': False, 'update_time': False})
    # convert array in to string separated by coma
    doc = {key: (', '.join(val) if type(val) == list else val) for key, val in doc.items()}
    form = SaveNumber(**doc)
    # ========================

    if form.validate_on_submit():
        web_logging.debug('request to edit _id= {}'.format(_id))
        # prepare for mongo
        form_recieved = Contact()
        form_recieved.from_form(form.data)
        form_recieved.update_time = datetime.utcnow()

        result = numbers.update_one({'_id': ObjectId(_id)}, {'$set': form_recieved.as_dict()})
        match_count, modified_count = result.matched_count, result.modified_count
        flash("match_count= {}, modified_count= {}".format(match_count, modified_count))
        return redirect(url_for('add_edit_number'))

    return render_template('save_contact.html', title=title, form=form)


@app.route('/save_contract/<bid>', methods=['GET', 'POST'])
@login_required
def save_contract(bid):
    title = 'Create contract -- ' + bid
    doc = data_active.find_one({'bid': bid})
    if doc is None:
        # error exit from function
        web_logging.error('bid= {} not found in "data_active"'.format(bid))
        flash('bid= {} not found in "data_active"'.format(bid))
        return redirect(url_for('lists'))

    # take only 10 chars as number
    doc['phone'] = doc['phone'].replace('-', '')
    doc['phone'] = doc['phone'][len(doc['phone'])-10:]

    search_number = numbers.find_one({'numbers': {'$eq': doc['phone']}})
    contract: dict = Contract().from_lists(doc)

    if search_number is None:
        # no contacts with such number, call create new contact form
        form_doc = {'city': doc['location'], 'numbers': doc['phone'], 'comment': doc['comment'],
                    'loc_comments': doc['comment']}
        info = '--------- New Contact ------------'
    else:
        form_doc = Contact().to_form(search_number)
        # form_doc = {'city': search_number['city'],
        #             'numbers': ', '.join(search_number['numbers']),
        #             'comment': search_number.get('comment', ''),
        #             'loc_comments': search_number.get('loc_comments', ''),
        #             'contact_type': search_number['contact_type'], 'nic': search_number['nic'],
        #             'org_type': search_number['org_type'], 'names': ', '.join(search_number.get('names', '')),
        #             'contact_id': search_number['_id']}

        info = '========= Contact already known, please check ======'

    form_doc.update(contract)
    web_logging.debug('data for form= {}'.format(form_doc))
    form = Transaction(**form_doc)

    if form.validate_on_submit():
        contact_info = Contact()
        contact_info.from_form(form.data)

        contract_info = Contract().from_form(form.data)

        if contact_info.contact_id is None:
            # contact is new
            contact_info.create_time = datetime.utcnow()
            contact_info.update_time = contact_info.create_time
            web_logging.debug('inserting contact_info= {}'.format(contact_info.as_dict()))
            web_logging.debug('inserting contract_info= {}'.format(contract_info))
            flash('inserting contact_info= {}, contract_info= {}'.format(contact_info.as_dict(), contract_info))
            result_contract = contracts.insert_one(contract_info)
            result_contact = numbers.insert_one(contact_info.as_dict())
            # add contact id into document
            result_contract_upd = contracts.update_one({'_id': ObjectId(result_contract.inserted_id)},
                                               {'$set': {'contact': ObjectId(result_contact.inserted_id)}})
            result_contact_upd = numbers.update_one({'_id': ObjectId(result_contact.inserted_id)},
                                                {'$addToSet': {'contracts': ObjectId(result_contract.inserted_id)}})
        else:
            # contact already exists
            contact_info.update_time = datetime.utcnow()
            web_logging.debug('inserting contact_info= {}'.format(contact_info.as_dict()))
            web_logging.debug('inserting contract_info= {}'.format(contract_info))
            flash('updating contact_info= {}, creating contract_info= {}'.format(contact_info.as_dict(), contract_info))
            contract_info['contact'] = [ObjectId(contact_info.contact_id)]
            result_contract = contracts.insert_one(contract_info)
            result_contact = numbers.update_one({'_id': ObjectId(contact_info.contact_id)},
                                                {'$addToSet': {'contracts': ObjectId(result_contract.inserted_id)}})

        return redirect('/contracts')

    return render_template('contract.html', title=title, form=form, info=info)


@app.route('/contracts', methods=['GET', 'POST'])
@login_required
def list_contracts():
    """
    list and filter exists contract
    :return:
    """
    title = 'Contracts'
    # create empty filter and sorting
    mongo_filter = {}
    sort_mongo = []
    # ===============================
    form = Contracts()
    delete_contract = DeleteContract()

    if delete_contract.delete.data and delete_contract.validate_on_submit():
        web_logging.debug('pushed delete contract id= {}'.format(delete_contract.record_id.data))
        del_mongo_req = {'_id': ObjectId(delete_contract.record_id.data)}

        # deleted_count = 0
        deleted_count = contracts.delete_one(del_mongo_req).deleted_count
        flash('deleleted id= {}, count= {}'.format(del_mongo_req, deleted_count))

    elif form.validate_on_submit() or request.method == 'GET':
        form_copy = dict(form.data)
        del form_copy['csrf_token']
        del form_copy['filter']
        sort_options = form_copy.pop('sort_field'), form_copy.pop('sort_direction')
        # sorting
        direction_dict = {'ASCENDING': pymongo.ASCENDING, 'DESCENDING': pymongo.DESCENDING}
        if sort_options[0] is not None:
            sort_mongo = [(sort_options[0], direction_dict[sort_options[1]])]

        patern = {'contract_time_low': lambda val: {"contract_time": {'$gte': val.astimezone(timezone.utc)}},
                  'contract_time_high': lambda val: {"contract_time": {'$lte': val.astimezone(timezone.utc)}},
                  'contract_rate': lambda val: {'contract_rate': val},
                  'contract_currency': lambda val: {'contract_currency': val},
                  'contract_amount': lambda val: {'contract_amount': val},
                  # remove spaces and create list fom string, separetor == ','
                  'contract_phones': lambda val: {'contract_phones': val.replace(' ', '').split(',')},
                  'finished': lambda val: {'done_time': {'$exists': val}},
                  'done_time': lambda val: {'done_time': {'$gte': val.astimezone(timezone.utc)}},
                  'contract_comments': lambda val: {'$text': {'$search': val}},
                  }
        form_received = {key: val for key, val in form_copy.items() if val != '' and val is not None and val != 'None'}
        for key, val in form_received.items():
            # create $and key for filtering time period
            if key == 'contract_time_low' or key == 'contract_time_high':
                mongo_filter.update({'$and': [patern[key](val)]
                                    if mongo_filter.get('$and') is None
                                    else mongo_filter.get('$and') + [(patern[key](val))]})
                continue
            mongo_filter.update(patern[key](val))
        web_logging.debug('mongo_filter= {}'.format(mongo_filter))

    # create list according to previos if
    web_logging.debug('mongo_filter= {}'.format(mongo_filter))
    docs = contracts.find(mongo_filter, sort=sort_mongo)
    return render_template('contracts.html', title=title, docs=docs, form=form, delete_contract=delete_contract)


@app.route('/create_contract/<_id>', methods=['GET', 'POST'])
@login_required
def create_contract(_id='new'):
    """
    create new contract or edit existing
    :param _id:
    :return:
    """
    # if request.method == 'GET':
    if _id == 'new':
        # create new contract
        title = 'Create contract manualy'
        form = SaveContract()
    else:
        # edit contract
        title = 'Edit contract -- ' + _id
        doc = contracts.find_one({'_id': ObjectId(_id)})
        if doc is None:
            web_logging.error('cotract not found, _id= {}'.format(_id))
            flash('cotract not found, _id= {}'.format(_id))
            return redirect(url_for('list_contracts'))

        contract = Contract()
        contract.done_time = kyiv_tz.localize(datetime.now())
        form = SaveContract(**contract.to_form(doc))

    if request.method == 'POST':
        if form.validate_on_submit():
            form_received: dict = Contract().from_form(form.data)
            if _id == 'new':
                result = contracts.insert_one(form_received)
                flash("inserted doc={}, _id={}".format(form_received, result.inserted_id))
            else:
                result = contracts.update_one({'_id': ObjectId(_id)}, {'$set': form_received})
                flash("modified_count= {}, updated doc= {}, ".format(result.modified_count, form_received))

            return redirect(url_for('list_contracts'))

    return render_template('create_edit_contract.html', title=title, form=form)

