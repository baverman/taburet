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
    def __init__(self, session):
        self.session = session
        self.processed_uses = {}

        self.on_sync_cb = []
        self.on_drop_cb = []

    def on_sync(self, func):
        self.on_sync_cb.append(func)
        return func

    def on_drop(self, func):
        self.on_drop_cb.append(func)
        return func

    def sync(self):
        for f in self.on_sync_cb:
            f(self.session.get_bind())

    def drop(self):
        for f in self.on_drop_cb:
            f(self.session.get_bind())

    def use(self, *packages):
        for package in iter_packages(packages):
            pname = package.__name__

            if pname in self.processed_uses: continue

            self.processed_uses[pname] = True

            if getattr(package, 'init', False):
                package.init(self)
