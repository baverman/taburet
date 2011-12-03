from .model import Account, get_account_by_name, get_toplevel_accounts, create_account, \
    create_transaction, get_all_accounts

def init(manager):
    from . import model
    manager.on_sync(model.Base.metadata.create_all)
    manager.on_drop(model.Base.metadata.drop_all)

    manager.use('taburet.transactions')
