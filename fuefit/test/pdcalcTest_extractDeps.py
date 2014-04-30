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

from fuefit.pdcalc import build_func_dependencies_graph, harvest_func, harvest_funcs_factory, filter_common_prefixes, \
    gen_all_prefix_pairs


def lstr(lst):
    return '\n'.join([str(e) for e in lst])



def funcs_fact(params, engine, dfin):
    from math import pi

    def f1(): engine['fuel_lhv'] = params['fuel'][engine['fuel']]['lhv']
    def f2(): dfin['rpm']     = dfin.rpm_norm * (engine.rpm_rated - engine.rpm_idle) + engine.rpm_idle
    def f3(): dfin['p']       = dfin.p_norm * engine.p_max
    def f4(): dfin['fc']      = dfin.fc_norm * engine.p_max
    def f5(): dfin['rps']     = dfin.rpm / 60
    def f6(): dfin['torque']  = (dfin.p * 1000) / (dfin.rps * 2 * pi)
    def f7(): dfin['pme']     = (dfin.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-3)
    def f8(): dfin['pmf']     = ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-3)) * (dfin.fc / (3600 * dfin.rps * 2 * pi)) * 10e-5
    def f9(): dfin['cm']      = dfin.rps * 2 * engine.stroke / 1000

    return (f1, f2, f3, f4, f5, f6, f7, f8, f9)

def funcs_fact2(dfin, engine, dfout):
    def f0(): return dfin.cm + dfin.pmf + dfin.pme

    def f1(): engine['eng_map_params']      = f0()
    def f2(): dfout['rpm','p','fc'] = engine['eng_map_params']
    def f3(): dfout['fc_norm'] = dfout.fc / dfout.p

    return (f1, f2, f3)



