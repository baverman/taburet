# -*- coding: utf-8 -*-

from couchdbkit import Document, ListProperty, FloatProperty, DateTimeProperty, StringProperty
import datetime

class Transaction(Document):
    from_acc = ListProperty(verbose_name="From accounts", required=True)
    to_acc = ListProperty(verbose_name="To accounts", required=True)
    amount = FloatProperty(default=0.0)
    date = DateTimeProperty(default=datetime.datetime.utcnow, required=True)


class Account(Document):
    title = StringProperty()
    parents = ListProperty()
    
    def get_balance(self):
        '''
        Возвращает баланс счета
        
        @return: Balance
        '''
        result = Transaction.view('accounting/balance', key=self._id).one()['value']
        return Balance(result['debet'], result['kredit'])


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