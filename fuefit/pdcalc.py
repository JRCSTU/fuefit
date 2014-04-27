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
import logging
from collections import OrderedDict, defaultdict
from collections.abc import Mapping, Iterable
import itertools as it
import functools as ft
import networkx as nx
from networkx.exception import NetworkXError
import re
from fuefit.mymock import MagicMock


_root_name = 'R'
_root_len = len(_root_name)+1
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


def harvest_funcs_factory(funcs_factory, root=None, renames=None, func_rels=None):
    if func_rels is  None:
        func_rels = []

    ## Invoke funcs_factory with "rooted" mockups as args
    #    to collect mock_calls.
    #
    (root, mocks) = mockup_func_args(funcs_factory, root=root, renames=renames)
    funcs = funcs_factory(*mocks)

    ## Harvest func deps as a list of 3-tuple (item, deps, funx)
    #    by inspecting root after each func-call.
    #
    for func in funcs:
        root.reset_mock()
        tmp = func()
        try: tmp += 2   ## Force dependencies from return values despite compiler-optimizations.
        except:
            pass
        harvest_mock_calls(root.mock_calls, func, func_rels)

    assert validate_func_relations(func_rels), func_rels
    return func_rels

def harvest_func(func, root=None, renames=None, func_rels=None):
    if func_rels is None:
        func_rels = []

    (root, mocks) = mockup_func_args(func, root=root, renames=renames)
    tmp = func(*mocks)
    try: tmp += 2   ## Force dependencies from return values despite compiler-optimizations.
    except:
        pass
    harvest_mock_calls(root.mock_calls, func, func_rels)

    assert validate_func_relations(func_rels), func_rels
    return func_rels


def mockup_func_args(func, renames=None, root=None):
    '''    renames: list or dict with renames, same len as func's args.'''
    import inspect

    argspec = inspect.getfullargspec(func)
    if (argspec.varargs or argspec.varkw):
        log.warning('Ignoring any dependencies from *varags or **keywords!')
    func_args = argspec.args

    ## Apply any override arg-names.
    #
    if renames:
        if isinstance(renames, Mapping):
            new_args = {arg:arg for arg in func_args}
            new_args.update(renames)
            new_args = new_args.keys()
        else:
            new_args = [arg if arg else farg for (farg, arg) in zip(func_args, renames)]
        if len(func_args) != len(new_args):
            raise ValueError("Argument-renames mismatched function(%s)!\n  Expected(%s), got(%s), result(%s)."%(func, func_args, renames, new_args))
        func_args = new_args

    if not root:
        root = make_mock(name=_root_name)
    mocks = [make_mock() for cname in func_args]
    for (mock, cname) in zip(mocks, func_args):
        root.attach_mock(mock, cname)
    return (root, mocks)


def harvest_mock_calls(mock_calls, func, func_rels):
    ## A map from 'pure.dot.paths --> call.__paths__
    #  filled-in and consumed )mostly) by harvest_mock_call().
    deps_set = OrderedDict()

    #last_path = None Not needed!
    for call in mock_calls:
        last_path = harvest_mock_call(call, func, deps_set, func_rels)

    ## Any remaining deps came from a last not-assignment (a statement) in func.
    #  Add them as non-dependent items.
    #
    if deps_set:
        deps_set[last_path] = None  ## We don't care about call dep-subprefixes(the value) anymore.
#         if ret is None:
#             item = last_path
#         else:
#             item = parse_mock_arg(ret)
        for dep in filter_common_prefixes(deps_set.keys()):
            append_func_relation(dep, [], func, func_rels)

def parse_mock_arg(mock):
    mpath = parse_mock_str(mock)[0]
    return (strip_magic_tail(mpath), mpath)

def harvest_mock_call(mock_call, func, deps_set, func_rels):
    '''Adds a 2-tuple (indep, [deps]) into indeps with all deps collected so far when it visits a __setartr__. '''

    def parse_mock_path(mock):
        mpath = parse_mock_str(mock)[0]
        try:
            ## Hack to consolidate 'dot.__getitem__.com' --> fot.Xt.com attributes.
            #  Just search if previous call is subprefix of this one.
            prev_path = next(reversed(deps_set))
            prev_call = deps_set[prev_path]
            if (prev_call+'()' == call[:len(prev_call)+2]):
                mpath = prev_path + mpath[len(prev_call)+_root_len+2:] # 4 = R.()
        except (KeyError, StopIteration):
            pass
        return strip_magic_tail(mpath)

    (call, args, kw) = mock_call

    deps_set.update((parse_mock_arg(arg) for arg in args        if isinstance(arg, MagicMock)))
    deps_set.update((parse_mock_arg(arg) for arg in kw.values() if isinstance(arg, MagicMock)))


    path = parse_mock_path(mock_call.parent)

    tail = call.split('.')[-1]
    if (tail == '__getitem__'):
        for item in harvest_indexing(args[0]):
            new_path = '%s.%s'%(path, item)
            deps_set[new_path] = call
    elif (tail == '__setitem__'):
        deps = list(deps_set.keys())
        deps_set.clear()

        for item in harvest_indexing(args[0]):
            new_path ='%s.%s'%(path, item)
            append_func_relation(new_path, deps, func, func_rels)

    return path

