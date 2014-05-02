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
import logging
from collections import OrderedDict, defaultdict
from collections.abc import Mapping, Iterable
import itertools as it
import inspect
import networkx as nx
import pandas as pd
from networkx.exception import NetworkXError
import re
from .mymock import MagicMock
from . import DEBUG


_root_name = 'R'
_root_len = len(_root_name)+1
log = logging.getLogger(__file__)


def make_mock(*args, **kwargs):
    return MagicMock(*args, **kwargs)


def harvest_funcs_factory(funcs_factory, root=None, func_rels=None):
    if func_rels is  None:
        func_rels = []

    ## Wrap and invoke funcs_factory with "rooted" mockups as args
    #    to collect mock_calls.
    #
    funcs_factory = wrap_funcs_factory(funcs_factory)
    (root, mocks) = funcs_factory.mockup_func_args(root=root)

    cfuncs = funcs_factory(*mocks) ## The cfuncs are now wrapped children.

    ## Harvest cfunc deps as a list of 3-tuple (item, deps, funx)
    #    by inspecting root after each cfunc-call.
    #
    for cfunc in cfuncs:
        root.reset_mock()
        tmp = cfunc()
        try: tmp += 2   ## Force dependencies from return values despite compiler-optimizations.
        except:
            pass
        harvest_mock_calls(root.mock_calls, cfunc, func_rels)
    funcs_factory.reset()

    assert validate_func_relations(func_rels), func_rels
    return func_rels

def harvest_func(func, root=None, func_rels=None):
    if func_rels is None:
        func_rels = []

    func = wrap_standalone_func(func)
    (root, mocks) = func.mockup_func_args(root=root)

    tmp = func(*mocks)
    try: tmp += 2   ## Force dependencies from return values despite compiler-optimizations.
    except:
        pass
    func.reset()
    harvest_mock_calls(root.mock_calls, func, func_rels)

    assert validate_func_relations(func_rels), func_rels
    return func_rels


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
        deps = [ii for i in index for ii in harvest_indexing(i)]
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

    func_rels = consolidate_relations(func_rels)

    for (path, (deps, funcs)) in func_rels.items():
        if (deps):
            deps = filter_common_prefixes(deps)
            graph.add_edges_from([(path, dep, {'funcs': funcs}) for dep in deps])

    cycles = list(nx.simple_cycles(graph))
    if cycles:
        raise ValueError('Cyclic dependencies! %s', cycles)

    return graph


def consolidate_relations(relations):
    '''(item1, deps, func), (item1, ...) --> {item1, (set(deps), set(funcs))}'''

    rels = defaultdict()
    rels.default_factory = lambda: (set(), set()) # (deps, funcs)

    ## Join all item's  deps & funcs, and strip root-name.
    #
    for (item, deps, func) in relations:
        (pdes, pfuncs) = rels[item[_root_len:]]
        pdes.update([d[_root_len:] for d in deps])
        pfuncs.add(func)

    return rels


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


def research_calculation_routes(graph, sources, dests):
    '''Find nodes reaching 'dests' but not 'sources'.

        sources: a list of nodes (existent or not) to search for all paths originating from them
        dests:   a list of nodes to search for all paths leading to them them
        return: a 2-tuple with the graph and its nodes topologically-ordered
    '''

    ## Remove unrelated dests already present in sources.
    #
    calc_out_nodes = set(dests)
    calc_out_nodes -= set(sources)

    calc_inp_nodes = set(graph.nbunch_iter(sources))

    ## Deps graph: all INPUT's deps broken
    #    To be used for planing functions_to_run.
    #
    deps_graph = graph.copy()
    deps_graph.remove_edges_from(deps_graph.out_edges(calc_inp_nodes))

    ## Data_to_be_calced: all INPUTs erased
    #    To be used for topological-sorting.
    #
    data_graph = graph.copy()
    data_graph.remove_nodes_from(calc_inp_nodes)
    try:
        calc_nodes = set(list(calc_out_nodes) + all_predecessors(data_graph, calc_out_nodes))
    except (KeyError, NetworkXError) as ex:
        unknown = [node for node in calc_out_nodes if node not in graph]
        raise ValueError('Unknown OUT-args(%s)!' % unknown) from ex
    else:
        return (calc_inp_nodes, calc_out_nodes, calc_nodes, deps_graph)

def all_predecessors(graph, nodes):
    return [k for node in nodes for k in nx.bfs_predecessors(graph, node).keys()]


