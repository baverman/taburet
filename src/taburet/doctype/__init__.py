import os.path
from couchdbkit import FileSystemDocsLoader, ResourceConflict, Document

def get_by_type(cls):
    return cls.view('doctype/get', key=cls.__name__, include_docs=True)   