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
'''A best-effort attempt to build computation dependency-graphs from method with dict-like objects (such as pandas),
inspired by XForms:
    http://lib.tkk.fi/Diss/2007/isbn9789512285662/article3.pdf
'''
# from unittest.mock import MagicMock
from fuefit.mymock import MagicMock
from collections.abc import Iterable
import itertools
import networkx as nx
import sys
import re

# from . import json_dumps
from fuefit import json_dumps, mymock, pairwise

## Workaround missing __truediv__() BUG fixed in 3.4: http://bugs.python.org/issue20968
def get_instrospector_var_factory():
    pyver = sys.version_info[:2]
    return MagicMock
#     if (pyver[0] >=3 and pyver[1] >=4):
#         return MagicMock
#     else:
#         class DepGrapher(MagicMock):
#             def __truediv__(self, other):
#                 return self.__div__(other)
#         return DepGrapher
make_instrospector_var = get_instrospector_var_factory()


def def_calculations(params, engine, df):
    from math import pi

    def f1(): engine['fuel_lhv'] = params['fuel'][engine['fuel']]['lhv']
    def f2(): df['rpm']     = df.rpm_norm * (engine.rpm_rated - engine.rpm_idle) + engine.rpm_idle
    def f3(): df['p']       = df.p_norm * engine.p_max
    def f4(): df['fc']      = df.fc_norm * engine.p_max
    def f5(): df['rps']     = df.rpm / 60
    def f6(): df['torque']  = (df.p * 1000) / (df.rps * 2 * pi)
    def f7(): df['pme']     = (df.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-3)
    def f8(): df['pmf']     = ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-3)) * (df.fc / (3600 * df.rps * 2 * pi)) * 10e-5
    def f9(): df['cm']      = df.rps * 2 * engine.stroke / 1000

    return (f1, f2, f3, f4, f5, f6, f7, f8, f9)


def gather_dependencies(funcs_factory):
    import inspect

    ## Invoke funcs_factory with "rooted" mockups as args.
    #
    argspec = inspect.getfullargspec(funcs_factory)
    if (argspec.varargs or argspec.varkw):
        raise NotImplementedError('Inspecting dependencies for func-factory with *varags or **keywords not supported!')
    (root, mocks) = make_introspect_args(argspec.args)
    funcs = funcs_factory(*mocks)

    ## Harvest func deps by inspecting root each time.
    #
    collected_deps_map = []
    for func in funcs:
        root.reset_mock()
        func()
        harvest_calls(root.mock_calls, func, collected_deps_map)

    return collected_deps_map


def make_introspect_args(args):
    root = make_instrospector_var(name='R')
    mocks = [make_instrospector_var() for arg in args]
    for (mock, arg) in zip(mocks, args):
        root.attach_mock(mock, arg)
    return (root, mocks)


def harvest_calls(mock_calls, func, collected_deps_map):
    collected_deps = set()
    for call in mock_calls:
        harvest_call(call, func, collected_deps, collected_deps_map)

    assert not collected_deps, collected_deps


def harvest_call(mock_call, func, collected_deps, collected_deps_map):
    '''Adds a 2-tuple (indep, [deps]) into indeps with all deps collected so far when it visits a __setartr__. '''
    (path, args, kw) = mock_call

    collected_deps.update((harvest_mock(arg) for arg in args if isinstance(arg, MagicMock)))
    collected_deps.update((harvest_mock(v) for v in kw.values() if isinstance(v, MagicMock)))


    parent = harvest_mock(mock_call.parent)
    #parent = strip_magick_calls(path)
    tail = path.split('.')[-1]
    if (tail == '__getitem__'):
        for item in harvest_indexing(args[0]):
            collected_deps.add('%s.%s'%(parent, item))
    if (tail == '__setitem__'):
        deps = list(collected_deps)
        collected_deps.clear()

        for item in harvest_indexing(args[0]):
            collected_deps_map.append(('%s.%s'%(parent, item), deps, func))


def harvest_indexing(index):
    '''Harvest any strings, slices, etc, assuming to be DF's indices. '''

#         if isinstance(index, MagicMock):
#             deps = [harvest_mock(index)]
    if isinstance(index, slice):
        deps = harvest_indexing(index.start) + harvest_indexing(index.stop) + harvest_indexing(index.step)
    elif isinstance(index, str):
        deps = [index]
    elif isinstance(index, Iterable):
        deps = list(itertools.chain(*[harvest_indexing(indx) for indx in index]))
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



def build_func_dependencies_graph(deps_map):
    G = nx.DiGraph()

    paths = set()   ## Collects all 'R.dotted.objects' to enforce segment-deps.
    for (item, deps, func) in deps_map:
        paths.add(item)
        paths.update(deps)

        G.add_edges_from([(item, dep, {'func': func}) for dep in deps])

#     for path in paths:
#         path.split('.')[::-1]

    return G




def test_inspect_func_dependencies():
    def func(df, params):
        df.hh[['tt','ll', 'i']]    = params.tt
        df.hh['tt':'ll', 'i']    = params.tt
        df.hh['tt']['ll']  = params.OO
        df(params.pp['g'])

    deps = gather_dependencies(func)
    print(deps)
    assert deps[0][1] == ['tt','ll', 'i'], deps[0][1]
    assert deps[1][1] == ['tt','ll', 'i'], deps[0][1]
    assert deps[2][1] == ['tt'], deps[2][1]
    assert deps[3][1] == ['ll'], deps[3][1]

    func1 = lambda df, params: df.hh[['tt','ll', 'i', params.b]]['g'] + params.tt
    func2 = lambda df, params: df.hh['tt','ll', 'i', params.b]['g'] + params.tt
    func3 = lambda df, params: df.hh['tt':'ll', 'i', params.b]['g'] + params.tt

    deps = gather_dependencies(func1); print(deps)
    deps = gather_dependencies(func2); print(deps)
    deps = gather_dependencies(func3); print(deps)



if __name__ == "__main__":
#     test_inspect_func_dependencies()
    deps = gather_dependencies(def_calculations)
    print('\n'.join([str(s) for s in deps]))

    G = build_func_dependencies_graph(deps)
    print(G.edge)
    print(nx.topological_sort(G))
    print(nx.topological_sort_recursive(G))
