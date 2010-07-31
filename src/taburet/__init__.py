import sys, os.path
from couchdbkit import FileSystemDocsLoader

def get_package(package):
    if isinstance(package, basestring):
        if package not in sys.modules: 
            __import__(package)
        
        return sys.modules[package]
    else:
        return package

def iter_packages(packages):
    if not hasattr(packages, '__iter__'):
        packages = (packages,)
    
    for package in packages:
        yield get_package(package)


class DbSetter(object):
    def __init__(self):
        self.package_dbs = {}
        self.packages_to_set = set()
        self.synced_dbs = {}
    
    def set_db(self, db, *packages):
        for package in iter_packages(packages):
            if not getattr(package, 'set_db', False):
                raise Exception('Package %s has no items to set db' % package.__name__)
            
            if package.__name__ in self.package_dbs:
                raise Exception('Package %s already has assigned db: %s' % (package.__name__, db.uri))
            
            for r  in package.set_db:
                r.set_db(db)
                
            self.package_dbs[package.__name__] = db
            self.packages_to_set.add(package.__name__)
            
            map(self.packages_to_set.add, getattr(package, 'module_deps', ()))
                
    def validate(self):
        packages_without_db = [r for r in self.packages_to_set if r not in self.package_dbs]
        if packages_without_db:
            raise Exception('You mist set db for following packages: %s' % ', '.join(packages_without_db))

    def sync_package(self, db, package, verbose=True):
        pname = package.__name__
        if db.uri in self.synced_dbs and pname in self.synced_dbs[db.uri]:
            return
        
        self.synced_dbs.setdefault(db.uri, {})[pname] = True

        for path in package.__path__:
            design_path = os.path.join(path, '_design')
            if os.path.exists(design_path):
                loader = FileSystemDocsLoader(design_path)
                loader.sync(db, verbose=verbose)
        
        design_deps = getattr(package, 'design_deps', False) 
        if design_deps:
            for r in design_deps:
                self.sync_package(db, get_package(r), verbose)
        
    def sync_design_documents(self, verbose=True):
        self.validate()
        
        for pname, db in self.package_dbs.iteritems():
            self.sync_package(db, get_package(pname), verbose)