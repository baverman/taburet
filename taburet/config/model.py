# -*- coding: utf-8 -*-
import weakref

from couchdbkit import ResourceNotFound, ResourceConflict

NO_VALUE = object()

def inc_updater(value):
    return value + 1

def dec_updater(value):
    return value - 1


class Param(object):
    def __init__(self, config, name):
        self.config = weakref.ref(config)
        self.name = name
        
    def get(self, default=NO_VALUE):
        return self.config().get(self.name, default)
    
    def set(self, value):
        self.config().set(self.name, value)
        
    def update(self, default, updater):
        return self.config().update(self.name, default, updater)
    
    def inc(self):
        return self.config().inc(self.name)

    def dec(self):
        return self.config().dec(self.name)

        
class Configuration(object):
    
    def __init__(self, db):
        self.db = db
        self.NotFound = ResourceNotFound

    def get(self, name, default=NO_VALUE):
        try:
            param = self.db.get(name)
        except ResourceNotFound:
            if default != NO_VALUE:
                return default
            else:
                raise
        
        return param['value']
    
    def set(self, name, value):
        try:
            doc = self.db.get(name)
            doc['value'] = value
        except ResourceNotFound:
            doc = {'_id':name, 'value':value}
        
        self.db.save_doc(doc)
        
    def update(self, name, default, updater):
        while True:
            try:
                doc = self.db.get(name)
            except ResourceNotFound:
                doc = {'_id':name, 'value':default}

            doc['value'] = updater(doc['value']) 
        
            try:
                self.db.save_doc(doc)
                break
            except ResourceConflict:
                pass
        
        return doc['value']
        
    def inc(self, name):
        return self.update(name, 0, inc_updater)
    
    def dec(self, name):
        return self.update(name, 0, dec_updater)

    def param(self, name):
        return Param(self, name)
