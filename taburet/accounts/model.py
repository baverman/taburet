# -*- coding: utf-8 -*-
from taburet.mongokit import Document, Field, wrap_collection

from taburet.counter import save_model_with_autoincremented_id
from taburet.transactions import balance, report, transactions, Transaction

class Account(Document):
    name = Field('')
    parents = Field([0])
    parent = Field(0)

    def balance(self, date_from=None, date_to=None):
        return balance(self.id, date_from, date_to)

    def report(self, date_from=None, date_to=None, group_by_day=True):
        return report(self.id, date_from, date_to, group_by_day)

    def subaccounts(self):
        return Account.find({'parent':self.id}).list()

    def transactions(self, date_from=None, date_to=None, income=False, outcome=False):
        return transactions(self.id, date_from, date_to, income, outcome)

    @property
    def account_path(self):
        return self.parents + [self.id]

    def __repr__(self):
        return "<Account: %s>" % self.id

def accounts_walk(accounts, only_leaf=False):
    def get_accounts(parent, level):
        subaccounts = sorted((r for r in accounts if (
            not parent and not r.parents) or (r.parents and parent == r.parents[-1])),
            key=lambda a:a.name)

        for acc in subaccounts:
            accs = list(get_accounts(acc.id, level + 1))
            if not accs or not only_leaf:
                yield level, acc
            for r in accs:
                yield r

    return get_accounts(None, 0)

class AccountsPlan(object):
    def add_account(self, name=None, parent=None):
        '''
        Добавляет счет в план

        @param name: расшифровка
        @param parent: счет, в который будет помещен создаваемый субсчет
        @return: Account
        '''
        account = Account()

        if name:
            account.name = name

        if parent:
            account.parents = parent.parents + [parent.id]
            account.parent = parent.id

        return save_model_with_autoincremented_id(account)

    def create_transaction(self, from_account, to_account, amount, date=None):
        tran = Transaction()
        tran.from_acc = from_account.parents + [from_account.id]
        tran.to_acc = to_account.parents + [to_account.id]
        tran.amount = amount

        if date:
            tran.date = date

        return tran

    def subaccounts(self):
        return Account.find({'parent':0}).list()

    def accounts(self):
        return Account.find().list()

    def get_by_name(self, name):
        return Account.find({'name':name}).one()

    def balance_report(self, date_from, date_to):
        pass
