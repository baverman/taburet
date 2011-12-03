# -*- coding: utf-8 -*-
from .model import make_transaction, Base, balance, transactions, day_report, month_report

def init(manager):
    manager.on_sync(Base.metadata.create_all)
    manager.on_drop(Base.metadata.drop_all)