class Test(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def test_filter_common_prefixes(self):
        filter_common_prefixes
        deps = ['a', 'a.b', 'b.cc', 'a.d', 'b', 'ac', 'a.c']
        res = filter_common_prefixes(deps)
        self.assertEqual(res, ['a.b', 'a.c', 'a.d', 'ac', 'b.cc'])

        deps = ['R.df.hh.tt', 'R.df.hh.ll', 'R.df.hh']
        res = filter_common_prefixes(deps)
        self.assertEqual(res, ['R.df.hh.ll', 'R.df.hh.tt'])

    def test_gen_all_prefix_pairs(self):
        path = 'R.foo.com'
        res = gen_all_prefix_pairs(path)
        self.assertEqual(list(res), [('R.foo', 'R'), ('R.foo.com', 'R.foo')])



    def testLambda(self):
        func = lambda df: df.hh['tt']

        deps = harvest_func(func)
        self.assertEqual(deps[0], ('R.df.hh.tt', [], func), deps)

    def testLambda_successors(self):
        func = lambda df: df.hh['tt'].ss
        deps = harvest_func(func)
        self.assertEqual(deps, [('R.df.hh.tt.ss', [], func)], deps)

        func = lambda df: df.hh['tt'].ss('some_arg')
        deps = harvest_func(func)
        self.assertEqual(deps, [('R.df.hh.tt.ss', [], func)], deps)

        func = lambda df: df.hh['tt'].ss['oo']
        deps = harvest_func(func)
        self.assertEqual(deps, [('R.df.hh.tt.ss.oo', [], func)], deps)

    def testLambda_indirectIndex(self):
        func = lambda df, params: df(params.hh['tt'])
        deps = harvest_func(func); print(deps)
        self.assertEqual(deps[0], ('R.df', [], func), deps)
        self.assertEqual(deps[1], ('R.params.hh.tt', [], func), deps)

    def testLambda_multiIndex(self):
        func = lambda df, params: df.hh[['tt','ll']] + params.tt
        deps = harvest_func(func)
        self.assertEqual(deps[0], ('R.df.hh.ll', [], func), deps)
        items = [item for (item, _, _) in deps]
        self.assertEqual(items, ['R.df.hh.ll', 'R.df.hh.tt', 'R.params.tt'], deps)

    def testLambda_sliceIndex(self):
        func = lambda df, params: df.hh['tt':'ll', 'ii']
        deps = harvest_func(func)
        self.assertEqual(deps[0], ('R.df.hh.ii', [], func), deps)
        self.assertEqual(deps[1], ('R.df.hh.ll', [], func), deps)
        self.assertEqual(deps[2], ('R.df.hh.tt', [], func), deps)
        self.assertEqual(len(deps), 3, deps)

    def testLambda_mixIndex(self):
        func = lambda df, params: df.hh['tt':'ll', 'i', params.b] + params.tt
        deps = harvest_func(func)
        items = [item for (item, _, _) in deps]
        self.assertEqual(items, ['R.df.hh.i', 'R.df.hh.ll', 'R.df.hh.tt', 'R.params.b', 'R.params.tt'], deps)

    @unittest.expectedFailure
    def testLambda_mixIndexSuccesor(self):
        func = lambda df, params: df.hh['tt':'ll', 'i', params.b]['g'] + params.tt
        deps = harvest_func(func)
        items = [item for (item, _, _) in deps]
        ## Cannot generate all combinations, but the last one!!
        self.assertEqual(items, ['R.df.hh.i.g', 'R.df.hh.ll.g', 'R.df.hh.tt.g', 'R.params.b', 'R.params.tt'], deps)


    def testFunc_sliceIndex(self):
        def func(df, params): df.hh['tt':'ll', 'ii']
        deps = harvest_func(func)
        self.assertEqual(deps[0], ('R.df.hh.ii', [], func), deps)
        self.assertEqual(deps[1], ('R.df.hh.ll', [], func), deps)
        self.assertEqual(deps[2], ('R.df.hh.tt', [], func), deps)
        self.assertEqual(len(deps), 3, deps)


    def test_harvest_funcs_factory(self):
        def func_fact(df, params):
            def f0(): df.hh['tt'].kk['ll']  = params.OO['PP'].aa
            def f1(): df.hh[['tt','ll', 'i']]    = params.tt
            def f2(): df.hh['tt':'ll', 'i']    = params.tt
            def f3(): df.hh['tt']

            return (f0, f1, f2, f3)

        deps = harvest_funcs_factory(func_fact)
#         self.assertEqual(deps[0][0], 'R.df.hh.tt.kk.ll', deps)
#         self.assertEqual(deps[0][1], 'R.params.OO.PP.aa', deps)

        self.assertEqual(deps[1][0], 'R.df.hh.tt', deps)
        self.assertEqual(deps[2][0], 'R.df.hh.ll', deps)
        self.assertEqual(deps[3][0], 'R.df.hh.i', deps)
        self.assertEqual(deps[1][1], ['R.params.tt'], deps)

        self.assertEqual(deps[4][0], 'R.df.hh.tt', deps)
        self.assertEqual(deps[5][0], 'R.df.hh.ll', deps)
        self.assertEqual(deps[6][0], 'R.df.hh.i', deps)

        self.assertEqual(deps[7][0], 'R.df.hh.tt', deps)

    @unittest.expectedFailure
    def test_harvest_lambas_factory(self):
        def func_fact(df, params):
            return [
                lambda: df.hh['tt'].kk['ll'] + params.OO['PP'].aa,
                lambda: df.hh[['tt','ll', 'i']] + params.tt,
                lambda: df.hh['tt':'ll', 'i'] + params.tt,
                lambda: df.hh['tt'],
            ]

        deps = harvest_funcs_factory(func_fact)
        self.assertEqual(deps[1][0], 'R.df.hh.tt.kk.ll', deps)
        self.assertEqual(deps[2][0], 'R.params.OO.PP.aa', deps) ## TODO: Why it fails?

        self.assertEqual(deps[1][0], 'R.df.hh.tt', deps)
        self.assertEqual(deps[2][0], 'R.df.hh.ll', deps)
        self.assertEqual(deps[3][0], 'R.df.hh.i', deps)
        self.assertEqual(deps[1][1], ['R.params.tt'], deps)

        self.assertEqual(deps[4][0], 'R.df.hh.tt', deps)
        self.assertEqual(deps[5][0], 'R.df.hh.ll', deps)
        self.assertEqual(deps[6][0], 'R.df.hh.i', deps)

        self.assertEqual(deps[7][0], 'R.df.hh.tt', deps)



    def testGatherDeps_smoke(self):
        deps = harvest_funcs_factory(funcs_fact)
        print('\n'.join([str(s) for s in deps]))


    def testGatherDepsAndBuldGraph_smoke(self):
        deps = harvest_funcs_factory(funcs_fact)
        print('\n'.join([str(s) for s in deps]))

        g = build_func_dependencies_graph(deps)
#         print(g.edge)
#         print('topological:', '\n'.join(nx.topological_sort(g)))
#         print('topological_recusrive:', '\n'.join(nx.topological_sort_recursive(g)))
#         for line in sorted(nx.generate_edgelist(g)):
#             print(line)

    def testGatherDepsAndBuldGraph_countNodes(self):
        deps = harvest_funcs_factory(funcs_fact)
        print('\n'.join([str(s) for s in deps]))

        g = build_func_dependencies_graph(deps)
        self.assertEqual(len(g), 20) #23 when adding.segments


    def build_web(self):
        rels = list()
        harvest_funcs_factory(funcs_fact, renames=[None, None, 'dfin'], func_rels=rels)
        harvest_funcs_factory(funcs_fact2, func_rels=rels)
        graph = build_func_dependencies_graph(rels)

        return graph

    def testGatherDepsAndBuldGraph_multiFuncsFacts_countNodes(self):
        import networkx as nx
        web = self.build_web()
        print("RELS:\n", lstr(web))
        print('ORDERED:\n', lstr(nx.topological_sort(web)))
        self.assertEqual(len(web), 25) #29 when adding.segments

        return web

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
