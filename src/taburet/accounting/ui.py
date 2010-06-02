from flask import Module, abort, url_for, request 
from couchdbkit import ResourceNotFound

from .model import AccountsPlan, Account
from taburet.ui import Form, TreeViewControl, TreeViewEndpointDataSource, jsonify

module = Module('taburet.accounting', url_prefix='/accounting')

@module.route('/form/accounts-plan')
def form_accounts_plan():
    form = Form()
    form.add_control(
        TreeViewControl('accounts',
            TreeViewEndpointDataSource(url_for('data_accounts'))))
    
    return jsonify(form)

@module.route('/data/accounts')
def data_accounts():
    root = request.args.get('root', None) #@UndefinedVariable
    if not root:
        plan = AccountsPlan()
        accounts = plan.accounts()
    else:
        try:
            account = Account.get(root)
        except ResourceNotFound:
            abort(404)
        
        accounts = account.subaccounts()
        
    return jsonify([{'id':r._id, 'name':r.name if r.name else r._id} for r in accounts])

@module.route('/data/account/<id>')
def data_account(id):
    try:
        account = Account.get(id)
    except ResourceNotFound:
        abort(404)

    return jsonify({'id':account._id, 'name':account.name})