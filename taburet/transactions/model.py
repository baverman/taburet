# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from itertools import groupby

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship, object_session

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    amount = Column(Numeric(18, 2))
    date = Column(DateTime)
    canceled = Column(Boolean)
    cancel_desc = Column(String(500))
    accounts = relationship('Destination', cascade="all, delete, delete-orphan")

    def cancel(self, desc=None):
        self.canceled = True
        self.desc = desc

    def __repr__(self):
        return "<%s -> %s: %f at %s>" % (repr(self.from_accs), repr(self.to_accs),
            self.amount, self.date)

    @property
    def from_accs(self):
        accs = [r for r in self.accounts if not r.direction]
        return [r.account for r in sorted(accs, key=lambda r: r.is_end)]

    @property
    def to_accs(self):
        accs = [r for r in self.accounts if r.direction]
        return [r.account for r in sorted(accs, key=lambda r: r.is_end)]


class Destination(Base):
    __tablename__ = 'destinations'

    tid = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    direction = Column(Boolean)
    account = Column(String(20), primary_key=True)
    is_end = Column(Boolean)

    def __repr__(self):
        return "[%s %s%s]" % (['<-', '->'][self.direction], self.account, '!' if self.is_end else '')

def make_transaction(acc_from, acc_to, amount, date=None):
    date = date or datetime.now()
    t = Transaction()
    t.amount = amount
    t.canceled = False
    t.date = date

    accounts = []

    for a in acc_from[:-1]:
        accounts.append(Destination(direction=False, account=a, is_end=False))
    accounts.append(Destination(direction=False, account=acc_from[-1], is_end=True))

    for a in acc_to[:-1]:
        accounts.append(Destination(direction=True, account=a, is_end=False))
    accounts.append(Destination(direction=True, account=acc_to[-1], is_end=True))

    t.accounts = accounts
    return t

class Balance(object):
    def __init__(self, debet, kredit):
        self.debet = debet
        self.kredit = kredit
        self.balance = debet - kredit

    def __repr__(self):
        return "<+: %f  -: %f  =: %f>" % (self.debet, self.kredit, self.balance)


def month_report(session, account_id_list, dt=None):
    dt = dt or datetime.now()

    dt_before = datetime(dt.year, dt.month, 1)
    dt_after = (dt_before + timedelta(days=32)).replace(day=1)

    rbefore = session.query(Destination.account, Destination.direction, func.sum(Transaction.amount))\
        .join(Transaction.accounts)\
        .filter(Destination.account.in_(account_id_list))\
        .filter(Transaction.canceled == False)\
        .filter(Transaction.date < dt_before)\
        .group_by(Destination.account, Destination.direction)

    rafter = session.query(Destination.account, Destination.direction, func.sum(Transaction.amount))\
        .join(Transaction.accounts)\
        .filter(Transaction.canceled == False)\
        .filter(Destination.account.in_(account_id_list))\
        .filter(Transaction.date >= dt_before)\
        .filter(Transaction.date < dt_after)\
        .group_by(Destination.account, Destination.direction)

    def get_debet_kredit(seq):
        result = {}
        for aid, dir, amount in seq:
            if aid not in result:
                result[aid] = [0, 0]

            if dir:
                result[aid][0] = amount
            else:
                result[aid][1] = amount

        return result

    result = {}
    for aid in account_id_list:
        result[aid] = {'kredit': 0, 'debet': 0, 'after': 0, 'before': 0}

    for aid, (d, k) in get_debet_kredit(rbefore).iteritems():
        rr = result[aid]
        rr['before'] = rr['after'] = d - k

    for aid, (d, k) in get_debet_kredit(rafter).iteritems():
        rr = result[aid]
        rr['debet'] = d
        rr['kredit'] = k
        rr['after'] = rr['before'] + d - k

    return result

def balance(session, aid, date_from=None, date_to=None):
    '''
    Возвращает баланс счета

    @return: Balance
    '''

    q = session.query(Destination.direction, func.sum(Transaction.amount))\
        .join(Transaction.accounts)\
        .filter(Destination.account == aid)\
        .filter(Transaction.canceled == False)

    if date_from:
        q = q.filter(Transaction.date >= date_from)

    if date_to:
        q = q.filter(Transaction.date < date_to)

    result = q.group_by(Destination.direction).all()

    kredit = debet = 0
    for r in result:
        if r[0]:
            debet = r[1]
        else:
            kredit = r[1]

    return Balance(debet, kredit)


def balances(id_list):
    '''
    Возвращает балансы переданных счетов

    @return: list of Balance
    '''
    return dict((r['key'], Balance(r['value']['debet'], r['value']['kredit']))
        for r in Transaction.get_db().view('transactions/balance', keys=id_list, group=True))


def day_report(session, aid, date_from=None, date_to=None):
    q = session.query(func.date_trunc('day', Transaction.date), Destination.direction,
             func.sum(Transaction.amount))\
        .join(Transaction.accounts)\
        .filter(Destination.account == aid)\
        .filter(Transaction.canceled == False)

    if date_from:
        q = q.filter(Transaction.date >= date_from)

    if date_to:
        q = q.filter(Transaction.date < date_to)

    result = q.group_by(func.date_trunc('day', Transaction.date), Destination.direction)

    data = []
    kredit = debet = 0
    last_data = None
    for r in result:
        if last_data is not None and last_data != r[0]:
            data.append((last_data, Balance(debet, kredit)))
            kredit = debet = 0

        last_data = r[0]
        if r[1]:
            debet = r[2]
        else:
            kredit = r[2]

    data.append((last_data, Balance(debet, kredit)))

    return data

def transactions(session, aid, date_from=None, date_to=None, income=False, outcome=False):
    q = session.query(Transaction)\
        .join(Transaction.accounts)\
        .filter(Destination.account == aid)

    if date_from:
        q = q.filter(Transaction.date >= date_from)

    if date_to:
        q = q.filter(Transaction.date < date_to)

    if income and not outcome:
        q = q.filter(Destination.direction == True)
    elif outcome and not income:
        q = q.filter(Destination.direction == False)

    return q
