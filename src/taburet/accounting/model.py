# -*- coding: utf-8 -*-

from couchdbkit import Document, ListProperty, FloatProperty, StringProperty
from taburet.couchdbkit import DateTimeProperty 

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
    title = StringProperty()
    parents = ListProperty()
    
    def _get_date_key(self, date):
        return [self._id, date.year, date.month, date.day]
    
    def balance(self, date_from=None, date_to=None):
        '''
        Возвращает баланс счета
        
        @return: Balance
        '''
        
        if date_from is None and date_to is None:
            result = Transaction.view('accounting/balance', key=self._id).one()['value']
        else:
            params = {}
            if date_from:
                params['startkey'] = self._get_date_key(date_from)
            
            if date_to:
                params['endkey'] = self._get_date_key(date_to)
                
            result = Transaction.view('accounting/balance_for_account', **params).one()['value']
        
        return Balance(result['debet'], result['kredit'])
    
    def subaccounts(self):
        return Account.view('accounting/accounts', key=self._id, include_docs=True).all()
    
    def transactions(self, date_from=None, date_to=None):
        params = {'include_docs':True}
        if date_from is None and date_to is None:
            params['startkey'] = [self._id]
            params['endkey'] = [self._id, {}]
        else:
            if date_from:
                params['startkey'] = self._get_date_key(date_from)
            
            if date_to:
                params['endkey'] = self._get_date_key(date_to)
                
        return Transaction.view('accounting/transactions', **params)
    
    def __repr__(self):
        return "<Account: %s" % self._id
    
    def __eq__(self, ob):
        return self._id == ob._id


class Balance(object):
    def __init__(self, debet, kredit):
        self.debet = debet
        self.kredit = kredit
        self.balance = debet - kredit

    
class AccountsPlan(object):
    def __init__(self):
        pass
    
    def add_account(self, id, title=None, parent=None):
        '''
        Добавляет счет в план
        
        @param id: уникальный для базы id
        @param title: расшифровка
        @param parent: счет, в который будет помещен создаваемый субсчет
        @return: Account
        '''
        account = Account()
        account._id = id
        
        if title:
            account.title = title
            
        if parent:
            account.parents = parent.parents + [parent._id]
        
        account.save()

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