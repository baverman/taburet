# -*- coding: utf-8 -*-

from couchdbkit import Document, ListProperty, StringProperty
from taburet.counter import save_model_with_autoincremented_id
from taburet.transactions import balance, report, transactions, Transaction

class Account(Document):
    name = StringProperty()
    parents = ListProperty()
    
    def balance(self, date_from=None, date_to=None):
        return balance(self._id, date_from, date_to)
    
    def report(self, date_from=None, date_to=None, group_by_day=True):
        return report(self._id, date_from, date_to, group_by_day)
    
    def subaccounts(self):
        return Account.view('accounts/accounts', key=self._id, include_docs=True).all()
    
    def transactions(self, date_from=None, date_to=None, income=False, outcome=False):
        return transactions(self._id, date_from, date_to, income, outcome)
    
    def __repr__(self):
        return "<Account: %s>" % self._id
    
    def __eq__(self, ob):
        if ob:
            return self._id == ob._id
        else:
            return False
        
    @property
    def id(self):
        return self._id

def accounts_walk(accounts):
    def get_accounts(parent, level):
        subaccounts = sorted(r for r in accounts if (not parent and not r.parents) or (r.parents and parent == r.parents[-1])) 
        for acc in subaccounts:
            yield level, acc
            for r in get_accounts(acc.id, level + 1):
                yield r
                
    return get_accounts(None, 0)

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
    
    def subaccounts(self):
        return Account.view('accounts/accounts', key='ROOT_ACCOUNT', include_docs=True).all()
    
    def accounts(self):
        return Account.view('doctype/get', key='Account', include_docs=True).all()
    
    def get_by_name(self, name):
        return Account.view('accounts/account_by_name', key=name, include_docs=True).one()
    
    def balance_report(self, date_from, date_to):
        pass