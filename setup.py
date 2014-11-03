#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
''''fuefit: Fit fuel-consumption engine-maps on a physical formula with 6 parameters.


Install:
========

To install it, assuming you have download the sources,
do the usual::

    python setup.py install

Or get it directly from the PIP repository::

    pip install fuefit


Tested with Python 3.4.


@author: ankostis@gmail.com, Apr-2014, JRC, (c) EUPL or later

'''

from distutils.version import StrictVersion
import sys, os

from setuptools import setup


## Fail early in ancient python-versions
#
py_verinfo = sys.version_info
py_sver = StrictVersion("%s.%s.%s" % py_verinfo[:3])
if py_verinfo[0] != 3 or py_sver < StrictVersion("3.3"):
    exit("Sorry, only Python >= 3.3 is supported!")
if sys.argv[-1] == 'setup.py':
    exit("To install, run `python setup.py install`")
    

projname = 'fuefit'
mydir = os.path.dirname(__file__)

# # Version-trick to have version-info in a single place,
# # taken from: http://stackoverflow.com/questions/2058802/how-can-i-get-the-version-defined-in-setup-py-setuptools-in-my-package
# #
def read_project_version(fname):
    fglobals = {'__version__':'x.x.x'}  # In case reading the version fails.
    exec(open(os.path.join(mydir, projname, fname)).read(), fglobals)
    return fglobals['__version__']

# Trick to use README file as long_description.
#  It's nice, because now 1) we have a top level README file and
#  2) it's easier to type in the README file than to put a raw string in below ...
def read_text_lines(fname):
    with open(os.path.join(mydir, fname)) as fd:
        return fd.readlines()

readme_lines = read_text_lines('README.rst')

setup(
    name=projname,
    version=read_project_version('_version.py'),
    description=readme_lines[1],
    long_description='\n'.join(readme_lines),
    author="Kostis Anagnostopoulos @ European Commission (JRC)",
    author_email="ankostis@gmail.com",
    url="https://github.com/ankostis/fuefit",
    download_url = "https://pypi.python.org/pypi/fuefit",
    license = "European Union Public Licence 1.1 or later (EUPL 1.1+)",
    keywords = [
         "automotive", "vehicle", "vehicles", "car", "cars", "fuel", "consumption",
        "engine", "engine-map", "fitting",
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: CPython",
        "Development Status :: 4 - Beta",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "License :: OSI Approved :: European Union Public Licence 1.1 (EUPL 1.1)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=['fuefit', 'fuefit.test', 'fuefit.excel'],
    package_data={'fuefit': ['docs'],},
#    extras_require = {
#        'Docs':  ['sphinx >= 1.2'],
#    },
    include_package_data = True,
    install_requires=[
        'enum34',
        'pandas',
        'xlrd',
        'scipy',
        'jsonschema',
        'networkx',
        'pint',
        'xlwings >= 0.2.3',
    ],
    setup_requires = [
        'setuptools',# >= 3.4.4',
        'setuptools-git >= 0.3',
        'sphinx >=1.2', # >=1.3
        'sphinx_rtd_theme',
        'matplotlib',
    ],
    tests_require = [
        'nose',
    ],
    test_suite='nose.collector',
    entry_points={
        'console_scripts': [
            'fuefit          = fuefit.__main__:main',
        ],
    },
    zip_safe=False,
    options={
        'build_sphinx' :{
            'build_dir': 'docs/_build',
        }
    },
)
