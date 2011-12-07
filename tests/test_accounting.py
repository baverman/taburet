# -*- coding: utf-8 -*-
from datetime import datetime

from taburet.accounts import Account, get_account_by_name, get_toplevel_accounts, create_account, \
    create_transaction, get_all_accounts
from taburet.transactions import transactions, month_report, TransactionBase

from .helpers import pytest_funcarg__pm

class Transaction(TransactionBase): pass

def pytest_funcarg__session(request):
    pm = pytest_funcarg__pm(request)
    pm.use('taburet.accounts', Transaction=Transaction)

    pm.drop()
    pm.sync()

    return pm.session

def test_account_plan_creating(session):
    create_account(session, 'Бу')
    create_account(session, 'Ла')
    session.commit()

    result = [r.name for r in get_toplevel_accounts(session)]
    assert u'Бу' in result
    assert u'Ла' in result
    assert len(result) == 2

def test_accounts_tree(session):
    create_account(session, 'acc1')
    create_account(session, 'acc3', create_account(session, 'acc2'))
    session.commit()

    result = [r.name for r in get_toplevel_accounts(session)]
    assert u'acc1' in result
    assert u'acc2' in result
    assert len(result) == 2

    acc = get_account_by_name(session, 'acc2')
    result = acc.subaccounts()
    assert len(result) == 1
    assert result[0].name == 'acc3'

    result = result[0].parent_accounts
    assert len(result) == 1
    assert result[0].name == 'acc2'

    result = result[0].parent_accounts
    assert result == []

def test_account_tree_and_billing_case(session):
    zacs = create_account(session)
    bich = create_account(session, u"Бичиков", zacs)
    petrov = create_account(session, u"Петров", zacs)

    kassa = create_account(session)
    nal = create_account(session, parent=kassa)
    beznal = create_account(session, parent=kassa)

    zp = create_account(session)
    konditer = create_account(session, parent=zp)
    zavhoz = create_account(session, parent=zp)
    session.commit()

    t = create_transaction(bich, nal, 1000.0)
    session.add(t)
    session.add(create_transaction(petrov, nal, 500.0))
    session.add(create_transaction(petrov, beznal, 100.0))

    session.add(create_transaction(nal, konditer, 300.0))
    session.add(create_transaction(nal, zavhoz, 200.0))
    session.commit()

    assert zacs.balance().balance == -1600
    assert bich.balance().balance == -1000
    assert petrov.balance().balance == -600

    assert kassa.balance().balance == 1100
    assert kassa.balance().debet == 1600
    assert kassa.balance().kredit == 500

    assert zp.balance().balance == 500

    t.amount = 900
    session.commit()

    assert zacs.balance().balance == -1500
    assert bich.balance().balance == -900
    assert petrov.balance().balance == -600

    assert kassa.balance().balance == 1000
    assert kassa.balance().debet == 1500
    assert kassa.balance().kredit == 500

    assert zp.balance().balance == 500

def test_billing_must_return_values_for_date_period(session):
    acc1 = create_account(session)
    acc2 = create_account(session)
    session.commit()

    session.add(create_transaction(acc1, acc2, 200.0, datetime(2010, 5, 20)))
    session.add(create_transaction(acc1, acc2, 300.0, datetime(2010, 5, 31)))
    session.add(create_transaction(acc1, acc2, 100.0, datetime(2010, 6, 01)))
    session.commit()

    balance = acc2.balance(datetime(2010,5,1), datetime(2010,6,1))
    assert balance.balance == 500

    balance = acc1.balance(datetime(2010,6,1), datetime(2010,7,1))
    assert balance.balance == -100

    balance = acc2.balance(datetime(2010,5,1), datetime(2010,7,1))
    assert balance.balance == 600

def test_billing_must_return_zero_balance_for_period_without_transactions(session):
    acc1 = create_account(session)
    acc2 = create_account(session)
    session.commit()

    session.add(create_transaction(acc1, acc2, 200.0, datetime(2010, 5, 20)))

    balance = acc2.balance(datetime(2010,5,21), datetime(2010,5,22))
    assert balance.balance == 0

def test_account_must_be_able_to_return_subaccounts(session):
    acc1 = create_account(session)
    acc2 = create_account(session)

    sacc1 = create_account(session, parent=acc1)
    sacc2 = create_account(session, parent=acc1)

    ssacc1 = create_account(session, parent=sacc2)
    session.commit()

    accounts = get_toplevel_accounts(session)
    assert acc1 in accounts
    assert acc2 in accounts
    assert not sacc2 in accounts

    accounts = acc1.subaccounts()
    assert sacc1 in accounts
    assert sacc2 in accounts
    assert not acc1 in accounts

    accounts = sacc2.subaccounts()
    assert accounts == [ssacc1]

    accounts = acc2.subaccounts()
    assert accounts == []

    accounts = get_all_accounts(session)
    assert acc1 in accounts
    assert acc2 in accounts
    assert sacc1 in accounts
    assert sacc2 in accounts
    assert ssacc1 in accounts

def test_account_must_be_able_to_be_found_by_name(session):
    acc1 = create_account(session, u'Счет1')
    create_account(session, u'Счет2')

    acc = get_account_by_name(session, u'Счет1')
    assert acc.id == acc1.id

    acc = get_account_by_name(session, u'Счет3')
    assert acc == None

    create_account(session, u'Счет1')

    try:
        get_account_by_name(session, u'Счет1')
        assert False, 'MultipleResultsFound must be raised'
    except Account.MultipleResultsFound:
        pass

