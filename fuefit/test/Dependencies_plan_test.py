#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
'''
Check pdcalc's function-dependencies exploration, reporting and classes .
'''
from collections import OrderedDict
import logging
import unittest

from networkx.classes.digraph import DiGraph

import pandas as pd

from ..pdcalc import (
    DependenciesError, execute_funcs_map, execute_plan,
    Dependencies, _research_calculation_routes,
    tell_paths_from_named_args
)


def lstr(lst):
    return '\n'.join([str(e) for e in lst])

def DF(d):
    return pd.DataFrame(d)
def SR(d):
    return pd.Series(d)


def make_test_graph():
    '''     (4)  6
             ^   ^
             | X |
            (3)  5
             ^   ^
              \ /
              [2]
               ^
               |
              (1)
    '''
    web = DiGraph()
    web.add_edges_from([(1,2), (2,3), (3,4), (2,5), (3,6), (5,6), (5,4)])
    return web


def funcs_fact1(params, engine, dfin, dfout):
    from math import pi

    def f1(): engine['fuel_lhv'] = params['fuel'][engine['fuel']]['lhv']
    def f2(): dfin['n']     = dfin.n_norm * (engine.n_rated - engine.n_idle) + engine.n_idle
    def f3(): dfin['p']       = dfin.p_norm * engine.p_max
    def f4(): dfin['fc']      = dfin.fc_norm * engine.p_max
    def f5(): dfin['rps']     = dfin.n / 60
    def f6(): dfin['torque']  = (dfin.p * 1000) / (dfin.rps * 2 * pi)
    def f7(): dfin['bmep']     = (dfin.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-6)
    def f8(): dfin['pmf']     = ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-3)) * (dfin.fc / (3600 * dfin.rps * 2 * pi)) * 10e-5
    def f9(): dfin['cm']      = dfin.rps * 2 * engine.stroke / 1000
    return (f1, f2, f3, f4, f5, f6, f7, f8, f9)

def funcs_fact2(params, engine, dfin, dfout):
    ## Out of returned funcs!!
    def f10(): return dfin.cm + dfin.pmf + dfin.bmep

    def f11(): engine['eng_map_params'] = f10()
    def f12():
        dfout['n']    = engine['eng_map_params']
        dfout['p']      = engine['eng_map_params'] * 2
        dfout['fc']     = engine['eng_map_params'] * 4
    def f13(): dfout['fc_norm']         = dfout.fc / dfout.p

    return (f11, f12, f13)

def funcs_fact3(params, engine, dfin, dfout):
    def f12():
        dfout['n']    = engine['eng_map_params']
        dfout['p']      = engine['eng_map_params'] * 2
        dfout['fc']     = engine['eng_map_params'] * 4
    def f13(): dfout['fc_norm']         = dfout.fc / dfout.p

    return (f12, f13)


def func11(params, engine, dfin, dfout):
    engine['eng_map_params'] = dfin.cm + dfin.pmf + dfin.bmep



def funcs_fact(params, engine, dfin, dfout):
    return funcs_fact1(params, engine, dfin, dfout) + funcs_fact2(params, engine, dfin, dfout)

def get_params():
    return {
        'fuel': {
            'diesel':{'lhv':42700},
            'petrol':{'lhv':43000}
        },
    }

def get_engine():
    return {
        'fuel': 'diesel',
#         'measured_eng_points': '',
        'n_idle': 100,
        'n_rated' : 12,
        'p_max'     : 2,
        'capacity'  : 1300,
        'stroke'    : 12,
    }

def build_base_deps():
    deps = Dependencies()
    deps.harvest_funcs_factory(funcs_fact)

    return deps

def make_plan_and_execute(deps, dests, named_args=None, sources=None):
    if not named_args is None:
        sources = tell_paths_from_named_args(named_args)
    elif sources is None:
        raise Exception("One of `named_args`, `sources` should not be None!")

    plan = deps.build_plan(sources, dests)
    #log.info('Execution PLAN: %s', plan)
    return execute_plan(plan, *named_args.values())


def bad_func(params, engine, dfin, dfout):
    raise AssertionError('Bad func invoked!')
def bad_funcs_fact(params, engine, dfin, dfout):
    def child():
        raise AssertionError("Bad funcs_fact's child invoked!")
    return (child, )


