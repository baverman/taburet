# -*- coding: utf-8 -*-
from pymongo import Connection

from taburet.mongokit import Document, Field
from taburet.counter import last_id_for, save_doc_with_autoincremented_id, \
    save_model_with_autoincremented_id

def pytest_funcarg__db(request):
    db = Connection().test
    db.collection1.drop()
    db.collection2.drop()
    return db

def test_counter_must_return_zero_for_nonexisting_keys(db):
    assert last_id_for(db.some_collection1) == 0

def test_counter_must_return_max_value(db):
    c1 = db.collection1
    c2 = db.collection2

    c1.insert({'_id':1})
    c1.insert({'_id':2})

    c2.insert({'_id':50})

    assert last_id_for(c1) == 2
    assert last_id_for(c2) == 50

def test_counter_must_return_changed_value_after_document_adding(db):
    c = db.collection1

    c.insert({'_id':1})
    assert last_id_for(c) == 1

    c.insert({'_id':100})
    assert last_id_for(c) == 100

def test_auto_increment_must_not_change_id_of_existing_documents(db):
    c = db.collection1

    c.insert({'_id':20})
    doc = c.find_one({'_id':20})
    doc['field'] = 'value'
    save_doc_with_autoincremented_id(c, doc)

    assert c.find_one({'_id':20})['field'] == 'value'
    assert not c.find({'_id':21}).count()

def test_auto_increment_must_increment_id_of_new_documents(db):
    c = db.collection1

    c.insert({'_id':20})

    save_doc_with_autoincremented_id(c, {'field':'value'})
    assert c.find_one({'_id':21})['field'] == 'value'

def test_auto_increment_on_concurent_document_saves(db):
    c = db.collection1

    c.insert({'_id':20})

    def insert():
        c.save({'_id':21})

    save_doc_with_autoincremented_id(c, {'field':'value'}, insert)
    assert c.find_one({'_id':22})['field'] == 'value'

def test_auto_increment_on_model(db):
    class Doc(Document):
        __collection__ = db.collection1

    Doc(document={'_id':20}).save()

    d = Doc()
    dd = save_model_with_autoincremented_id(d)

    assert dd is d
    assert d.id == 21
