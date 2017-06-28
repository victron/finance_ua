import json
from datetime import datetime, timedelta

import pymongo
from bson.objectid import ObjectId

from curs import web_logging
from flask import render_template, flash, redirect, url_for, abort, jsonify, request, make_response
from flask_login import login_user, logout_user, login_required
from curs import app, web_logging
from mongo_collector.mongo_start import data_active, numbers
from curs.forms_numbers import FilterNumbers, SaveNumber, Transaction, DeleteNumber


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
# def list_numbers(**kwargs):
    # hidden_filter = kwargs.get('hidden', {})
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
        # setattr(del_number, 'filters', HiddenField(default=form_filter.data, validators=[Optional()]))
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

    form_recieved = {'contact_type': form.contact_type.data, 'comment': form.comment.data, 'loc_comments': form.loc_comments.data,
                     'nic': form.nic.data, 'org_type': form.org_type.data, 'names': form.names.data,
                     'city': form.city.data, 'street': form.street.data, 'building': form.building.data,
                     'numbers': form.numbers.data}

    doc = dict(form_recieved)
    # form_recieved.update(hidden_filter)

    if form.validate_on_submit():
        web_logging.debug('request to save number')
        flash('nic= {nic}; contact_typ= {contact_type}; org_type= {org_type}; names= {names}; numbers= {numbers};'
              'comment= {comment};'
              'city= {city}; street= {street}, building={building}, loc_comments={loc_comments}'
              .format(nic=form_recieved['nic'], contact_type=form_recieved['contact_type'],
                      org_type=form_recieved['org_type'], names=form_recieved['names'],
                      numbers=form_recieved['numbers'], city=form_recieved['city'], street=form_recieved['street'],
                      building=form_recieved['building'], loc_comments=form_recieved['loc_comments'],
                      comment=form_recieved['comment']))
        create_time = {'create_time': datetime.now()}
        update_time = {'update_time': datetime.now()}
        doc.update(create_time)
        doc.update(update_time)

        doc['numbers'] = doc['numbers'].replace(' ', '')
        doc['numbers'] = doc['numbers'].split(',')
        doc['numbers'] = list(set(doc['numbers']))    # remove duplicates

        if doc.get('names') is not None:
            doc['names'] = doc['names'].split(',')
            doc['names'] = [field.strip() for field in doc['names']]
            doc['names'] = list(set(doc['names']))  # remove duplicates
        result = numbers.insert_one({key: val for key, val in doc.items() if val != ''}) # delete empty fields before insert
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
        form_recieved = dict(form.data)
        del form_recieved['csrf_token']
        form_recieved = {key: val for key, val in form_recieved.items() if val != ''}
        form_recieved['update_time'] = datetime.now()

        form_recieved['numbers'] = form_recieved['numbers'].replace(' ', '')
        form_recieved['numbers'] = form_recieved['numbers'].split(',')
        form_recieved['numbers'] = list(set(form_recieved['numbers']))

        if form_recieved.get('names') is not None:
            form_recieved['names'] = form_recieved['names'].split(',')
            form_recieved['names'] = [field.strip() for field in form_recieved['names']]
            form_recieved['names'] = list(set(form_recieved['names']))  # remove duplicates

        result = numbers.update_one({'_id': ObjectId(_id)}, {'$set': form_recieved})
        match_count, modified_count = result.matched_count, result.modified_count
        flash("match_count= {}, modified_count= {}".format(match_count, modified_count))
        return redirect(url_for('add_edit_number'))

    return render_template('save_contact.html', title=title, form=form)
