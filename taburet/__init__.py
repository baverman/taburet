import sys

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
    def __init__(self, db):
        self.db = db
        self.processed_uses = {}

    def use(self, *packages):
        for package in iter_packages(packages):
            pname = package.__name__

            if pname in self.processed_uses: continue

            self.processed_uses[pname] = True

            if getattr(package, 'init', False):
                package.init(self)
