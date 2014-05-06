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

''''A calculator producing fuel-consumption engine-maps from measured data-points
fitted according to XXX's formula.


Install:
========

To install it, assuming you have download the sources,
do the usual::

    python setup.py install

Or get it directly from the PIP repository::

    pip3 install fuefit


Tested with Python 3.4.


Overview:
=========

Fuefit accepts as input data-points for RPM, Power and Fuel-Consumprtion
(or equivalent quantities such as CM, PME/Torwue and PMF) and spits-out
fitted fuel-maps according to the formula:

   (a + b*cm + c*cm**2)*pmf + (a2 + b2*cm)*pmf**2 + loss0 + loss2*cm**2\n",

An "execution" or a "run" of an experiment is depicted in the following diagram::

                           _______________
         .----------.     |               |      .------------------.
        /   Model  /  ==> |   Experiment  | ==> / Model(augmented) /
       /----------/       |_______________|    '------------------'
      /  fuefit  /
     /  consts  /
    '----------'

Usage:
======

A usage example::

    >> import fuefit

    >> model = {
        "engine": {
            "gear_ratios":      [120.5, 75, 50, 43, 37, 32],
            "resistance_coeffs":[100, 0.5, 0.04],
        }
    }

    >> experiment = fuefit.Experiment(model)

    >> model = experiment.run()

    >> print(model['engine']


For information on the model-data, check the schema::

    print(fuefit.instances.model_schema())



@author: ankostis@gmail.com, Apr-2014, JRC, (c) AGPLv3 or later

'''

#from setuptools import setup
from cx_Freeze import setup, Executable
import os

projname = 'fuefit'
mydir = os.path.dirname(__file__)

## Version-trick to have version-info in a single place,
## taken from: http://stackoverflow.com/questions/2058802/how-can-i-get-the-version-defined-in-setup-py-setuptools-in-my-package
##
def readversioninfo(fname):
    fglobals = {'__version_info__':('x', 'x', 'x')} # In case reading the version fails.
    exec(open(os.path.join(mydir, projname, fname)).read(), fglobals)  # To read __version_info__
    return fglobals['__version_info__']

# Trick to use README file as long_description.
#  It's nice, because now 1) we have a top level README file and
#  2) it's easier to type in the README file than to put a raw string in below ...
def readtxtfile(fname):
    with open(os.path.join(mydir, fname)) as fd:
        return fd.read()

setup(
    name = projname,
    packages = [projname],
#     package_data= {'projname': ['data/*.csv']},
    test_suite="fuefit.test", #TODO: check setup.py testsuit indeed works.
    version = '.'.join(readversioninfo('_version.py')),
    description = __doc__.strip().split("\n")[0],
    author = "ankostis",
    author_email = "ankostis@gmail.com",
    url = "https://github.com/ankostis/fuefit",
    license = "GNU Affero General Public License v3 or later (AGPLv3+)",
    keywords = ['fuel', 'fuel-consumption', 'engine', 'engine-map', 'emissions', 'fitting', 'vehicles', 'cars', 'automotive'],
    classifiers = [
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
    long_description = __doc__,
    install_requires = [
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
    test_requires = [
    ],
    options = {
        'build_exe': {
            'include_msvcr': True,
            'compressed': True,
            'include_in_shared_zip': True,
        }, 'bdist_msi': {
            'add_to_path': False,
        },
    },
    executables = [Executable("fuefit/main.py")]
)