def append_func_relation(item, deps, func, func_rels):
    func_rels.append((item, deps, func))

def harvest_indexing(index):
    '''Harvest any strings, slices, etc, assuming to be DF's indices. '''

    if isinstance(index, slice):
        deps = harvest_indexing(index.start) + harvest_indexing(index.stop) + harvest_indexing(index.step)
    elif isinstance(index, str):
        deps = [index]
    elif isinstance(index, Iterable):
        deps = list(it.chain(*[harvest_indexing(indx) for indx in index]))
    else:
        deps = []
    return deps


def strip_magic_tail(path):
    '''    some.path___with_.__magics__ --> some.path '''
    pa_th = path.split('.')
    while (pa_th[-1].startswith('__')):
        del pa_th[-1]
        if (not pa_th):
            return []
    path = '.'.join(pa_th)
    return path[:-2] if path.endswith('()') else path


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


def build_func_dependencies_graph(func_rels, graph = None):
    if graph is None:
        graph = nx.DiGraph()

    (func_rels, all_paths) = consolidate_relations(func_rels)

    for (path, (deps, funcs)) in func_rels.items():
        if (deps):
            deps = filter_common_prefixes(deps)
            graph.add_edges_from([(path, dep, {'funcs': funcs}) for dep in deps])

    ## Add all LSide 'R.dotted.objects' segments,
    #     even without any funcs attribute.
    #
    for path in set(all_paths):
        graph.add_edges_from(gen_all_prefix_pairs(path))

    cycles = list(nx.simple_cycles(graph))
    if cycles:
        raise ValueError('Cyclic dependencies! %s', cycles)

    return graph


def consolidate_relations(relations):
    rels = defaultdict()
    rels.default_factory = lambda: (set(), set())

    ## Join all item's  deps & funcs
    #
    for (item, deps, func) in relations:

        (pdes, pfuncs) = rels[item[_root_len:]]
        pdes.update([d[_root_len:] for d in deps])
        pfuncs.add(func)

    ## Gather all paths and remove self-dependencies.
    #
    all_paths = set()
    for (path, (deps, _)) in rels.items():
        deps.discard(path)
        all_paths.update(deps)
    all_paths.update(rels.keys())


    return (rels, all_paths)


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


class FuncsExplorer:
    '''Discovers functions-relationships and produces FuncRelations (see build_web()) to inspect them.

    The name of the arguments must correlate between different functions
    '''

    def __init__(self):
        self.rels = []
        self.root = make_mock(name=_root_name)

    def harvest_func(self, func, renames=None):
        harvest_func(func, root=self.root, func_rels=self.rels, renames=renames)

    def harvest_funcs_factory(self, funcs_factory, renames=None):
        harvest_funcs_factory(funcs_factory, root=self.root, func_rels=self.rels, renames=renames)

    def add_func_rel(self, item, deps=None, func=None):
        if not deps:
            deps = []
        append_func_relation(item, deps, func, self.rels)

    def build_web(self):
        graph = build_func_dependencies_graph(self.rels, graph=FuncRelations())
        return FuncRelations(graph)



class FuncRelations(nx.DiGraph):
    def __init__(self, *args, **kws):
        nx.DiGraph.__init__(self, *args, **kws)

    def ordered(self, reverse=False):
        '''    reversed: when True, bring calculation order. otherwise, dependency-order.'''
        if reverse:
            return nx.topological_sort(self)
        else:
            return nx.topological_sort(self)


    def find_funcs_sequence(self, source, dest):
        '''Returns the functions required to calculate 'dest' from 'source' appropriately ordered.

            source: a list of nodes (existent or not) to search for all paths between them.
            dest:   a list of nodes to search for all paths between them.
        '''

        #recalc = self.ordered(True)


        try:
            for n in dest:
                deps = nx.bfs_predecessors(self, n)
                fan_in = deps.keys()
                g = self.subgraph(fan_in)
                gl = nx.topological_sort(g)
                print(n, gl)
        except (KeyError, NetworkXError) as ex:
            unknown = [d for d in dest if d not in self]
            raise ValueError('Unknown OUT-args(%s)!' % unknown) from ex
