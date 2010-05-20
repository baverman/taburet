# -*- coding: utf-8 -*-

from couchdbkit import Document, ListProperty, FloatProperty, StringProperty
from couchdbkit import Property, BadValueError

from calendar import timegm
import datetime, time

class DateTimeProperty(Property):
    def __init__(self, verbose_name=None, auto_now=False, auto_now_add=False,
               **kwds):
        super(DateTimeProperty, self).__init__(verbose_name, **kwds)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        self.FORMAT = '%Y/%m/%d %H:%M:%S'

    def validate(self, value, required=True):
        value = super(DateTimeProperty, self).validate(value, required=required)

        if value is None:
            return value

        if value and not isinstance(value, self.data_type):
            raise BadValueError('Property %s must be a %s, current is %s' %
                          (self.name, self.data_type.__name__, type(value).__name__))
        return value

    def default_value(self):
        if self.auto_now or self.auto_now_add:
            return self.now()
        return Property.default_value(self)

    def to_python(self, value):
        if isinstance(value, basestring):
            try:
                timestamp = timegm(time.strptime(value, self.FORMAT))
                value = datetime.datetime.utcfromtimestamp(timestamp)
            except ValueError:
                raise ValueError('Invalid ISO date/time %r' % value)
        return value

    def to_json(self, value):
        if self.auto_now:
            value = self.now()
        
        if value is None:
            return value
        
        return value.replace(microsecond=0).strftime(self.FORMAT)

    data_type = datetime.datetime

    @staticmethod
    def now():
        return datetime.datetime.utcnow()


class Transaction(Document):
    from_acc = ListProperty(verbose_name="From accounts", required=True)
    to_acc = ListProperty(verbose_name="To accounts", required=True)
    amount = FloatProperty(default=0.0)
    date = DateTimeProperty(default=datetime.datetime.now, required=True)


class Account(Document):
    title = StringProperty()
    parents = ListProperty()
    
    def _get_balance_key(self, date):
        return [self._id, date.year, date.month, date.day]
    
    def get_balance(self, date_from=None, date_to=None):
        '''
        Возвращает баланс счета
        
        @return: Balance
        '''
        
        if date_from is None and date_to is None:
            result = Transaction.view('accounting/balance', key=self._id).one()['value']
        else:
            params = {}
            if date_from:
                params['startkey'] = self._get_balance_key(date_from)
            
            if date_to:
                params['endkey'] = self._get_balance_key(date_to)
                
            result = Transaction.view('accounting/balance_for_account', **params).one()['value']
        
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