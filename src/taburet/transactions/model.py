# -*- coding: utf-8 -*-
from couchdbkit import Document, ListProperty, FloatProperty, ResourceNotFound, ResourceConflict
from taburet.cdbkit import DateTimeProperty 

from datetime import datetime

import os.path

class Transaction(Document):
    NotFound = ResourceNotFound
    
    from_acc = ListProperty(verbose_name="From accounts", required=True)
    to_acc = ListProperty(verbose_name="To accounts", required=True)
    amount = FloatProperty(default=0.0)
    date = DateTimeProperty(default=datetime.now, required=True)

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
