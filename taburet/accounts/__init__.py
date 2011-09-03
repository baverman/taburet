from model import Account, AccountsPlan, accounts_walk

def init(manager):
    Account.__collection__ = manager.db.accounts
    manager.db.accounts.ensure_index('parent')
    manager.db.accounts.ensure_index('name')

    manager.use('taburet.transactions')