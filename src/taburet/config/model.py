# -*- coding: utf-8 -*-

from couchdbkit import ResourceNotFound

NO_VALUE = object()

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