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
import networkx as nx

from fuefit.pdcalc import build_func_dependencies_graph, harvest_func, harvest_funcs_factory, filter_common_prefixes, gen_all_prefix_pairs,\
    FuncsExplorer, FuncRelations, find_connecting_subgraph

def lstr(lst):
    return '\n'.join([str(e) for e in lst])



def funcs_fact(params, engine, df):
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

def funcs_fact2(dfin, engine, dfout):
    def f0(): return dfin.cm + dfin.pmf + dfin.pme

    def f1(): engine['eng_map_params']      = dfin.cm + dfin.pmf + dfin.pme
    def f2(): dfout['rpm','p','fc'] = engine['eng_map_params']
    def f3(): dfout['fc_norm'] = dfout.fc / dfout.p

    return (f0, f1, f2, f3)



class Test(unittest.TestCase):
    def build_web(self):
        fexp = FuncsExplorer()
        fexp.harvest_funcs_factory(funcs_fact, renames=[None, None, 'dfin'])
        fexp.harvest_funcs_factory(funcs_fact2, )
        web = fexp.build_web()

        return web


    def testSmoke_FuncExplorer_countNodes(self):
        web = self.build_web()
#         print("RELS:\n", lstr(fexp.rels))
#         print('ORDERED:\n', lstr(web.ordered(True)))
        self.assertEqual(len(web), 29)

        return web

    def testSmoke_FuncRelations_fail(self):
        web = self.build_web()

        with self.assertRaisesRegex(ValueError, 'dfout\.BAD'):
            web.find_funcs_sequence(('dfin.fc_norm', 'dfin.XX'), ('dfout.fc', 'dfout.BAD'))


    def test_find_connecting_subgraph(self):
        web = self.build_web()

        inp = ('dfin.fc', 'dfin.fc_norm', 'dfin.XX')
        out = ('dfout.fc', 'dfout.rpm')
        (g, pre_nodes) = find_connecting_subgraph(web, inp, out)

        print(inp, out)
        print(pre_nodes)
        print(nx.topological_sort(g))

        self.assertTrue('dfin.fc_norm' not in g)
        self.assertEqual(pre_nodes, nx.topological_sort_recursive(g))

        print(len(web), len(pre_nodes))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()