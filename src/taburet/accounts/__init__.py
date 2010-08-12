from .model import Account, AccountsPlan

set_db = (Account,)
module_deps = ('taburet.transactions',)
design_deps = ('taburet.counter', 'taburet.doctype')