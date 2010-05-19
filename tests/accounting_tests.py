# -*- coding: utf-8 -*-

import sys, os.path

from couchdbkit import Server

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

def tes_transactions(db):
    t1 = Transaction(from_acc=['acc1'], to_acc=['acc2'], amount=100.05)
    t2 = Transaction(from_acc=['acc3'], to_acc=['acc2'], amount=450.11)
    t3 = Transaction(from_acc=['acc2'], to_acc=['acc1'], amount=50.99)
    
    t1.save()
    t2.save()
    t3.save()
    
    result = Transaction.view('accounting/balance', key="acc1")
    assert result.one()['value'] == -49.06

    result = Transaction.view('accounting/balance', key="acc2")
    assert result.one()['value'] == 499.17

    result = Transaction.view('accounting/balance', key="acc3")
    assert result.one()['value'] == -450.11
    
    result = Transaction.view('accounting/balance')
    assert result.one()['value'] == 0
    
def test_account_tree_and_billing(db):
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