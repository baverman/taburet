# -*- coding: utf-8 -*-
from datetime import datetime
from bson import Code, SON

from taburet.mongokit import Document, Field, Currency

class Transaction(Document):
    from_acc = Field([])
    to_acc = Field([])
    amount = Currency(0)
    date = Field(datetime.now)

    def save(self, do_reduce=True):
        Document.save(self)

        if do_reduce:
            Transaction.__collection__.map_reduce(transactions_balance_map, transactions_reduce,
                out=SON([("reduce", "%s.balance" % Transaction.__collection__.name)]),
                query={'_id':self.id})

            Transaction.__collection__.map_reduce(transactions_balances_map, transactions_reduce,
                out=SON([("reduce", "%s.balances" % Transaction.__collection__.name)]),
                query={'_id':self.id})

        return self

    def __repr__(self):
        return "<%s -> %s: %f at %s>" % (str(self.from_acc), str(self.to_acc),
            self.amount, self.date)


class Balance(object):
    def __init__(self, debet, kredit):
        self.debet = debet
        self.kredit = kredit
        self.balance = debet - kredit

    def __repr__(self):
        return "<+: %f  -: %f  =: %f>" % (self.debet, self.kredit, self.balance)


def month_report(account_id_list, dt=None):
    dt = dt or datetime.now()

    year, month = dt.year, dt.month
    view_name = 'month_report_%s' % dt.strftime('%Y%m')
    design_id = '_design/' + view_name

    if not Transaction.get_db().doc_exist(design_id):
        design_doc = {'_id':design_id, 'language':'erlang', 'views':{'get':{
            'map': open(os.path.join(os.path.split(__file__)[0], 'month_report', 'map.erl')).read().decode('utf8') % {'year':year, 'month':month},
            'reduce': open(os.path.join(os.path.split(__file__)[0], 'month_report', 'reduce.erl')).read().decode('utf8'),
        }}}
        try:
            Transaction.get_db().save_doc(design_doc)
        except ResourceConflict:
            pass

    result = Transaction.get_db().view(view_name+'/get', keys=account_id_list, group=True)
    result = dict((r['key'], r['value']) for r in result)

    for id in account_id_list:
        if id not in result:
            result[id] = {'kredit': 0, 'debet': 0, 'after': 0, 'before': 0}

    return result

def balance(aid, date_from=None, date_to=None):
    '''
    Возвращает баланс счета

    @return: Balance
    '''

    if date_from is None and date_to is None:
        result = Transaction.__collection__.balance.find_one({'_id':aid})
        if result:
            result = result['value']
    else:
        query = {'_id.acc': aid, '_id.dt':{}}
        if date_from:
            query['_id.dt']['$gte'] = date_from

        if date_to:
            query['_id.dt']['$lt'] = date_to

        result = Transaction.__collection__.balances.group(['_id.acc'], query,
            {'kredit':0L, 'debet':0L},
            '''function(obj, prev) {
                  prev.kredit += obj.value.kredit
                  prev.debet += obj.value.debet
               }'''
        )

        if result:
            result = result[0]

    if result:
        return Balance(result['debet']/100.0, result['kredit']/100.0)
    else:
        return Balance(0, 0)


def balances(id_list):
    '''
    Возвращает балансы переданных счетов

    @return: list of Balance
    '''
    return dict((r['key'], Balance(r['value']['debet'], r['value']['kredit']))
        for r in Transaction.get_db().view('transactions/balance', keys=id_list, group=True))


def report(id, date_from=None, date_to=None, group_by_day=True):
    params = {'group':True, 'group_level':4}

    params['startkey'] = [id]
    params['endkey'] = [id, {}]

    if date_from:
        params['startkey'] = get_date_key(id, date_from)

    if date_to:
        params['endkey'] = get_date_key(id, date_to)

    result = Transaction.view('transactions/exact_balance_for_account', **params).all()

    return ((r['key'][1:], Balance(**r['value'])) for r in result)

def transactions(aid, date_from=None, date_to=None, income=False, outcome=False):
    query = {}

    if date_from:
        query.setdefault('date', {})['$gte'] = date_from

    if date_to:
        query.setdefault('date', {})['$lt'] = date_to

    if income and not outcome:
        query['to_acc'] = aid
    elif outcome and not income:
        query['from_acc'] = aid
    else:
        q = query['$or'] = []
        q.append({'from_acc':aid})
        q.append({'to_acc':aid})

    return Transaction.find(query)

def all_transactions(id, date_from=None, date_to=None):
    params = {'include_docs':True, 'reduce':False, 'descending':True}

    params['startkey'] = [id, {}]
    params['endkey'] = [id]

    if date_from:
        params['startkey'] = get_date_key(id, date_to)

    if date_to:
        params['endkey'] = get_date_key(id, date_from)

    return Transaction.view('transactions/balance_for_account', **params)


transactions_balances_map = Code("""
function(){
    var obj = this
    obj.from_acc.forEach(function(acc) {
        var dt = new Date(obj.date.getTime())
        dt.setUTCHours(0)
        dt.setUTCMinutes(0)
        dt.setUTCSeconds(0)
        dt.setUTCMilliseconds(0)
        emit({acc:acc, dt:dt}, {kredit:obj.amount, debet:0});
    })

    obj.to_acc.forEach(function(acc) {
        var dt = new Date(obj.date.getTime())
        dt.setUTCHours(0)
        dt.setUTCMinutes(0)
        dt.setUTCSeconds(0)
        dt.setUTCMilliseconds(0)
        emit({acc:acc, dt:dt}, {kredit:0, debet:obj.amount});
    })
}
""")

transactions_balance_map = Code("""
function(){
    var obj = this
    obj.from_acc.forEach(function(acc) {
        emit(acc, {kredit:obj.amount, debet:0});
    })

    obj.to_acc.forEach(function(acc) {
        emit(acc, {kredit:0, debet:obj.amount});
    })
}
""")

transactions_reduce = Code("""
function(key, values){
    var result = {kredit:0, debet:0}
    values.forEach(function(v) {
        result.kredit += v.kredit
        result.debet += v.debet
    })
    return result
}
""")