def test_account_transaction_list(session):
    acc1 = create_account(session)
    acc2 = create_account(session)
    acc3 = create_account(session)
    session.commit()

    session.add(create_transaction(acc1, acc2, 100.0, datetime(2010, 5, 22, 10, 23, 40)))
    session.add(create_transaction(acc2, acc1, 200.0, datetime(2010, 6, 1, 10, 10, 10)))
    session.add(create_transaction(acc3, acc2, 300.0, datetime(2010, 7, 1, 10, 10, 10)))
    session.commit()

    result = acc2.transactions().all()
    assert result[0].amount == 100
    assert result[1].amount == 200
    assert result[2].amount == 300

    result = acc2.transactions(income=True).all()
    assert len(result) == 2
    assert result[0].amount == 100
    assert result[1].amount == 300

    result = acc2.transactions(outcome=True).all()
    assert len(result) == 1
    assert result[0].amount == 200

    result = acc1.transactions().all()
    assert len(result) == 2

    result = acc3.transactions().all()
    assert len(result) == 1

    result = acc1.transactions(datetime(2010, 5, 1), datetime(2010, 6, 1)).one()
    assert result.amount == 100
    assert result.date == datetime(2010, 5, 22, 10, 23, 40)

    try:
        result = acc1.transactions(datetime(2010, 5, 1), datetime(2010, 6, 1), income=True).one()
        assert False, 'NoResultFound must was thrown'
    except Account.NoResultFound: pass

    result = acc1.transactions(datetime(2010, 5, 1), datetime(2010, 6, 1), outcome=True).one()
    assert result.amount == 100

    result = acc1.transactions(datetime(2010, 6, 1), datetime(2010, 7, 1)).one()
    assert result.amount == 200

def test_transaction_list_must_include_all_destinations(session):
    acc1 = create_account(session)
    acc2 = create_account(session)
    acc3 = create_account(session, parent=acc2)
    session.commit()

    session.add(create_transaction(acc1, acc3, 100.0))
    session.commit()

    acc1_tid = acc1.tid
    acc2_tid = acc2.tid
    acc3_tid = acc3.tid
    session.expunge_all()

    result = transactions(session, acc3_tid).one()
    assert result.from_accs == [acc1_tid]
    assert result.to_accs == [acc2_tid, acc3_tid]

    result = transactions(session, acc3_tid, income=True).one()
    assert result.from_accs == [acc1_tid]
    assert result.to_accs == [acc2_tid, acc3_tid]

def test_account_report(session):
    acc1 = create_account(session)
    acc2 = create_account(session)
    acc3 = create_account(session)
    session.commit()

    session.add(create_transaction(acc1, acc2, 100.0, datetime(2010, 5, 22)))
    session.add(create_transaction(acc2, acc1, 200.0, datetime(2010, 5, 25)))
    session.add(create_transaction(acc3, acc2, 300.0, datetime(2010, 7, 1)))
    session.commit()

    result = list(acc1.report(datetime(2010, 5, 1), datetime(2010, 6, 1)))
    assert result[0][0] == datetime(2010, 5, 22)
    assert result[0][1].kredit == 100

    assert result[1][0] == datetime(2010, 5, 25)
    assert result[1][1].debet == 200

def test_month_report(session):
    acc1 = create_account(session)
    acc2 = create_account(session)
    acc3 = create_account(session)
    session.commit()

    session.add(create_transaction(acc1, acc2, 50.0, datetime(2009, 8, 22)))
    session.add(create_transaction(acc1, acc2, 100.0, datetime(2010, 5, 22)))
    session.add(create_transaction(acc2, acc1, 200.0, datetime(2010, 5, 25)))
    session.add(create_transaction(acc3, acc2, 300.0, datetime(2010, 7, 1)))

    result = month_report(session, (acc1.tid, acc2.tid), datetime(2010, 5, 22))
    assert len(result) == 2
    assert result[acc1.tid] == {'before':-50, 'debet':200, 'kredit':100, 'after':50}
    assert result[acc2.tid] == {'before':50, 'debet':100, 'kredit':200, 'after':-50}

    result = month_report(session, (acc1.tid, acc2.tid), datetime(2010, 7, 1))
    assert len(result) == 2
    assert result[acc1.tid] == {'before':50, 'debet':0, 'kredit':0, 'after':50}
    assert result[acc2.tid] == {'before':-50, 'debet':300, 'kredit':0, 'after':250}

    result = month_report(session, (acc3.tid,), datetime(2010, 7, 1))
    assert len(result) == 1
    assert result[acc3.tid] == {'before':0, 'debet':0, 'kredit':300, 'after':-300}

def test_billing_support_transaction_cancellation(session):
    acc1 = create_account(session)
    acc2 = create_account(session)
    session.commit()

    t = create_transaction(acc1, acc2, 50.0)
    session.add(t)
    session.commit()

    assert acc1.balance().balance == -50
    assert acc2.balance().balance == 50

    t.cancel('Bad')
    session.commit()

    assert acc1.balance().balance == 0
    assert acc2.balance().balance == 0

def test_billing_support_transaction_removing(session):
    acc1 = create_account(session)
    acc2 = create_account(session)
    session.commit()

    t = create_transaction(acc1, acc2, 50.0)
    session.add(t)
    session.commit()

    assert acc1.balance().balance == -50
    assert acc2.balance().balance == 50

    session.delete(t)
    session.commit()
    assert acc1.balance().balance == 0
    assert acc2.balance().balance == 0