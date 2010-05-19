import os.path
from couchdbkit.loaders import FileSystemDocsLoader
from .model import Transaction, Account

def sync_design_documents(db, verbose=False):
    loader = FileSystemDocsLoader(os.path.join(os.path.split(__file__)[0], '_design'))
    loader.sync(db, verbose=verbose)