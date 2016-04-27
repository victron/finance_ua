from mongo_collector.mongo_start import aware_times

octothorpe = lambda x, dictionary: x * -1 if dictionary['nbu_auction']['operation'] == 'buy' else x
octothorpe2 = lambda doc: dict(doc, amount_accepted_all=doc['amount_accepted_all'] * -1,
                               amount_requested=doc['amount_requested'] * -1) \
                            if doc.get('nbu_auction_operation') == 'buy' else doc

def reformat_for_js_bonds(doc: dict) -> dict:
    # add in doc coupon pay
    if 'bonds' in doc:
        sum_amount = 0
        for bond in doc.pop('bonds'):
            bond_doc = aware_times(bond.collection).find_one({'_id': bond.id})
            sum_amount += bond_doc['amount'] / 100 * bond_doc['incomelevel']
        doc['sum_coupon'] = sum_amount
    return octothorpe2(doc)

def reformat_for_js(doc):
    if 'nbu_auction' in doc:
        doc['amount_requested'] = octothorpe(doc['nbu_auction'].pop('amount_requested'), doc)
        doc['amount_accepted_all'] = octothorpe(doc['nbu_auction'].pop('amount_accepted_all'), doc)
        del doc['nbu_auction']
    # doc['time'] = doc['time'].strftime('%Y-%m-%d_%H')
    return doc