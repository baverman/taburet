import os.path
from couchdbkit.loaders import FileSystemDocsLoader
from .model import Transaction, Account, AccountsPlan

def sync_design_documents(db, verbose=False):
    loader = FileSystemDocsLoader(os.path.join(os.path.split(__file__)[0], '_design'))
    loader.sync(db, verbose=verbose)
    
def set_db_for_models(db):
    Transaction.set_db(db)
    Account.set_db(db)