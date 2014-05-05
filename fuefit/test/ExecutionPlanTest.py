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
from fuefit.pdcalc import execute, DependenciesError
'''Check pdcalc's function-dependencies exploration, reporting and classes .

Created on Apr 23, 2014

@author: ankostis
'''
import unittest
from collections import OrderedDict
import logging
from networkx.classes.digraph import DiGraph
import pandas as pd

from ..pdcalc import Dependencies, research_calculation_routes, tell_paths_from_named_args

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
    def f2(): dfin['rpm']     = dfin.rpm_norm * (engine.rpm_rated - engine.rpm_idle) + engine.rpm_idle
    def f3(): dfin['p']       = dfin.p_norm * engine.p_max
    def f4(): dfin['fc']      = dfin.fc_norm * engine.p_max
    def f5(): dfin['rps']     = dfin.rpm / 60
    def f6(): dfin['torque']  = (dfin.p * 1000) / (dfin.rps * 2 * pi)
    def f7(): dfin['pme']     = (dfin.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-6)
    def f8(): dfin['pmf']     = ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-3)) * (dfin.fc / (3600 * dfin.rps * 2 * pi)) * 10e-5
    def f9(): dfin['cm']      = dfin.rps * 2 * engine.stroke / 1000
    return (f1, f2, f3, f4, f5, f6, f7, f8, f9)

def funcs_fact2(params, engine, dfin, dfout):
    ## Out of returned funcs!!
    def f10(): return dfin.cm + dfin.pmf + dfin.pme

    def f11(): engine['eng_map_params'] = f10()
    def f12():
        dfout['rpm']    = engine['eng_map_params']
        dfout['p']      = engine['eng_map_params'] * 2
        dfout['fc']     = engine['eng_map_params'] * 4
    def f13(): dfout['fc_norm']         = dfout.fc / dfout.p

    return (f11, f12, f13)

def funcs_fact3(params, engine, dfin, dfout):
    def f12():
        dfout['rpm']    = engine['eng_map_params']
        dfout['p']      = engine['eng_map_params'] * 2
        dfout['fc']     = engine['eng_map_params'] * 4
    def f13(): dfout['fc_norm']         = dfout.fc / dfout.p

    return (f12, f13)


def func11(params, engine, dfin, dfout):
    engine['eng_map_params'] = dfin.cm + dfin.pmf + dfin.pme



def funcs_fact(params, engine, dfin, dfout):
    return funcs_fact1(params, engine, dfin, dfout) + funcs_fact2(params, engine, dfin, dfout)

def get_params():
    return {
        'fuel': {'diesel':{'lhv':42700}, }, 'petrol':{'lhv':43000}
    }

def get_engine():
    return {
        'fuel': 'diesel',
#         'engine_points': '',
        'rpm_idle': 100,
        'rpm_rated' : 12,
        'p_max'     : 2,
        'capacity'  : 1300,
        'stroke'    : 12,
    }

def build_base_deps():
    deps = Dependencies()
    deps.harvest_funcs_factory(funcs_fact)

    return deps

def make_plan_and_execute(planner, dests, named_args, sources=None):
    plan = planner.build_plan(dests, named_args, sources=sources)
    #log.info('Execution PLAN: %s', plan)
    return planner.execute_plan(plan, *named_args.values())


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
        plan = deps.build_planner()
