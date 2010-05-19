import sys, os.path

from couchdbkit import Server

SRC_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..', 'src'))
sys.path.insert(0, SRC_PATH)
from taburet.accounting import Transaction, Account, sync_design_documents

def pytest_funcarg__db(request):
    s = Server()
    
    if 'test' in s:
        del s['test']
    
    db = s.create_db('test')

    Transaction.set_db(db)
    
    sync_design_documents(db, True)
    
    return db

def test_transactions(db):
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