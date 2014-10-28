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

from distutils.core import setup
import os

from setuptools import setup


#import py2exe
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
    packages=[projname],
#     package_data= {'projname': ['data/*.csv']},
    version=read_project_version('_version.py'),
    description=readme_lines[1],
    long_description='\n'.join(readme_lines),
    author="Kostis Anagnostopoulos @ European Commission (JRC)",
    author_email="ankostis@gmail.com",
    url="https://github.com/ankostis/fuefit",
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
    requires=[
        'enum34',
        'numpy',
        'pandas',
        'xlrd',
        'scipy',
        'jsonschema',
        'networkx',
        'pint',
        'xlwings',
    ],
    entry_points={
        'console_scripts': [
            'fuefitcmd = fuefit.cmdline:main',
        ],
    }, 
    options={
    },
)
