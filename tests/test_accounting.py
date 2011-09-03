# -*- coding: utf-8 -*-
from datetime import datetime

from pymongo import Connection

from taburet import PackageManager
from taburet.accounts import AccountsPlan, Account
from taburet.transactions import month_report

def pytest_funcarg__plan(request):
    db = Connection().test
    db.accounts.drop()
    db.transactions.drop()
    db.transactions.balances.drop()
    db.transactions.balance.drop()

    PackageManager(db).use('taburet.accounts')

    return AccountsPlan()

def test_account_tree_and_billing_case(plan):
    zacs = plan.add_account()
    bich = plan.add_account(u"Бичиков", zacs)
    petrov = plan.add_account(u"Петров", zacs)

    kassa = plan.add_account()
    nal = plan.add_account(parent=kassa)
    beznal = plan.add_account(parent=kassa)

    zp = plan.add_account()
    konditer = plan.add_account(parent=zp)
    zavhoz = plan.add_account(parent=zp)

    plan.create_transaction(bich, nal, 1000.0).save()
    plan.create_transaction(petrov, nal, 500.0).save()
    plan.create_transaction(petrov, beznal, 100.0).save()

    plan.create_transaction(nal, konditer, 300.0).save()
    plan.create_transaction(nal, zavhoz, 200.0).save()

    assert zacs.balance().balance == -1600
    assert bich.balance().balance == -1000
    assert petrov.balance().balance == -600

    assert kassa.balance().balance == 1100
    assert kassa.balance().debet == 1600
    assert kassa.balance().kredit == 500

    assert zp.balance().balance == 500

def test_billing_must_return_values_for_date_period(plan):
    acc1 = plan.add_account()
    acc2 = plan.add_account()

    plan.create_transaction(acc1, acc2, 200.0, datetime(2010, 5, 20)).save()
    plan.create_transaction(acc1, acc2, 300.0, datetime(2010, 5, 31)).save()
    plan.create_transaction(acc1, acc2, 100.0, datetime(2010, 6, 01)).save()

    balance = acc2.balance(datetime(2010,5,1), datetime(2010,6,1))
    assert balance.balance == 500

    balance = acc1.balance(datetime(2010,6,1), datetime(2010,7,1))
    assert balance.balance == -100

    balance = acc2.balance(datetime(2010,5,1), datetime(2010,7,1))
    assert balance.balance == 600

def test_billing_must_return_zero_balance_for_period_without_transactions(plan):
    acc1 = plan.add_account()
    acc2 = plan.add_account()

    plan.create_transaction(acc1, acc2, 200.0, datetime(2010, 5, 20)).save()

    balance = acc2.balance(datetime(2010,5,21), datetime(2010,5,22))
    assert balance.balance == 0

def test_account_must_be_able_to_return_subaccounts(plan):
    acc1 = plan.add_account()
    acc2 = plan.add_account()

    sacc1 = plan.add_account(parent=acc1)
    sacc2 = plan.add_account(parent=acc1)

    ssacc1 = plan.add_account(parent=sacc2)

    accounts = plan.subaccounts()
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

    accounts = plan.accounts()
    assert acc1 in accounts
    assert acc2 in accounts
    assert sacc1 in accounts
    assert sacc2 in accounts
    assert ssacc1 in accounts

def test_account_must_be_able_to_be_found_by_name(plan):
    acc1 = plan.add_account(u'Счет1')
    plan.add_account(u'Счет2')

    acc = plan.get_by_name(u'Счет1')
    assert acc == acc1

    acc = plan.get_by_name(u'Счет3')
    assert acc == None

    plan.add_account(u'Счет1')

    try:
        plan.get_by_name(u'Счет1')
        assert False, 'MultipleResultsFound must be raised'
    except Account.MultipleResultsFound:
        pass

def test_account_transaction_list(plan):
    acc1 = plan.add_account()
    acc2 = plan.add_account()
    acc3 = plan.add_account()

    plan.create_transaction(acc1, acc2, 100.0, datetime(2010, 5, 22, 10, 23, 40)).save()
    plan.create_transaction(acc2, acc1, 200.0, datetime(2010, 6, 1, 10, 10, 10)).save()
    plan.create_transaction(acc3, acc2, 300.0, datetime(2010, 7, 1, 10, 10, 10)).save()

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

    result = acc1.transactions(datetime(2010, 5, 1), datetime(2010, 6, 1), income=True).one()
    assert result == None

    result = acc1.transactions(datetime(2010, 5, 1), datetime(2010, 6, 1), outcome=True).one()
    assert result.amount == 100

    result = acc1.transactions(datetime(2010, 6, 1), datetime(2010, 7, 1)).one()
    assert result.amount == 200

def test_account_report(plan):
    acc1 = plan.add_account()
    acc2 = plan.add_account()
    acc3 = plan.add_account()

    plan.create_transaction(acc1, acc2, 100.0, datetime(2010, 5, 22)).save()
    plan.create_transaction(acc2, acc1, 200.0, datetime(2010, 5, 25)).save()
    plan.create_transaction(acc3, acc2, 300.0, datetime(2010, 7, 1)).save()

    result = list(acc1.report(datetime(2010, 5, 1), datetime(2010, 5, 31)))
    assert result[0][0] == [2010, 5, 22]
    assert result[0][1].kredit == 100

    assert result[1][0] == [2010, 5, 25]
    assert result[1][1].debet == 200

def test_month_report(plan):
    acc1 = plan.add_account()
    acc2 = plan.add_account()
    acc3 = plan.add_account()

    plan.create_transaction(acc1, acc2, 50.0, datetime(2009, 8, 22)).save()
    plan.create_transaction(acc1, acc2, 100.0, datetime(2010, 5, 22)).save()
    plan.create_transaction(acc2, acc1, 200.0, datetime(2010, 5, 25)).save()
    plan.create_transaction(acc3, acc2, 300.0, datetime(2010, 7, 1)).save()

    result = month_report((acc1.id, acc2.id), datetime(2010, 5, 22))
    assert len(result) == 2
    assert result[acc1.id] == {'before':-50, 'debet':200, 'kredit':100, 'after':50}
    assert result[acc2.id] == {'before':50, 'debet':100, 'kredit':200, 'after':-50}

    result = month_report((acc1.id, acc2.id), datetime(2010, 7, 1))
    assert len(result) == 2
    assert result[acc1.id] == {'before':50, 'debet':0, 'kredit':0, 'after':50}
    assert result[acc2.id] == {'before':-50, 'debet':300, 'kredit':0, 'after':250}

    result = month_report((acc3.id,), datetime(2010, 7, 1))
    assert len(result) == 1
    assert result[acc3.id] == {'before':0, 'debet':0, 'kredit':300, 'after':-300}