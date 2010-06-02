#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

sys.path.append('./src')

from taburet.utils import sync_design_documents
import taburet.accounting.ui

import couchdbkit

from flask import Flask
app = Flask(__name__)
app.debug = True

app.register_module(taburet.accounting.ui.module)

s = couchdbkit.Server()
db = s.get_or_create_db('demo')
sync_design_documents(db, ('taburet.counter', 'taburet.accounting'))
taburet.accounting.set_db_for_models(db)

app.run()