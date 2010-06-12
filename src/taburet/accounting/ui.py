# -*- coding: utf-8 -*-

from flask import Module, abort, url_for, request 
from couchdbkit import ResourceNotFound

from .model import AccountsPlan, Account
from taburet.ui import (Window, Form, TreeViewControl, TreeViewEndpointDataSource,
    jsonify, TextField)

module = Module('taburet.accounting', url_prefix='/accounting')

@module.route('/form/accounts-plan')
def form_accounts_plan():
    window = Window()
    
    tree = TreeViewControl('accounts',
            TreeViewEndpointDataSource(url_for('data_accounts')))
    tree.root_title = u'Счета'
    
    form = Form('account', url_for('data_account'),[
        TextField('id', 'id'),
        TextField('name', u'Счет')
    ])
   
    window.add(tree)
    window.add(form)
    
    window.on(tree.selected_event()) \
        .do(form.update_action())
    
    return jsonify(window)

@module.route('/data/accounts')
def data_accounts():
    root = request.args.get('root', None) #@UndefinedVariable
    if not root or root=='root':
        plan = AccountsPlan()
        accounts = plan.accounts()
    else:
        try:
            account = Account.get(root)
        except ResourceNotFound:
            abort(404)
        
        accounts = account.subaccounts()
        
    return jsonify([{'id':r._id, 'name':r.name if r.name else r._id} for r in accounts])

@module.route('/data/account/<id>', methods=('GET', 'POST'))
@module.route('/data/account', methods=('GET', 'POST'))
def data_account(id=None):
    id = id or request.args.get('id') #@UndefinedVariable
    try:
        account = Account.get(id)
    except ResourceNotFound:
        abort(404)

    return jsonify({'id':account._id, 'name':account.name})