def find_calculation_order(graph, calc_nodes):
    subgraph = graph.subgraph(calc_nodes)
    ordered_calc_nodes = list(reversed(nx.topological_sort(subgraph)))

    return ordered_calc_nodes


def find_missing_input(calc_inp_nodes, graph):
    '''Search for *tentatively* missing data.'''
    calc_inp_nodes = set(calc_inp_nodes) # for efficiency below
    missing_input_nodes = []
    for node in nx.dfs_predecessors(graph):
        if ( node not in calc_inp_nodes and graph.out_degree(node) == 0):
            missing_input_nodes.append(node)
    return missing_input_nodes


def extract_funcs_from_edges(graph, ordered_nodes):
    # f=list(fs[0]['funcs'])[0]
    funcs = [f for (_, _, d) in graph.edges_iter(ordered_nodes, True) if d
            for f in d['funcs']] # a list of sets


    ## Remove duplicates whilist preserving order.
    funcs = list(OrderedDict.fromkeys(funcs))

    return funcs



def default_arg_paths_extractor(arg_name, arg, paths):
    '''Add recursively all indexes found, skipping the inner-ones (ie 'df.some.key', but not 'df' & 'df.some'.

    BUT for pandas-series, their index (their infos-axis) gets appended only the 1st time
    (not if invoked in recursion, from DataFrame columns).
    '''
    try:
        for key in arg.keys():
            path = '%s.%s'%(arg_name, key)
            value = arg[key]
            if (isinstance(value, pd.Series)):
                paths.append(path) # do not recurse into series.
            else:
                default_arg_paths_extractor(path, value, paths)
    except (AttributeError, KeyError):
        paths.append(arg_name)


def tell_paths_from_named_args(named_args, arg_paths_extractor_func=default_arg_paths_extractor, paths=None):
    '''named_args: an args-map {name: arg} as returned by inspect.signature(func).bind(*args).arguments: BoundArguments'''

    if paths is None:
        paths = []
    for (name, arg) in named_args.items():
        arg_paths_extractor_func(name, arg, paths)

    return paths



def wrap_standalone_func(func):
    return DepFunc(func=func, is_funcs_factory=False)
def wrap_funcs_factory(funcs_factory):
    return DepFunc(func=funcs_factory, is_funcs_factory=True)
class DepFunc:
    '''A wrapper for functions explored for relations, optionally allowing them to form a hierarchy of factories and produced functions.

    It can be in 3 types:
        * 0, standalone function: args given to function invocation are used immediatelt,
        * 10, functions-factory: args are stored and will be used by the child-funcs returned,
        * 20, child-func: created internally, and no args given when invoced, will use parent-factory's args.

    Use factory methods to create one of the first 2 types:
        * pdcalc.wrap_standalone_func()
        * pdcalc.wrap_funcs_factory()
    '''
    TYPES = ['standalone', 'funcs_fact', 'child']

    def __init__(self, func, is_funcs_factory=False, _child_index=None):
        self.func = func
        if is_funcs_factory:            ## Factory
            self._type = 1
            self.child_funcs = None

            assert _child_index == None, self
        elif _child_index is not None:  ## Child
            self._type = 2
            self.child_index = _child_index

            assert func.is_funcs_factory(), self
            assert _child_index >= 0 and _child_index < len(func.child_funcs)
        else:                           ## Standalone
            self._type = 0

            assert _child_index == None, self

    def get_type(self):
        return DepFunc.TYPES[self._type]

    def is_standalone_func(self):
        return self._type == 0
    def is_funcs_factory(self):
        return self._type == 1
    def is_child_func(self):
        return self._type == 2

    def reset(self):
        if self.is_funcs_factory():
            self.child_funcs = None
    def is_reset(self):
        assert self.is_funcs_factory(), self

        return self.child_funcs is not None

    def mockup_func_args(self, root=None):
        assert not self.is_child_func(), self

        if not root:
            root = make_mock(name=_root_name)

        sig = inspect.signature(self.func)
        mocks = []
        for (name, param) in sig.parameters.items():
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                log.warning('Any dependencies from **%s will be ignored for %s!', name, self)
                break
            mock = make_mock()
            mocks.append(mock)
            root.attach_mock(mock, name)
        return (root, mocks)


    def __call__(self, *args, **kwargs):
        if self.is_standalone_func():           ## Standalone
            return self.func(*args, **kwargs)

        elif self.is_funcs_factory():           ## Factory
            self.child_funcs = self.func(*args, **kwargs)
            return [DepFunc(func=self, _child_index=i) for i in range(len(self.child_funcs))]

        else:                                   ## Child
            parent_fact = self.func
            assert parent_fact.is_funcs_factory(), self

            ## Use new args only if parent has previously been reset.
            #
            if (args or kwargs) and not parent_fact.is_reset():
                parent_fact(*args, **kwargs) ## Ignore returned depfuncs, we are the children!

            cfunc = parent_fact.child_funcs[self.child_index]
            return cfunc()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        try:
            if (self.is_child_func()):
                return 'DepFunc<child>(%s, %s)'%(self.func.func, self.child_index)
            return 'DepFunc<%s>(%s)'%(self.get_type(), self.func)
        except:
            return 'DepFunc<BAD_STR>(%s)'%self.func



