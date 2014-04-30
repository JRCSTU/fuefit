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
'''Check pdcalc's function-dependencies exploration, reporting and classes .

Created on Apr 23, 2014

@author: ankostis
'''
import unittest
import logging
from networkx.classes.digraph import DiGraph
import pandas as pd

from fuefit.pdcalc import FuncsExplorer, FuncRelations, research_calculation_routes, extract_funcs_from_edges,\
    tell_paths_from_args

def lstr(lst):
    return '\n'.join([str(e) for e in lst])

def DF(d):
    return pd.DataFrame(d)
def SR(d):
    return pd.Series(d)

def funcs_fact(params, engine, dfin, dfout):
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

    ## Out of returned funcs!!
    def f10(): return dfin.cm + dfin.pmf + dfin.pme

    def f11(): engine['eng_map_params'] = f10()
    def f12():
        dfout['rpm']    = engine['eng_map_params']
        dfout['p']      = engine['eng_map_params'] * 2
        dfout['fc']     = engine['eng_map_params'] * 4
    def f13(): dfout['fc_norm']         = dfout.fc / dfout.p

    return (f1, f2, f3, f4, f5, f6, f7, f8, f9, f11, f12, f13)

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

class Test(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        l=logging.getLogger()
        l.setLevel(logging.DEBUG)
        l.addHandler(logging.StreamHandler())


    def build_web(self, extra_rels=None):
        fexp = FuncsExplorer(funcs_fact)
        if extra_rels:
            fexp.add_func_rel('engine.fuel_lhv', ('params.fuel.diesel.lhv', 'params.fuel.petrol.lhv'))
        web = fexp.build_web()

        return web


    def testSmoke_FuncExplorer_countNodes(self):
        web = self.build_web()
#         print("RELS:\n", lstr(fexp.rels))
#         print('ORDERED:\n', lstr(web.graph.ordered(True)))
        self.assertEqual(len(web.graph), 25) #29 when adding.segments

        return web

    def test_find_connecting_nodes_smoke(self):
        web = self.build_web()

        inp = ('dfin.fc', 'dfin.fc_norm', 'dfin.XX')
        out = ('dfout.fc', 'dfout.rpm')
        (_, _, cn_nodes, _) = research_calculation_routes(web.graph, inp, out)
        self.assertTrue('dfin.fc_norm' not in cn_nodes)

        #print(cn_nodes)

    def test_find_connecting_nodes_fail(self):
        web = self.build_web()

        inp = ('dfin.fc', 'dfin.fc_norm')
        out = ('dfout.fc', 'dfout.BAD')
        with self.assertRaisesRegex(ValueError, 'dfout\.BAD'):
            research_calculation_routes(web.graph, inp, out)


    def test_find_connecting_nodes_good(self):
        web = DiGraph()
        web.add_edges_from([(1,2), (2,3), (3,4), (2,5), (3,6)])

        inp = (1, 3, 4)
        out = (2,)
        (_, _, cn_nodes, _) = research_calculation_routes(web, inp, out)
        all_out = {1,4,3}
        all_in = {2,5}
        self.assertTrue(cn_nodes - all_out == cn_nodes, cn_nodes)
        self.assertTrue(all_in & cn_nodes == all_in, cn_nodes)

    def test_find_connecting_nodes_good_sharedDep(self):
        web = DiGraph()
        web.add_edges_from([(1,2), (2,3), (3,4), (2,5), (3,6), (5,6)])

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


    def testSmoke_FuncRelations_fail(self):
        web = self.build_web()

        args = []
        inp = ('dfin.fc', 'dfin.fc_norm')
        out = ('dfout.fc', 'dfout.BAD')
        with self.assertRaisesRegex(ValueError, 'dfout\.BAD'):
            web.run_funcs(args, out, inp)

    def test_tell_paths_from_args_dicts(self):
        d = {'arg1':{'a':1, 'b':2}, 'arg2':{11:11, 12:{13:13}}}

        paths = tell_paths_from_args(d)
        self.assertTrue('arg1.a' in paths, paths)
        self.assertFalse('arg1.a.1' in paths, paths)
        self.assertTrue('arg1.b' in paths, paths)
        self.assertFalse('arg1.b.2' in paths, paths)
        self.assertTrue('arg2.11' in paths, paths)
        self.assertFalse('arg2.11.2' in paths, paths)
        self.assertTrue('arg2.12.13' in paths, paths)
        self.assertFalse('arg2.12.13.13' in paths, paths)

    def test_tell_paths_from_args_DF(self):
        d = pd.DataFrame({'a':[1,2], 'b':[3,4]})

        paths = tell_paths_from_args({'arg1':d})
        self.assertTrue('arg1.a' in paths, paths)
        self.assertTrue('arg1.b' in paths, paths)
        self.assertEqual(len(paths), 2, paths)

    def test_tell_paths_from_args_Series(self):
        d = pd.Series({'a':[1,2], 'b':3})

        paths = tell_paths_from_args({'arg1':d})
        self.assertTrue('arg1.a' in paths, paths)
        self.assertTrue('arg1.b' in paths, paths)
        self.assertEqual(len(paths), 2, paths)


    def testSmoke_FuncRelations_good(self):
        web = self.build_web()

        params = SR(get_params())
        engine = SR(get_engine())
        dfin =  DF({'fc':[1, 2], 'fc_norm':[22, 44], 'rpm':[10,20], 'pme':[100,200], 'some_foo':[1,2]}) # TODO: Check dotted.var.names.
        dfout = DF({})
        args = [params, engine, dfin, dfout]

        #inp = ('dfin.fc', 'dfin.fc_norm')
        #web.run_funcs(args, out, inp)
        out = ('dfout.rpm', 'dfout.fc_norm')
        web.run_funcs(args, out)

    def testSmoke_FuncRelations_goodExtraRels(self):
        web = self.build_web()

        params = SR(get_params())
        engine = SR(get_engine())
        dfin =  DF({'fc':[1, 2], 'fc_norm':[22, 44], 'rpm':[10,20], 'pme':[100,200], 'some_foo':[1,2]}) # TODO: CHeck dotted.var.names.
        dfout = DF({})
        args = [params, engine, dfin, dfout]

        #inp = ('dfin.fc', 'dfin.fc_norm')
        #web.run_funcs(args, out, inp)
        out = ('dfout.rpm', 'dfout.fc_norm')
        web.run_funcs(args, out)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
