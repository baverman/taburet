# -*- coding: utf-8 -*-

from .model import Transaction, Balance

set_db = [Transaction]

def get_date_key(id, date):
    return [id, date.year, date.month, date.day]

def balance(id, date_from=None, date_to=None):
    '''
    Возвращает баланс счета
    
    @return: Balance
    '''
    
    if date_from is None and date_to is None:
        result = Transaction.view('transactions/balance', key=id).one()
    else:
        params = {}
        if date_from:
            params['startkey'] = get_date_key(id, date_from)
        
        if date_to:
            params['endkey'] = get_date_key(id, date_to)
            
        result = Transaction.view('transactions/balance_for_account', **params).one()
        
    if result:
        result = result['value']
        return Balance(result['debet'], result['kredit'])
    else:
        return Balance(0, 0)        

def report(id, date_from=None, date_to=None, group_by_day=True):
    params = {'group':True, 'group_level':4}
    
    if date_from is None and date_to is None:
        params['startkey'] = [id]
        params['endkey'] = [id, {}]
    else:
        if date_from:
            params['startkey'] = get_date_key(id, date_from)
        
        if date_to:
            params['endkey'] = get_date_key(id, date_to)
    
    result = Transaction.view('transactions/exact_balance_for_account', **params).all()
    
    return ((r['key'][1:], Balance(**r['value'])) for r in result)
    
def transactions(id, date_from=None, date_to=None, income=False, outcome=False):
    params = {'include_docs':True}
    
    type = 3
    if income:
        type = 1
    
    if outcome:
        type = 2
    
    if date_from is None and date_to is None:
        params['startkey'] = [type, id]
        params['endkey'] = [type, id, {}]
    else:
        if date_from:
            params['startkey'] = [type] + get_date_key(id, date_from)
        
        if date_to:
            params['endkey'] = [type] + get_date_key(id, date_to)
            
    return Transaction.view('transactions/transactions', **params)