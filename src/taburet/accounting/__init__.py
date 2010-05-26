import os.path
from couchdbkit.loaders import FileSystemDocsLoader
from .model import Transaction, Account, AccountsPlan

def set_db_for_models(db):
    Transaction.set_db(db)
    Account.set_db(db)