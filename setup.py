#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
''''
Setuptools script for *fuefit* that calculates fitted fuel-maps from measured engine data-points based on coefficients with physical meaning.


Install:
========

Runs on Python-3, tested on: see :file:`.travis.yaml`

To install it, assuming you have download the sources,
do the usual::

    python setup.py install

Or get it directly from the PIP repository::

    pip install fuefit

'''

from distutils.version import StrictVersion
import os, sys, io
import re

from setuptools import setup


## Fail early in ancient python-versions
#
py_verinfo = sys.version_info
py_sver = StrictVersion("%s.%s.%s" % py_verinfo[:3])
if py_verinfo[0] != 3 or py_sver < StrictVersion("3.3"):
    exit("Sorry, only Python 3.3+ is supported!")
if sys.argv[-1] == 'setup.py':
    exit("To install, run `python setup.py install`")
    

proj_name = 'fuefit'
mydir = os.path.dirname(__file__)

## Version-trick to have version-info in a single place,
## taken from: http://stackoverflow.com/questions/2058802/how-can-i-get-the-version-defined-in-setup-py-setuptools-in-my-package
##
def read_project_version():
    fglobals = {}
    with io.open(os.path.join(mydir, proj_name, '_version.py')) as fd:
        exec(fd.read(), fglobals)  # To read __version__
    return fglobals['__version__']

def read_text_lines(fname):
    with io.open(os.path.join(mydir, fname)) as fd:
        return fd.readlines()

def yield_sphinx_only_markup(lines):
    """
    :param file_inp:     a `filename` or ``sys.stdin``?
    :param file_out:     a `filename` or ``sys.stdout`?`

    """
    substs = [
        ## Selected Sphinx-only Roles.
        #
        (r':abbr:`([^`]+)`',        r'\1'),
        (r':ref:`([^`]+)`',         r'`\1`_'),
        (r':term:`([^`]+)`',        r'**\1**'),
        (r':dfn:`([^`]+)`',         r'**\1**'),
        (r':(samp|guilabel|menuselection):`([^`]+)`',        r'``\2``'),


        ## Sphinx-only roles:
        #        :foo:`bar`   --> foo(``bar``)
        #        :a:foo:`bar` XXX afoo(``bar``)
        #
        #(r'(:(\w+))?:(\w+):`([^`]*)`', r'\2\3(``\4``)'),
        (r':(\w+):`([^`]*)`', r'\1(``\2``)'),


        ## Sphinx-only Directives.
        #
        (r'\.\. doctest',           r'code-block'),
        (r'\.\. plot::',            r'.. '),
        (r'\.\. seealso',           r'info'),
        (r'\.\. glossary',          r'rubric'),
        (r'\.\. figure::',          r'.. '),
        (r'\.\. image::',          r'.. '),


        ## Other
        #
        (r'\|version\|',              r'x.x.x'),
    ]

    regex_subs = [ (re.compile(regex, re.IGNORECASE), sub) for (regex, sub) in substs ]

    def clean_line(line):
        try:
            for (regex, sub) in regex_subs:
                line = regex.sub(sub, line)
        except Exception as ex:
            print("ERROR: %s, (line(%s)"%(regex, sub))
            raise ex

        return line

    for line in lines:
        yield clean_line(line)



proj_ver = read_project_version()


readme_lines = read_text_lines('README.rst')
description = readme_lines[1]
long_desc = ''.join(yield_sphinx_only_markup(readme_lines))
## Trick from: http://peterdowns.com/posts/first-time-with-pypi.html
download_url = 'https://github.com/ankostis/%s/tarball/v%s' %(proj_name, proj_ver)

setup(
    name=proj_name,
    version=proj_ver,
    description=description,
    long_description=long_desc,
    author="Kostis Anagnostopoulos @ European Commission (JRC)",
    author_email="ankostis@gmail.com",
    url="https://github.com/ankostis/fuefit",
    download_url=download_url,
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
    include_package_data = True,
    package_data={
        'fuefit.test': ['*.bat', '*.sh'],
        'fuefit.excel': ['*.xlsm', '*.ico'],
    },
#    extras_require = {
#        'docs':  ['sphinx >= 1.2'],
#    },
    install_requires=[
        'enum34',
        'pandas',
        'xlrd',
        'scipy',
        'lmfit',
        'jsonschema',
        'matplotlib',
        'networkx',
        'pint',
        'xlwings == 0.2.3',
    ],
    setup_requires = [
        'setuptools',# >= 3.4.4',
        'setuptools-git >= 0.3', ## Gather package-data from all files in git.
        'nose>=1.0',
        'sphinx', # >=1.3',
        'sphinx_rtd_theme',
        'matplotlib',
        'wheel',
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
    zip_safe=True,
    options={
        'build_sphinx' :{
            'build_dir': 'docs/_build',
        },
        'bdist_wheel' :{
            'universal': True,
        },
    },
)
