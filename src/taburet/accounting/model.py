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
    
    balance = property(lambda self: Transaction.view('accounting/balance', key=self._id).one()['value'])
    debet = property(lambda self: Transaction.view('accounting/debet', key=self._id).one()['value'])
    kredit = property(lambda self: Transaction.view('accounting/kredit', key=self._id).one()['value'])


class AccountsPlan(object):
    def __init__(self):
        pass
    
    def add_account(self, id, title=None, parent=None):
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