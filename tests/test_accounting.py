# -*- coding: utf-8 -*-

import sys, os.path

from couchdbkit import Server

from datetime import datetime

SRC_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..', 'src'))
sys.path.insert(0, SRC_PATH)

from taburet.utils import sync_design_documents
from taburet.accounting import AccountsPlan, set_db_for_models

TEST_DB = 'test'

def pytest_funcarg__db(request):
    s = Server()
    
    if TEST_DB in s:
        del s[TEST_DB]
    
    db = s.create_db(TEST_DB)

    set_db_for_models(db)
    
    sync_design_documents(db, ('taburet.counter', 'taburet.accounting'))
    
    return db

def test_account_tree_and_billing_case(db):
    plan = AccountsPlan()
    
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
    
def test_billing_must_return_values_for_date_period(db):
    plan = AccountsPlan()
    
    acc1 = plan.add_account()
    acc2 = plan.add_account()
    
    plan.create_transaction(acc1, acc2, 200.0, datetime(2010, 5, 20)).save()
    plan.create_transaction(acc1, acc2, 300.0, datetime(2010, 5, 31)).save()
    plan.create_transaction(acc1, acc2, 100.0, datetime(2010, 6, 01)).save()
    
    balance = acc2.balance(datetime(2010,5,1), datetime(2010,5,31))
    assert balance.balance == 500
    
    balance = acc1.balance(datetime(2010,6,1), datetime(2010,6,30))
    assert balance.balance == -100
    
    balance = acc2.balance(datetime(2010,5,1), datetime(2010,6,30))
    assert balance.balance == 600
    
def test_account_must_be_able_to_return_subaccounts(db):
    plan = AccountsPlan()
    
    acc1 = plan.add_account()
    acc2 = plan.add_account()
    
    sacc1 = plan.add_account(parent=acc1)
    sacc2 = plan.add_account(parent=acc1)
    
    ssacc1 = plan.add_account(parent=sacc2)
    
    accounts = plan.accounts()
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
    
def test_account_transaction_list(db):
    plan = AccountsPlan()
    
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
    
    result = acc1.transactions().all()
    assert len(result) == 2

    result = acc3.transactions().all()
    assert len(result) == 1
    
    result = acc1.transactions(datetime(2010, 5, 1), datetime(2010, 5, 31)).one()
    assert result.amount == 100
    assert result.date == datetime(2010, 5, 22, 10, 23, 40)
    
    result = acc1.transactions(datetime(2010, 6, 1), datetime(2010, 6, 30)).one()
    assert result.amount == 200  