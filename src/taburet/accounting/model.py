# -*- coding: utf-8 -*-

from couchdbkit import Document, ListProperty, FloatProperty, StringProperty
from taburet.cdbkit import DateTimeProperty 
from taburet.counter import save_model_with_autoincremented_id

import datetime


class Transaction(Document):
    from_acc = ListProperty(verbose_name="From accounts", required=True)
    to_acc = ListProperty(verbose_name="To accounts", required=True)
    amount = FloatProperty(default=0.0)
    date = DateTimeProperty(default=datetime.datetime.now, required=True)

    def __repr__(self):
        return "<%s -> %s: %f at %s>" % (str(self.from_acc), str(self.to_acc),
            self.amount, self.date)


class Account(Document):
    name = StringProperty()
    parents = ListProperty()
    
    def _get_date_key(self, date):
        return [self._id, date.year, date.month, date.day]
    
    def balance(self, date_from=None, date_to=None):
        '''
        Возвращает баланс счета
        
        @return: Balance
        '''
        
        if date_from is None and date_to is None:
            result = Transaction.view('accounting/balance', key=self._id).one()
        else:
            params = {}
            if date_from:
                params['startkey'] = self._get_date_key(date_from)
            
            if date_to:
                params['endkey'] = self._get_date_key(date_to)
                
            result = Transaction.view('accounting/balance_for_account', **params).one()
            
        if result:
            result = result['value']
            return Balance(result['debet'], result['kredit'])
        else:
            return Balance(0, 0)        
    
    def report(self, date_from=None, date_to=None, group_by_day=True):
        params = {'group':True, 'group_level':4}
        
        if date_from is None and date_to is None:
            params['startkey'] = [self._id]
            params['endkey'] = [self._id, {}]
        else:
            if date_from:
                params['startkey'] = self._get_date_key(date_from)
            
            if date_to:
                params['endkey'] = self._get_date_key(date_to)
        
        result = Transaction.view('accounting/exact_balance_for_account', **params).all()
        
        return ((r['key'][1:], Balance(**r['value'])) for r in result)
    
    def subaccounts(self):
        return Account.view('accounting/accounts', key=self._id, include_docs=True).all()
    
    def transactions(self, date_from=None, date_to=None, income=False, outcome=False):
        params = {'include_docs':True}
        
        type = 3
        if income:
            type = 1
        
        if outcome:
            type = 2
        
        if date_from is None and date_to is None:
            params['startkey'] = [type, self._id]
            params['endkey'] = [type, self._id, {}]
        else:
            if date_from:
                params['startkey'] = [type] + self._get_date_key(date_from)
            
            if date_to:
                params['endkey'] = [type] + self._get_date_key(date_to)
                
        return Transaction.view('accounting/transactions', **params)
    
    def __repr__(self):
        return "<Account: %s>" % self._id
    
    def __eq__(self, ob):
        if ob:
            return self._id == ob._id
        else:
            return False


class Balance(object):
    def __init__(self, debet, kredit):
        self.debet = debet
        self.kredit = kredit
        self.balance = debet - kredit

    def __repr__(self):
        return "<+: %f  -: %f  =: %f>" % (self.debet, self.kredit, self.balance)

    
class AccountsPlan(object):
    def __init__(self):
        pass
    
    def add_account(self, name=None, parent=None):
        '''
        Добавляет счет в план
        
        @param id: уникальный для базы id
        @param title: расшифровка
        @param parent: счет, в который будет помещен создаваемый субсчет
        @return: Account
        '''
        account = Account()
        
        if name:
            account.name = name
            
        if parent:
            account.parents = parent.parents + [parent._id]
        
        save_model_with_autoincremented_id(account, 'acc')

        return account
    
    def create_transaction(self, from_account, to_account, amount, date=None):
        tran = Transaction()
        tran.from_acc = from_account.parents + [from_account._id]
        tran.to_acc = to_account.parents + [to_account._id]
        tran.amount = amount
        
        if date:
            tran.date = date
            
        return tran
    
    def accounts(self):
        return Account.view('accounting/accounts', key='ROOT_ACCOUNT', include_docs=True).all()
    
    def get_by_name(self, name):
        return Account.view('accounting/account_by_name', key=name, include_docs=True).one()
    
    def balance_report(self, date_from, date_to):
        pass