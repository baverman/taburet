import os.path
import sys
from couchdbkit import FileSystemDocsLoader

def sync_design_documents(db, packages, verbose=True):
    if not hasattr(packages, '__iter__'):
        packages = (packages,)
        
    for package in packages:
        if isinstance(package, basestring):
            __import__(package)
            package = sys.modules[package]
            
        for p in package.__path__:
            path = os.path.join(p, '_design')
            loader = FileSystemDocsLoader(path)
            loader.sync(db, verbose=verbose)