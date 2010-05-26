# -*- coding: utf-8 -*-

import sys, os.path

from couchdbkit import Server, Document, StringProperty

SRC_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..', 'src'))
sys.path.insert(0, SRC_PATH)

from taburet.utils import sync_design_documents
from taburet.counter import max_num_for, \
    save_doc_with_autoincremented_id, save_model_with_autoincremented_id

def pytest_funcarg__db(request):
    s = Server()
    
    if 'test' in s:
        del s['test']
    
    db = s.create_db('test')
    sync_design_documents(db, 'taburet.counter')
    
    return db

def test_counter_must_return_zero_for_nonexisting_keys(db):
    assert max_num_for(db, 'fake_prefix') == 0

def test_counter_must_return_max_value(db):
    db['aaa-1'] = {}
    db['aaa-2'] = {}
    db['aaa-bbb'] = {}
    db['vvv-50'] = {}
    
    assert max_num_for(db, 'aaa') == 2
    assert max_num_for(db, 'vvv') == 50
    
def test_counter_must_return_changed_value_after_document_adding(db):
    db['aaa-1'] = {}
    assert max_num_for(db, 'aaa') == 1
    
    db['aaa-100'] = {}
    assert max_num_for(db, 'aaa') == 100
    
def test_auto_increment_must_not_change_id_of_existing_documents(db):
    db['wow-20'] = {}
    doc = db['wow-20']
    doc['field'] = 'value'
    save_doc_with_autoincremented_id(doc, db, 'wow')
    
    assert db['wow-20']['field'] == 'value'
    assert 'wow-21' not in db
    
def test_auto_increment_must_increment_id_of_new_documents(db):
    db['wow-20'] = {}
    save_doc_with_autoincremented_id({'field':'value'}, db, 'wow')
    
    assert db['wow-21']['field'] == 'value'

def test_auto_increment_must_resolve_conflicts(db):
    db['aaa-1'] = {}
    
    save_doc_with_autoincremented_id({'_id':'aaa-1', 'field':'value'}, db, 'aaa')
    assert db['aaa-2']['field'] == 'value'

def test_save_model_document(db):
    
    class Model(Document):
        field = StringProperty()
    
    Model.set_db(db)
    
    doc = Model()
    save_model_with_autoincremented_id(doc, 'aaa')
    assert doc._id == 'aaa-1'
    
    doc = Model()
    doc._id = 'aaa-1'
    doc.field = 'value'
    save_model_with_autoincremented_id(doc, 'aaa')
    
    doc = Model.get('aaa-2')
    assert doc.field == 'value'  