class Test(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        l=logging.getLogger()
        l.setLevel(logging.DEBUG)
        l.handlers = [logging.StreamHandler()]



    def testSmoke_FuncExplorer_countNodes(self):
        deps = build_base_deps()
        graph = deps._build_deps_graph()
#         print("RELS:\n", lstr(deps.rels))
#         print('ORDERED:\n', lstr(plan.graph.ordered(True)))
        self.assertEqual(len(graph), 25) #29 when adding.segments

        return graph

    def test_find_connecting_nodes_smoke(self):
        deps = build_base_deps()
        graph = deps._build_deps_graph()

        inp = ('dfin.fc', 'dfin.fc_norm', 'dfin.XX')
        out = ('dfout.fc', 'dfout.n')
        (_, _, cn_nodes, _) = _research_calculation_routes(graph, inp, out)
        self.assertTrue('dfin.fc_norm' not in cn_nodes)

        #print(cn_nodes)

    def test_find_connecting_nodes_fail(self):
        deps = build_base_deps()
        graph = deps._build_deps_graph()

        inp = ('dfin.fc', 'dfin.fc_norm')
        out = ('dfout.fc', 'dfout.BAD')
        with self.assertRaisesRegex(DependenciesError, 'dfout\.BAD'):
            _research_calculation_routes(graph, inp, out)


    def test_find_connecting_nodes_good(self):
        web = make_test_graph()
        web.remove_edges_from([(5,6), (5,4)])

        inp = (1, 3, 4)
        out = (2,)
        (_, _, cn_nodes, _) = _research_calculation_routes(web, inp, out)
        all_out = {1,4,3}
        all_in = {2,5}
        self.assertTrue(cn_nodes - all_out == cn_nodes, cn_nodes)
        self.assertTrue(all_in & cn_nodes == all_in, cn_nodes)

    def test_find_connecting_nodes_good_sharedDep(self):
        web = make_test_graph()
        web.remove_edges_from([(5,4)])

        inp = (1, 3, 4)
        out = (2,)
        (_, _, cn_nodes, _) = _research_calculation_routes(web, inp, out)
        all_out = {1,4,3}
        all_in = {2,5,6}
        self.assertTrue(cn_nodes - all_out == cn_nodes, cn_nodes)
        self.assertTrue(all_in & cn_nodes == all_in, cn_nodes)

    def test_find_connecting_nodes_good_sourceDep(self):
        '''     (4)  6
                 ^   ^
                 | X |
                (3)  5
                 ^   ^
                  \ /
                  [2]
                   ^
                   |
                  (1)
        '''
        web = DiGraph()
        web.add_edges_from([(1,2), (2,3), (3,4), (2,5), (3,6), (5,6), (5,4)])

        inp = (1, 3, 4)
        out = (2,)
        (_, _, cn_nodes, _) = _research_calculation_routes(web, inp, out)
        all_out = {1,4,3}
        all_in = {2,5,6}
        self.assertTrue(cn_nodes - all_out == cn_nodes, cn_nodes)
        self.assertTrue(all_in & cn_nodes == all_in, cn_nodes)


    def testSmoke_ExecutionPlan_fail(self):
        deps = build_base_deps()

        args = {}
        inp = ('dfin.fc', 'dfin.fc_norm')
        out = ('dfout.fc', 'dfout.BAD')
        with self.assertRaisesRegex(DependenciesError, 'dfout\.BAD'):
            make_plan_and_execute(deps, out, args, inp)

    def test_tell_paths_from_named_args_dicts(self):
        d = {'arg1':{'a':1, 'b':2}, 'arg2':{11:11, 12:{13:13}}}

        paths = tell_paths_from_named_args(d)
        self.assertTrue('arg1.a' in paths, paths)
        self.assertFalse('arg1.a.1' in paths, paths)
        self.assertTrue('arg1.b' in paths, paths)
        self.assertFalse('arg1.b.2' in paths, paths)
        self.assertTrue('arg2.11' in paths, paths)
        self.assertFalse('arg2.11.2' in paths, paths)
        self.assertTrue('arg2.12.13' in paths, paths)
        self.assertFalse('arg2.12.13.13' in paths, paths)

    def test_tell_paths_from_named_args_DF(self):
        d = pd.DataFrame({'a':[1,2], 'b':[3,4]})

        paths = tell_paths_from_named_args({'arg1':d})
        self.assertTrue('arg1.a' in paths, paths)
        self.assertTrue('arg1.b' in paths, paths)
        self.assertEqual(len(paths), 2, paths)

    def test_tell_paths_from_named_args_Series(self):
        d = pd.Series({'a':[1,2], 'b':3})

        paths = tell_paths_from_named_args({'arg1':d})
        self.assertTrue('arg1.a' in paths, paths)
        self.assertTrue('arg1.b' in paths, paths)
        self.assertEqual(len(paths), 2, paths)


    def testSmoke_ExecutionPlan_good(self):
        deps = build_base_deps()

        ## TODO, Check dotted.var.names.
        engine = SR(get_engine())
        dfin = DF({'fc':[1, 2], 'fc_norm':[22, 44], 'n':[10,20], 'bmep':[100,200], 'some_foo':[1,2]})
        dfout = DF({})
        args = OrderedDict([
            ('params', SR(get_params())),
            ('engine', engine),
            ('dfin',  dfin),
            ('dfout', dfout),
        ])
        out = ('dfout.n', 'dfout.fc_norm')

        engine_c = engine.copy()
        dfin_c = dfin.copy()
        dfout_c = dfout.copy()

        make_plan_and_execute(deps, out, named_args=args)

        ## Check args modified!
        self.assertFalse(engine.equals(engine_c), engine)
        self.assertFalse(dfin.equals(dfin_c), dfin)
        self.assertFalse(dfout.equals(dfout_c), dfout)

    def testSmoke_ExecutionPlan_goodExtraRels(self):
        deps = build_base_deps()
        deps.add_func_rel('engine.fuel_lhv', ('params.fuel.diesel.lhv', 'params.fuel.petrol.lhv'))

        engine = SR(get_engine())
        dfin = DF({'fc':[1, 2], 'fc_norm':[22, 44], 'n':[10,20], 'bmep':[100,200], 'some_foo':[1,2]})
        dfout = DF({})
        args = OrderedDict([
            ('params', SR(get_params())),
            ('engine', engine),
            ('dfin',  dfin),
            ('dfout', dfout),
        ])
        out = ('dfout.n', 'dfout.fc_norm')

        engine_c = engine.copy()
        dfin_c = dfin.copy()
        dfout_c = dfout.copy()

        make_plan_and_execute(deps, out, named_args=args)

        ## Check args modified!
        self.assertFalse(engine.equals(engine_c), engine)
        self.assertFalse(dfin.equals(dfin_c), dfin)
        self.assertFalse(dfout.equals(dfout_c), dfout)


    def testSmoke_ExecutionPlan_multiFatcs_good(self):
        deps = Dependencies()
        deps.harvest_funcs_factory(funcs_fact1)
        deps.harvest_funcs_factory(funcs_fact2)
        deps.add_func_rel('engine.fuel_lhv', ('params.fuel.diesel.lhv', 'params.fuel.petrol.lhv'))

        engine = SR(get_engine())
        dfin = DF({'fc':[1, 2], 'fc_norm':[22, 44], 'n':[10,20], 'bmep':[100,200], 'some_foo':[1,2]})
        dfout = DF({})
        args = OrderedDict([
            ('params', SR(get_params())),
            ('engine', engine),
            ('dfin',  dfin),
            ('dfout', dfout),
        ])
        out = ('dfout.n', 'dfout.fc_norm')

        engine_c = engine.copy()
        dfin_c = dfin.copy()
        dfout_c = dfout.copy()

        make_plan_and_execute(deps, out, args)

        ## Check args modified!
        self.assertFalse(engine.equals(engine_c), engine)
        self.assertFalse(dfin.equals(dfin_c), dfin)
        self.assertFalse(dfout.equals(dfout_c), dfout)


    def testSmoke_funcs_map_good(self):
        params = SR(get_params())
        engine = SR(get_engine())
        dfin = DF({'fc':[1, 2], 'fc_norm':[22, 44], 'n':[10,20], 'bmep':[100,200], 'some_foo':[1,2]})
        dfout = DF({})
        out = ('dfout.n', 'dfout.fc_norm')

        engine_c = engine.copy()
        dfin_c = dfin.copy()
        dfout_c = dfout.copy()


        funcs_map = {
            funcs_fact1: True,
            funcs_fact3: True,
            func11: False,
            ('engine.fuel_lhv', ('params.fuel.diesel.lhv', 'params.fuel.petrol.lhv'), None): None,
            ('a.standalone', 'some.dep', bad_func): None,
            ('a.funcs_fact', ('one.dep', 'another.dep'), (bad_funcs_fact, 0)): None,
        }

        execute_funcs_map(funcs_map, out, params, engine, dfout=dfout, dfin=dfin)

        ## Check args modified!
        self.assertFalse(engine.equals(engine_c), engine)
        self.assertFalse(dfin.equals(dfin_c), dfin)
        self.assertFalse(dfout.equals(dfout_c), dfout)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
