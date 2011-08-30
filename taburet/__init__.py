import sys, os.path

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


class PackageManager(object):
    def __init__(self):
        self.package_dbs = {}
        self.packages_to_set = set()
        self.synced_dbs = {}
        self.processed_uses = {}
        self.same_dbs = {}

    def set_db(self, db, *packages):
        for package in iter_packages(packages):
            pname = package.__name__
            if not getattr(package, 'set_db', False):
                raise Exception('Package %s has no items to set db' % pname)

            if pname in self.package_dbs:
                raise Exception('Package %s already has assigned db: %s' % (pname, db.uri))

            self.package_dbs[pname] = db
            self.packages_to_set.add(pname)

            self.use(package)

    def use(self, *packages):
        for package in iter_packages(packages):
            pname = package.__name__

            if pname in self.processed_uses: continue

            self.processed_uses[pname] = True

            if getattr(package, 'set_db', False):
                self.packages_to_set.add(pname)

            if getattr(package, 'same_db', False):
                self.same_dbs[pname] = package.same_db
                self.packages_to_set.add(package.same_db)

            self.use(*getattr(package, 'module_deps', ()))

    def init_same_dbs(self):
        def set_db(pname):
            sname = self.same_dbs[pname]
            if sname in self.package_dbs:
                self.package_dbs[pname] = self.package_dbs[sname]
            elif sname in self.same_dbs:
                set_db(sname)

        for pname in self.same_dbs:
            set_db(pname)

    def validate(self):
        self.init_same_dbs()
        packages_without_db = [r for r in self.packages_to_set if r not in self.package_dbs]
        if packages_without_db:
            raise Exception('You must set db for following packages: %s' % ', '.join(packages_without_db))

    def sync_package(self, db, package, verbose=True):
        pname = package.__name__
        if db.uri in self.synced_dbs and pname in self.synced_dbs[db.uri]:
            return

        self.synced_dbs.setdefault(db.uri, {})[pname] = True

        for path in package.__path__:
            design_path = os.path.join(path, '_design')
            if os.path.exists(design_path):
                for dname in os.listdir(design_path):
                    full_path = os.path.join(design_path, dname)
                    if os.path.isdir(full_path):
                        doc = document(full_path)
                        doc.push((db,), force=True)

        design_deps = getattr(package, 'design_deps', False)
        if design_deps:
            for r in design_deps:
                self.sync_package(db, get_package(r), verbose)

    def sync_design_documents(self, verbose=True):
        self.validate()

        for pname, db in self.package_dbs.iteritems():
            package = get_package(pname)

            for r  in package.set_db:
                r.set_db(db)

            self.sync_package(db, package, verbose)

    def set_dbs(self):
        self.validate()

        for pname, db in self.package_dbs.iteritems():
            package = get_package(pname)

            for r  in package.set_db:
                r.set_db(db)
