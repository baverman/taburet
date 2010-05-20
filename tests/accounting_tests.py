# -*- coding: utf-8 -*-

import sys, os.path

from couchdbkit import Server

from datetime import datetime

SRC_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..', 'src'))
sys.path.insert(0, SRC_PATH)
from taburet.accounting import Transaction, AccountsPlan, sync_design_documents, set_db_for_models

def pytest_funcarg__db(request):
    s = Server()
    
    if 'test' in s:
        del s['test']
    
    db = s.create_db('test')

    set_db_for_models(db)
    
    sync_design_documents(db, True)
    
    return db

def tes_account_tree_and_billing_case(db):
    plan = AccountsPlan()
    
    zacs = plan.add_account("acc_zac")
    bich = plan.add_account("acc_zac_bich", u"Бичиков", zacs)
    petrov = plan.add_account("acc_zac_petrov", u"Петров", zacs)
    
    kassa = plan.add_account("acc_kassa")
    nal = plan.add_account("acc_kassa_nal", parent=kassa)
    beznal = plan.add_account("acc_kassa_beznal", parent=kassa)
    
    zp = plan.add_account("acc_zp")
    konditer = plan.add_account('acc_zp_konditer', parent=zp)
    zavhoz = plan.add_account('acc_zp_zavhoz', parent=zp)
    
    plan.create_transaction(bich, nal, 1000.0).save()
    plan.create_transaction(petrov, nal, 500.0).save()
    plan.create_transaction(petrov, beznal, 100.0).save()
    
    plan.create_transaction(nal, konditer, 300.0).save()
    plan.create_transaction(nal, zavhoz, 200.0).save()
    
    assert zacs.get_balance().balance == -1600
    assert bich.get_balance().balance == -1000
    assert petrov.get_balance().balance == -600
    
    assert kassa.get_balance().balance == 1100
    assert kassa.get_balance().debet == 1600
    assert kassa.get_balance().kredit == 500
    
    assert zp.get_balance().balance == 500
    
def test_billing_must_return_values_for_date_period(db):
    plan = AccountsPlan()
    
    acc1 = plan.add_account('acc1')
    acc2 = plan.add_account('acc2')
    
    plan.create_transaction(acc1, acc2, 200.0, datetime(2010, 5, 20)).save()
    plan.create_transaction(acc1, acc2, 300.0, datetime(2010, 5, 31)).save()
    plan.create_transaction(acc1, acc2, 100.0, datetime(2010, 6, 01)).save()
    
    balance = acc2.get_balance(datetime(2010,5,1), datetime(2010,5,31))
    assert balance.balance == 500
    
    balance = acc1.get_balance(datetime(2010,6,1), datetime(2010,6,30))
    assert balance.balance == -100
    
    balance = acc2.get_balance(datetime(2010,5,1), datetime(2010,6,30))
    assert balance.balance == 600 