# -*- coding: utf-8 -*-

from model import Transaction, Balance, month_report, balance, report, transactions

def init(manager):
    Transaction.__collection__ = manager.db.transactions

    manager.db.transactions.balances.ensure_index([('_id.acc', 1), ('_id.dt', 1)])

    manager.db.transactions.ensure_index([('date', 1), ('from_acc', 1)])
    manager.db.transactions.ensure_index([('date', 1), ('to_acc', 1)])