#         print("RELS:\n", lstr(deps.rels))
#         print('ORDERED:\n', lstr(plan.graph.ordered(True)))
        self.assertEqual(len(plan.graph), 25) #29 when adding.segments

        return plan

    def test_find_connecting_nodes_smoke(self):
        deps = build_base_deps()
        plan = deps.build_planner()

        inp = ('dfin.fc', 'dfin.fc_norm', 'dfin.XX')
        out = ('dfout.fc', 'dfout.rpm')
        (_, _, cn_nodes, _) = research_calculation_routes(plan.graph, inp, out)
        self.assertTrue('dfin.fc_norm' not in cn_nodes)

        #print(cn_nodes)

    def test_find_connecting_nodes_fail(self):
        deps = build_base_deps()
        plan = deps.build_planner()

        inp = ('dfin.fc', 'dfin.fc_norm')
        out = ('dfout.fc', 'dfout.BAD')
        with self.assertRaisesRegex(DependenciesError, 'dfout\.BAD'):
            research_calculation_routes(plan.graph, inp, out)


    def test_find_connecting_nodes_good(self):
        web = make_test_graph()
        web.remove_edges_from([(5,6), (5,4)])

        inp = (1, 3, 4)
        out = (2,)
        (_, _, cn_nodes, _) = research_calculation_routes(web, inp, out)
        all_out = {1,4,3}
        all_in = {2,5}
        self.assertTrue(cn_nodes - all_out == cn_nodes, cn_nodes)
        self.assertTrue(all_in & cn_nodes == all_in, cn_nodes)

    def test_find_connecting_nodes_good_sharedDep(self):
        web = make_test_graph()
        web.remove_edges_from([(5,4)])

        inp = (1, 3, 4)
        out = (2,)
        (_, _, cn_nodes, _) = research_calculation_routes(web, inp, out)
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
        (_, _, cn_nodes, _) = research_calculation_routes(web, inp, out)
        all_out = {1,4,3}
        all_in = {2,5,6}
        self.assertTrue(cn_nodes - all_out == cn_nodes, cn_nodes)
        self.assertTrue(all_in & cn_nodes == all_in, cn_nodes)


    def testSmoke_ExecutionPlan_fail(self):
        deps = build_base_deps()
        plan = deps.build_planner()

        args = {}
        inp = ('dfin.fc', 'dfin.fc_norm')
        out = ('dfout.fc', 'dfout.BAD')
        with self.assertRaisesRegex(DependenciesError, 'dfout\.BAD'):
            make_plan_and_execute(plan, out, args, inp)

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
        plan = deps.build_planner()

        ## TODO, Check dotted.var.names.
        engine = SR(get_engine())
        dfin = DF({'fc':[1, 2], 'fc_norm':[22, 44], 'rpm':[10,20], 'pme':[100,200], 'some_foo':[1,2]})
        dfout = DF({})
        args = OrderedDict([
            ('params', SR(get_params())),
            ('engine', engine),
            ('dfin',  dfin),
            ('dfout', dfout),
        ])
        out = ('dfout.rpm', 'dfout.fc_norm')

        engine_c = engine.copy()
        dfin_c = dfin.copy()
        dfout_c = dfout.copy()

        make_plan_and_execute(plan, out, args)

        ## Check args modified!
        self.assertFalse(engine.equals(engine_c), engine)
        self.assertFalse(dfin.equals(dfin_c), dfin)
        self.assertFalse(dfout.equals(dfout_c), dfout)

    def testSmoke_ExecutionPlan_goodExtraRels(self):
        deps = build_base_deps()
        deps.add_func_rel('engine.fuel_lhv', ('params.fuel.diesel.lhv', 'params.fuel.petrol.lhv'))
        plan = deps.build_planner()

        engine = SR(get_engine())
        dfin = DF({'fc':[1, 2], 'fc_norm':[22, 44], 'rpm':[10,20], 'pme':[100,200], 'some_foo':[1,2]})
        dfout = DF({})
        args = OrderedDict([
            ('params', SR(get_params())),
            ('engine', engine),
            ('dfin',  dfin),
            ('dfout', dfout),
        ])
        out = ('dfout.rpm', 'dfout.fc_norm')

        engine_c = engine.copy()
        dfin_c = dfin.copy()
        dfout_c = dfout.copy()

        make_plan_and_execute(plan, out, args)

        ## Check args modified!
        self.assertFalse(engine.equals(engine_c), engine)
        self.assertFalse(dfin.equals(dfin_c), dfin)
        self.assertFalse(dfout.equals(dfout_c), dfout)


    def testSmoke_ExecutionPlan_multiFatcs_good(self):
        deps = Dependencies()
        deps.harvest_funcs_factory(funcs_fact1)
        deps.harvest_funcs_factory(funcs_fact2)
        deps.add_func_rel('engine.fuel_lhv', ('params.fuel.diesel.lhv', 'params.fuel.petrol.lhv'))
        plan = deps.build_planner()

        engine = SR(get_engine())
        dfin = DF({'fc':[1, 2], 'fc_norm':[22, 44], 'rpm':[10,20], 'pme':[100,200], 'some_foo':[1,2]})
        dfout = DF({})
        args = OrderedDict([
            ('params', SR(get_params())),
            ('engine', engine),
            ('dfin',  dfin),
            ('dfout', dfout),
        ])
        out = ('dfout.rpm', 'dfout.fc_norm')

        engine_c = engine.copy()
        dfin_c = dfin.copy()
        dfout_c = dfout.copy()

        make_plan_and_execute(plan, out, args)

        ## Check args modified!
        self.assertFalse(engine.equals(engine_c), engine)
        self.assertFalse(dfin.equals(dfin_c), dfin)
        self.assertFalse(dfout.equals(dfout_c), dfout)


    def testSmoke_funcs_map_good(self):
        params = SR(get_params())
        engine = SR(get_engine())
        dfin = DF({'fc':[1, 2], 'fc_norm':[22, 44], 'rpm':[10,20], 'pme':[100,200], 'some_foo':[1,2]})
        dfout = DF({})
        out = ('dfout.rpm', 'dfout.fc_norm')

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

        execute(funcs_map, out, params, engine, dfout=dfout, dfin=dfin)

        ## Check args modified!
        self.assertFalse(engine.equals(engine_c), engine)
        self.assertFalse(dfin.equals(dfin_c), dfin)
        self.assertFalse(dfout.equals(dfout_c), dfout)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
