from setuptools import setup, find_packages

setup(
    name     = 'taburet',
    version  = '0.1dev',
    author   = 'Anton Bobrov',
    author_email = 'bobrov@vl.ru',
    description = 'Accounting platform',
#    long_description = open('README.rst').read(),
    zip_safe   = False,
    packages = find_packages(),
    install_requires = ['blinker', 'pyExcelerator', 'couchdbkit'],
    include_package_data = True,
    url = 'http://github.com/baverman/taburet',
    classifiers = [
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: Developers",
        "Natural Language :: Russian",
    ],
)
