# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from bson import Code, SON

from taburet.mongokit import Document, Field, Currency

GROUP_FUNC = ({'kredit':0L, 'debet':0L},
'''function(obj, prev) {
      prev.kredit += obj.value.kredit
      prev.debet += obj.value.debet
   }''')


def local_transaction_reducer(tid, revert_mp=1):
    Transaction.__collection__.map_reduce(transactions_balance_map, transactions_reduce,
        out=SON([("reduce", "%s.balance" % Transaction.__collection__.name)]),
        query={'_id':tid}, scope={'revert_mp':revert_mp})

    Transaction.__collection__.map_reduce(transactions_balances_map, transactions_reduce,
        out=SON([("reduce", "%s.balances" % Transaction.__collection__.name)]),
        query={'_id':tid}, scope={'revert_mp':revert_mp})


class Transaction(Document):
    from_acc = Field([])
    to_acc = Field([])
    amount = Currency(0)
    date = Field(datetime.now)
    canceled = Field(required=False)
    cancel_desc = Field(required=False)

    transaction_reducer = staticmethod(local_transaction_reducer)

    def save(self, do_reduce=True):
        if '_id' in self and do_reduce:
            Transaction.transaction_reducer(self.id, -1)

        Document.save(self)

        if do_reduce:
            Transaction.transaction_reducer(self.id)

        return self

    def cancel(self, desc=None):
        assert '_id' in self
        Transaction.transaction_reducer(self.id, -1)

        self.canceled = True
        if desc:
            self.cancel_desc = desc

        Document.save(self)

    def remove(self):
        assert '_id' in self
        Transaction.transaction_reducer(self.id, -1)
        Document.remove(self)

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

    dt_before = datetime(dt.year, dt.month, 1)
    dt_after = (dt_before + timedelta(days=32)).replace(day=1)

    rbefore = Transaction.__collection__.balances.group(['_id.acc'],
        {'_id.acc':{'$in':account_id_list}, '_id.dt':{'$lt':dt_before}}, *GROUP_FUNC)

    rafter = Transaction.__collection__.balances.group(['_id.acc'],
        {'_id.acc':{'$in':account_id_list}, '_id.dt':{'$gte':dt_before, '$lt':dt_after}},
        *GROUP_FUNC)

    result = {}
    for aid in account_id_list:
        result[aid] = {'kredit': 0, 'debet': 0, 'after': 0, 'before': 0}

    for r in rbefore:
        rr = result[int(r['_id.acc'])]
        rr['before'] = rr['after'] = (r['debet'] - r['kredit'])/100.0

    for r in rafter:
        rr = result[int(r['_id.acc'])]
        k, d = r['kredit']/100.0, r['debet']/100.0
        rr['debet'] = d
        rr['kredit'] = k
        rr['after'] = rr['before'] + d - k

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

        result = Transaction.__collection__.balances.group(['_id.acc'], query, *GROUP_FUNC)

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


def report(aid, date_from=None, date_to=None):
    query = {'_id.acc': aid}

    if date_from:
        query.setdefault('_id.dt', {})['$gte'] = date_from

    if date_to:
        query.setdefault('_id.dt', {})['$lt'] = date_to

    result = Transaction.__collection__.balances.group(['_id.acc', '_id.dt'], query,
        *GROUP_FUNC)

    return ((r['_id.dt'], Balance(r['debet']/100.0, r['kredit']/100.0)) for r in result)

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

transactions_balances_map = Code("""function(){
    var obj = this
    obj.from_acc.forEach(function(acc) {
        var dt = new Date(obj.date.getTime())
        dt.setUTCHours(0)
        dt.setUTCMinutes(0)
        dt.setUTCSeconds(0)
        dt.setUTCMilliseconds(0)
        emit({acc:acc, dt:dt}, {kredit:obj.amount * revert_mp, debet:0});
    })

    obj.to_acc.forEach(function(acc) {
        var dt = new Date(obj.date.getTime())
        dt.setUTCHours(0)
        dt.setUTCMinutes(0)
        dt.setUTCSeconds(0)
        dt.setUTCMilliseconds(0)
        emit({acc:acc, dt:dt}, {kredit:0, debet:obj.amount * revert_mp});
    })
}""")

transactions_balance_map = Code("""function(){
    var obj = this
    obj.from_acc.forEach(function(acc) {
        emit(acc, {kredit:obj.amount * revert_mp, debet:0});
    })

    obj.to_acc.forEach(function(acc) {
        emit(acc, {kredit:0, debet:obj.amount * revert_mp});
    })
}""")

transactions_reduce = Code("""function(key, values){
    var result = {kredit:0, debet:0}
    values.forEach(function(v) {
        result.kredit += v.kredit
        result.debet += v.debet
    })
    return result
}""")
