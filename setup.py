#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 ankostis@gmail.com
#
# This file is part of fuefit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

''''fuefit: Fit fuel-consumption engine-maps on a physical formula with 6 parameters.


Install:
========

To install it, assuming you have download the sources,
do the usual::

    python setup.py install

Or get it directly from the PIP repository::

    pip3 install fuefit


Tested with Python 3.4.


@author: ankostis@gmail.com, Apr-2014, JRC, (c) AGPLv3 or later

'''

import os
from cx_Freeze import Executable
from cx_Freeze import setup
# from distutils.core import setup
# from setuptools import setup
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

readme_lines = read_text_lines('README.txt')

setup(
    name=projname,
    packages=[projname],
#     package_data= {'projname': ['data/*.csv']},
    version=read_project_version('_version.py'),
    description=readme_lines[1],
    long_description='\n'.join(readme_lines),
    author="ankostis",
    author_email="ankostis@gmail.com",
    url="https://github.com/ankostis/fuefit",
    license="GNU Affero General Public License v3 or later (AGPLv3+)",
    keywords=['fuel', 'fuel-consumption', 'engine', 'engine-map', 'emissions', 'fitting', 'vehicles', 'cars', 'automotive'],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
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
        'jsonpointer',
        'networkx',
        'pint',
    ],
    scripts = ['fuefit.py'],
    options={
        'build_exe': {
            "excludes": [
                "jsonschema", #!!!! Schemas do not work in library-zip, so needs manuall to copy directly into app-dir
                "numpy", "scipy", #!!!! lostesso
                "PyQt4", "PySide",
                "IPython", "numexpr",
                "pygments", "pyreadline", "jinja2",
                "setuptools",
                "statsmodels", "docutils",
                "xmlrpc", "pytz",
                "nose",
                "Cython", "pydoc_data", "sphinx", "docutils",
                "multiprocessing", "lib2to3", "_markerlib",
#                 #urllib<--email<--http<--pandas
#                 #distutils" <-- pandas.compat
            ],
            'includes': [
                'matplotlib.backends.backend_tkagg',
            ],
            'include_files': [
                ## MANUAL COPY into build/exe-dir
                ##     from: https://bitbucket.org/anthony_tuininga/cx_freeze/issue/43/import-errors-when-using-cx_freeze-with
                #  site_packages(32bit/64bit)/
                #    jsonschema
                #    numpy
                #    scipy
            ],
            'include_msvcr': True,
            'compressed': False,
#            'create_shared_zip': False,
#             'include_in_shared_zip': True,
        }, 'bdist_msi': {
            'add_to_path': False,
        },
    },
    executables=[Executable("fuefit.py", )], #base="Win32GUI")],
)
