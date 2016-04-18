

octothorpe = lambda x, dictionary: x * -1 if dictionary['nbu_auction']['operation'] == 'buy' else x
octothorpe2 = lambda doc: dict(doc, amount_accepted_all=doc['amount_accepted_all'] * -1,
                               amount_requested=doc['amount_requested'] * -1) \
                            if doc.get('nbu_auction_operation') == 'buy' else doc
def reformat_for_js(doc):
    if 'nbu_auction' in doc:
        doc['amount_requested'] = octothorpe(doc['nbu_auction'].pop('amount_requested'), doc)
        doc['amount_accepted_all'] = octothorpe(doc['nbu_auction'].pop('amount_accepted_all'), doc)
        del doc['nbu_auction']
    # doc['time'] = doc['time'].strftime('%Y-%m-%d_%H')
    return doc