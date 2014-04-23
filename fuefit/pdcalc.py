#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2013-2014 ankostis@gmail.com
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
import logging
'''A best-effort attempt to build computation dependency-graphs from method with dict-like objects (such as pandas),
inspired by XForms:
    http://lib.tkk.fi/Diss/2007/isbn9789512285662/article3.pdf
'''
# from unittest.mock import MagicMock
from fuefit.mymock import MagicMock
from collections.abc import Iterable
import itertools as it
import functools as ft
import networkx as nx
import re


_root_name = 'R'
log = logging.getLogger(__file__)


def get_mock_factory():
    return MagicMock
#     pyver = sys.version_info[:2]
#     if (pyver[0] >=3 and pyver[1] >=4):
#         return MagicMock
#     else:
## Workaround missing __truediv__() BUG fixed in 3.4: http://bugs.python.org/issue20968
#
#         class DepGrapher(MagicMock):
#             def __truediv__(self, other):
#                 return self.__div__(other)
#         return DepGrapher
make_mock = get_mock_factory()


def harvest_funcs_factory(funcs_factory, func_rels=None):
    if not func_rels:
        func_rels = []

    ## Invoke funcs_factory with "rooted" mockups as args
    #    to collect mock_calls.
    #
    (root, mocks) = mockup_func_args(funcs_factory)
    funcs = funcs_factory(*mocks)

    ## Harvest func deps as a list of 3-tuple (item, deps, funx)
    #    by inspecting root after each func-call.
    #
    for func in funcs:
        root.reset_mock()
        func()
        harvest_mock_calls(root.mock_calls, func, func_rels)

    assert validate_func_relations(func_rels), func_rels
    return func_rels

def harvest_func(func, func_rels=None):
    if not func_rels:
        func_rels = []

    (root, mocks) = mockup_func_args(func)
    func(*mocks)
    harvest_mock_calls(root.mock_calls, func, func_rels)

    assert validate_func_relations(func_rels), func_rels
    return func_rels


def mockup_func_args(func):
    import inspect

    argspec = inspect.getfullargspec(func)
    if (argspec.varargs or argspec.varkw):
        log.warning('Ignoring any dependencies from *varags or **keywords!')
    return make_mock_args(argspec.args)

def make_mock_args(args):
    root = make_mock(name=_root_name)
    mocks = [make_mock() for arg in args]
    for (mock, arg) in zip(mocks, args):
        root.attach_mock(mock, arg)
    return (root, mocks)


def harvest_mock_calls(mock_calls, func, func_rels):
    deps_set = set()
    parent = None
    for call in mock_calls:
        parent = harvest_mock_call(call, func, deps_set, func_rels)

    ## Any remaining deps came from a last not-assignment (a statement) in func.
    #  Add them as non-dependent items.
    #
    if deps_set:
        ## Not sure why add parent, but without it:
        #    df(params.hh['tt'])
        #  skips R.df!
        deps_set.add(parent)
        for dep in filter_common_prefixes(deps_set):
            append_func_relation(dep, [], func, func_rels)


def harvest_mock_call(mock_call, func, deps_set, func_rels):
    '''Adds a 2-tuple (indep, [deps]) into indeps with all deps collected so far when it visits a __setartr__. '''
    (path, args, kw) = mock_call

    deps_set.update((harvest_mock(arg) for arg in args if isinstance(arg, MagicMock)))
    deps_set.update((harvest_mock(v) for v in kw.values() if isinstance(v, MagicMock)))


    parent = harvest_mock(mock_call.parent)
    #parent = strip_magick_calls(path)
    tail = path.split('.')[-1]
    if (tail == '__getitem__'):
        for item in harvest_indexing(args[0]):
            deps_set.add('%s.%s'%(parent, item))
    if (tail == '__setitem__'):
        deps = list(deps_set)
        deps_set.clear()

        for item in harvest_indexing(args[0]):
            append_func_relation('%s.%s'%(parent, item), deps, func, func_rels)

    return parent

def append_func_relation(item, deps, func, func_rels):
    func_rels.append((item, deps, func))

def harvest_indexing(index):
    '''Harvest any strings, slices, etc, assuming to be DF's indices. '''

#         if isinstance(index, MagicMock):
#             deps = [harvest_mock(index)]
    if isinstance(index, slice):
        deps = harvest_indexing(index.start) + harvest_indexing(index.stop) + harvest_indexing(index.step)
    elif isinstance(index, str):
        deps = [index]
    elif isinstance(index, Iterable):
        deps = list(it.chain(*[harvest_indexing(indx) for indx in index]))
    else:
        deps = []
    return deps

def harvest_mock(mock):
    return strip_magick_calls(parse_mock_str(mock)[0])

def strip_magick_calls(path):#Assumes magciks always at tail.
    pa_th = path.split('.')
    while (pa_th[-1].startswith('__')):
        del pa_th[-1]
        if (not pa_th):
            return []
    path = '.'.join(pa_th)
    return path

_mock_id_regex = re.compile(r"name='([^']+)' id='(\d+)'")
def parse_mock_str(m):
    return _mock_id_regex.search(m.__repr__()).groups()

def validate_func_relations(func_rels):
    items = [not item.startswith(_root_name) for (item, _, _) in func_rels]
    if any(items):
        return False
    deps = [not dep.startswith(_root_name) for (_, deps, _) in func_rels for dep in deps]
    if any(deps):
        return False
    return True


def build_func_dependencies_graph(func_rels):
    G = nx.DiGraph()

    paths = set()
    for (path, deps, func_fact) in func_rels:
        paths.add(path)
        if (deps):
            deps = filter_common_prefixes(deps)
            G.add_edges_from([(path, dep, {'func_fact': func_fact}) for dep in deps])

    ## Add all LSide 'R.dotted.objects' segments,
    #     even without any func attribute.
    #
    for path in set(paths):
        G.add_edges_from(gen_all_prefix_pairs(path))

    return G


def gen_all_prefix_pairs(path):
    ''' R.foo.com' --> [('R.foo.com', 'R.foo'), ('R.foo', 'R')] but outer reversed'''
    (it1, it2) = it.tee(path.split('.'))
    s1 = ''
    s2 = next(it2)
    try:
        while(True):
            s1 += next(it1)
            s2 += '.' + next(it2)
            yield (s2, s1)
            s1 += '.'
    except StopIteration:
        pass

def filter_common_prefixes(deps):
    '''deps: not-empty set

    example::
        deps = ['a', 'a.b', 'b.cc', 'a.d', 'b', 'ac', 'a.c']
        res = filter_common_prefixes(deps)
        assert res == ['a.b', 'a.c', 'a.d', 'ac', 'b.cc']
    '''

    deps = sorted(deps)
    (it1, it2) = it.tee(deps)
    s2 = next(it2)
    ndeps = []
    try:
        while(True):
            s1=next(it1)
            s2=next(it2)
            if s1+'.' != s2[:len(s1)+1]:
                ndeps.append(s1)
    except StopIteration:
        ndeps.append(s2)

    return ndeps