class Dependencies:
    '''Discovers functions-relationships and produces ExecutionPlanner (see build_planner()) to inspect them. '''

    def __init__(self):
        self.rels = []

    def add_funcs_factory(self, funcs_factory):
        root = make_mock(name=_root_name)
        harvest_funcs_factory(funcs_factory, root=root, func_rels=self.rels)
        log.debug('DEPS collected(%i): %s', len(self.rels), self.rels)

    def add_func(self, func):
        root = make_mock(name=_root_name)
        harvest_func(func, root=root, func_rels=self.rels)
        log.debug('DEPS collected(%i): %s', len(self.rels), self.rels)

    def add_func_rel(self, item, deps=None, func=None, args=None):
        '''func: a list of integers, the indices of funcs returned by the factory'''
        if deps is None:
            deps = []
        append_func_relation(item, deps, func, self.rels)

    def build_planner(self):
        graph = build_func_dependencies_graph(self.rels)
        log.debug('GRAPH constructed(%i): %s', graph.size(), graph.edges(data=True))
        return ExecutionPlanner(graph)




class ExecutionPlanner:
    '''Constructed by Dependencies.'''

    def __init__(self, graph):
        self.graph = graph

    def make_empty_plan(self):
        return pd.Series(dict(calc_inp_nodes=[], calc_out_nodes=[], calc_nodes=[],
            missing_data=[] if DEBUG else None, deps_graph=[]))

    def establish_plan(self, dests, named_args=None, sources=None, plan=None):
        '''Limit graph to all those dotted.data reaching from 'sources' to 'dests'.

            named_args: an ordered map {name: arg} as returned by inspect.signature(func).bind(*args).arguments: BoundArguments
            sources: a list of dotted.data (existent or not) to search for all dotted.data originating from them
            dests:   a list of dotted.data to search for all dotted.data leading to them them

        Example::

            args = {'dfin': df, 'dfout':some.dict}
        '''

        if plan is None:
            plan = self.make_empty_plan()
            plan.dests = dests

        if (sources is None):
            sources         = tell_paths_from_named_args(named_args)
        log.debug('EXISTING data(%i): %s', len(sources), sources)
        log.debug('REQUESTED data(%i): %s', len(dests), dests)

        (calc_inp_nodes, calc_out_nodes, unordered_calc_nodes, deps_graph) = \
                                research_calculation_routes(self.graph, sources, dests)
        plan.deps_graph     = deps_graph
        plan.calc_out_nodes = calc_out_nodes
        plan.calc_inp_nodes = calc_inp_nodes

        calc_nodes          = find_calculation_order(self.graph, unordered_calc_nodes)
        plan.calc_nodes     = calc_nodes
        plan.deps           = deps_graph.edges(calc_nodes, data=True)

        if DEBUG:
            missing_inp_nodes       = find_missing_input(calc_inp_nodes, deps_graph)
            plan.missing_inp_nodes  = missing_inp_nodes
        else:
            plan.missing_inp_nodes  = None

        funcs               = extract_funcs_from_edges(deps_graph, calc_nodes)
        plan.funcs          = funcs

        return plan


    def run_plan(self, plan, *args, **kwargs):
        results = [func(*args, **kwargs) for func in plan.funcs]
        return results


    def make_plan_and_run(self, dests, named_args, sources=None):
        plan = self.establish_plan(dests, named_args, sources=sources)
        log.info('Execution PLAN: %s', plan)
        return self.run_plan(plan, *named_args.values())

    def __str__(self):
        return "%s(nodes=%r)" % ('ExecutionPlanner', self.graph.nodes())

