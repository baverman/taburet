# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from taburet.transactions import make_transaction, balance, transactions, day_report

Base = declarative_base()

class Account(Base):
    __tablename__ = 'accounts'

    NoResultFound = NoResultFound
    MultipleResultsFound = MultipleResultsFound

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    parent = Column(Integer)
    parents = Column(String(100))
    desc = Column(String(500))

    def __init__(self, name, parent=None, desc=None):
        self.name = name
        if parent:
            assert parent.id, 'Parent obj must be persistent'
            self.parents = parent.account_path
            self.parent = parent.id
        else:
            self.parents = ''
            self.parent = None

        self.desc = desc

    @property
    def tid(self):
        assert self.id
        return 'account:%s' % self.id

    def balance(self, date_from=None, date_to=None):
        return balance(object_session(self), self.tid, date_from, date_to)

    def report(self, date_from=None, date_to=None):
        return day_report(object_session(self), self.tid, date_from, date_to)

    def subaccounts(self):
        return object_session(self).query(Account).filter_by(parents=self.account_path).all()

    def transactions(self, date_from=None, date_to=None, income=False, outcome=False):
        return transactions(object_session(self), self.tid, date_from, date_to, income, outcome)

    @property
    def account_path(self):
        if self.parents:
            return self.parents + ':' + str(self.id)
        else:
            return str(self.id)

    @property
    def parent_accounts(self):
        if self.parents:
            session = object_session(self)
            ids = map(int, self.parents.split(':'))
            return session.query(Account).filter(Account.id.in_(ids)).all()
        else:
            return []

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

def create_transaction(from_account, to_account, amount, date=None):
    from_accs = ['account:' + r for r in from_account.account_path.split(':')]
    to_accs = ['account:' + r for r in to_account.account_path.split(':')]
    return make_transaction(from_accs, to_accs, amount, date)

def get_toplevel_accounts(session):
    return session.query(Account).filter_by(parent=None).all()

def get_all_accounts(session):
    return session.query(Account).all()

def get_account_by_name(session, name):
    try:
        return session.query(Account).filter_by(name=name).one()
    except NoResultFound:
        return None

def balance_report(session, date_from, date_to):
    pass

def create_account(session, name=None, parent=None, desc=None):
    acc = Account(name, parent, desc)
    session.add(acc)
    session.flush()
    return acc