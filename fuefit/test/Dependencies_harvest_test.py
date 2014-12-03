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
import logging
import unittest

import itertools as it

from ..pdcalc import _build_func_dependencies_graph, harvest_func, harvest_funcs_factory, _filter_common_prefixes, \
    Dependencies, DependenciesError, _validate_func_relations


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


def lstr(lst):
    return '\n'.join([str(e) for e in lst])



def funcs_fact(params, engine, dfin):
    from math import pi

    def f1(): engine['fuel_lhv'] = params['fuel'][engine['fuel']]['lhv']
    def f2(): dfin['n']     = dfin.n_norm * (engine.n_rated - engine.n_idle) + engine.n_idle
    def f3(): dfin['p']       = dfin.p_norm * engine.p_max
    def f4(): dfin['fc']      = dfin.fc_norm * engine.p_max
    def f5(): dfin['rps']     = dfin.n / 60
    def f6(): dfin['torque']  = (dfin.p * 1000) / (dfin.rps * 2 * pi)
    def f7(): dfin['bmep']    = (dfin.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-6)
    def f8(): dfin['pmf']     = ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-3)) * (dfin.fc / (3600 * dfin.rps * 2 * pi)) * 10e-5
    def f9(): dfin['cm']      = dfin.rps * 2 * engine.stroke / 1000

    return (f1, f2, f3, f4, f5, f6, f7, f8, f9)

def funcs_fact2(dfin, engine, dfout):
    def f0(): return dfin.cm + dfin.pmf + dfin.bmep

    def f1(): engine['eng_map_params']      = f0()
    def f2(): dfout['n','p','fc'] = engine['eng_map_params']
    def f3(): dfout['fc_norm'] = dfout.fc / dfout.p

    return (f1, f2, f3)



class Test(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)

    def test_filter_common_prefixes(self):
        _filter_common_prefixes
        deps = ['a', 'a.b', 'b.cc', 'a.d', 'b', 'ac', 'a.c']
        res = _filter_common_prefixes(deps)
        self.assertEqual(res, ['a.b', 'a.c', 'a.d', 'ac', 'b.cc'])

        deps = ['R.dfin.hh.tt', 'R.dfin.hh.ll', 'R.dfin.hh']
        res = _filter_common_prefixes(deps)
        self.assertEqual(res, ['R.dfin.hh.ll', 'R.dfin.hh.tt'])

    def test_gen_all_prefix_pairs(self):
        path = 'R.foo.com'
        res = gen_all_prefix_pairs(path)
        self.assertEqual(list(res), [('R.foo', 'R'), ('R.foo.com', 'R.foo')])



    def testLambda(self):
        func = lambda dfin: dfin.hh['tt']

        deps = harvest_func(func)
        self.assertEqual(deps[0][0:2], ('R.dfin.hh.tt', []), deps)

    def testLambda_successors(self):
        func = lambda dfin: dfin.hh['tt'].ss
        deps = harvest_func(func)
        self.assertEqual(deps[0][0:2], ('R.dfin.hh.tt.ss', []), deps)
        self.assertEqual(len(deps), 1, deps)

        func = lambda dfin: dfin.hh['tt'].ss('some_arg')
        deps = harvest_func(func)
        self.assertEqual(deps[0][0:2], ('R.dfin.hh.tt.ss', []), deps)
        self.assertEqual(len(deps), 1, deps)

        func = lambda dfin: dfin.hh['tt'].ss['oo']
        deps = harvest_func(func)
        self.assertEqual(deps[0][0:2], ('R.dfin.hh.tt.ss.oo', []), deps)
        self.assertEqual(len(deps), 1, deps)

    def testLambda_indirectIndex(self):
        func = lambda dfin, params: dfin(params.hh['tt'])
        deps = harvest_func(func); print(deps)
        self.assertEqual(deps[0][0:2], ('R.dfin', []), deps)
        self.assertEqual(deps[1][0:2], ('R.params.hh.tt', []), deps)

    def testLambda_multiIndex(self):
        func = lambda dfin, params: dfin.hh[['tt','ll']] + params.tt
        deps = harvest_func(func)
        self.assertEqual(deps[0][0:2], ('R.dfin.hh.ll', []), deps)
        items = [item for (item, _, _) in deps]
        self.assertEqual(items, ['R.dfin.hh.ll', 'R.dfin.hh.tt', 'R.params.tt'], deps)

    def testLambda_sliceIndex(self):
        func = lambda dfin, params: dfin.hh['tt':'ll', 'ii']
        deps = harvest_func(func)
        self.assertEqual(deps[0][0:2], ('R.dfin.hh.ii', []), deps)
        self.assertEqual(deps[1][0:2], ('R.dfin.hh.ll', []), deps)
        self.assertEqual(deps[2][0:2], ('R.dfin.hh.tt', []), deps)
        self.assertEqual(len(deps), 3, deps)

    def testLambda_mixIndex(self):
        func = lambda dfin, params: dfin.hh['tt':'ll', 'i', params.b] + params.tt
        deps = harvest_func(func)
        items = [item for (item, _, _) in deps]
        self.assertEqual(items, ['R.dfin.hh.i', 'R.dfin.hh.ll', 'R.dfin.hh.tt', 'R.params.b', 'R.params.tt'], deps)

    @unittest.expectedFailure
    def testLambda_mixIndexSuccesor(self):
        func = lambda dfin, params: dfin.hh['tt':'ll', 'i', params.b]['g'] + params.tt
        deps = harvest_func(func)
        items = [item for (item, _, _) in deps]
        ## Cannot generate all combinations, but the last one!!
        self.assertEqual(items, ['R.dfin.hh.i.g', 'R.dfin.hh.ll.g', 'R.dfin.hh.tt.g', 'R.params.b', 'R.params.tt'], deps)


    def testFunc_sliceIndex(self):
        def func(dfin, params): dfin.hh['tt':'ll', 'ii']
        deps = harvest_func(func)
        self.assertEqual(deps[0][0:2], ('R.dfin.hh.ii', []), deps)
        self.assertEqual(deps[1][0:2], ('R.dfin.hh.ll', []), deps)
        self.assertEqual(deps[2][0:2], ('R.dfin.hh.tt', []), deps)
        self.assertEqual(len(deps), 3, deps)


    def test_harvest_funcs_factory(self):
        def func_fact(dfin, params):
            def f0(): dfin.hh['tt'].kk['ll']  = params.OO['PP'].aa
            def f1(): dfin.hh[['tt','ll', 'i']]    = params.tt
            def f2(): dfin.hh['tt':'ll', 'i']    = params.tt
            def f3(): dfin.hh['tt']

            return (f0, f1, f2, f3)

        deps = harvest_funcs_factory(func_fact)
#         self.assertEqual(deps[0][0], 'R.dfin.hh.tt.kk.ll', deps)
#         self.assertEqual(deps[0][1], 'R.params.OO.PP.aa', deps)

        self.assertEqual(deps[1][0], 'R.dfin.hh.tt', deps)
        self.assertEqual(deps[2][0], 'R.dfin.hh.ll', deps)
        self.assertEqual(deps[3][0], 'R.dfin.hh.i', deps)
        self.assertEqual(deps[1][1], ['R.params.tt'], deps)

        self.assertEqual(deps[4][0], 'R.dfin.hh.tt', deps)
        self.assertEqual(deps[5][0], 'R.dfin.hh.ll', deps)
        self.assertEqual(deps[6][0], 'R.dfin.hh.i', deps)

        self.assertEqual(deps[7][0], 'R.dfin.hh.tt', deps)

    @unittest.expectedFailure
    def test_harvest_lambas_factory(self):
        def func_fact(dfin, params):
            return [
                lambda: dfin.hh['tt'].kk['ll'] + params.OO['PP'].aa,
                lambda: dfin.hh[['tt','ll', 'i']] + params.tt,
                lambda: dfin.hh['tt':'ll', 'i'] + params.tt,
                lambda: dfin.hh['tt'],
            ]

        deps = harvest_funcs_factory(func_fact)
        self.assertEqual(deps[1][0], 'R.dfin.hh.tt.kk.ll', deps)
        self.assertEqual(deps[2][0], 'R.params.OO.PP.aa', deps) ## TODO: Why it fails?

        self.assertEqual(deps[1][0], 'R.dfin.hh.tt', deps)
        self.assertEqual(deps[2][0], 'R.dfin.hh.ll', deps)
        self.assertEqual(deps[3][0], 'R.dfin.hh.i', deps)
        self.assertEqual(deps[1][1], ['R.params.tt'], deps)

        self.assertEqual(deps[4][0], 'R.dfin.hh.tt', deps)
        self.assertEqual(deps[5][0], 'R.dfin.hh.ll', deps)
        self.assertEqual(deps[6][0], 'R.dfin.hh.i', deps)

        self.assertEqual(deps[7][0], 'R.dfin.hh.tt', deps)



    def testGatherDeps_smoke(self):
        deps = harvest_funcs_factory(funcs_fact)
        print('\n'.join([str(s) for s in deps]))


    def testGatherDepsAndBuldGraph_smoke(self):
        deps = harvest_funcs_factory(funcs_fact)
        print('\n'.join([str(s) for s in deps]))

        g = _build_func_dependencies_graph(deps)
#         print(g.edge)
#         print('topological:', '\n'.join(nx.topological_sort(g)))
#         print('topological_recusrive:', '\n'.join(nx.topological_sort_recursive(g)))
#         for line in sorted(nx.generate_edgelist(g)):
#             print(line)

    def testGatherDepsAndBuldGraph_countNodes(self):
        deps = harvest_funcs_factory(funcs_fact)
        print('\n'.join([str(s) for s in deps]))

        g = _build_func_dependencies_graph(deps)
        self.assertEqual(len(g), 20) #23 when adding.segments


    def build_web(self):
        rels = list()
        harvest_funcs_factory(funcs_fact, func_rels=rels)
        harvest_funcs_factory(funcs_fact2, func_rels=rels)
        graph = _build_func_dependencies_graph(rels)

        return graph

    def testGatherDepsAndBuldGraph_multiFuncsFacts_countNodes(self):
        import networkx as nx
        web = self.build_web()
        print("RELS:\n", lstr(web))
        print('ORDERED:\n', lstr(nx.topological_sort(web)))
        self.assertEqual(len(web), 25) #29 when adding.segments

        return web



    def test_validate_func_relations_FAIL(self):
        cases = [
            (('some.item', ('a.dep', 'a.dep.other'), None), 'prefixed with root'),
            (('R.some.item', ('a.dep', 'a.dep.other'), None), 'prefixed with root'),
            (('R.some.item', ('R.a.dep', 'a.dep.other'), None), 'prefixed with root'),
            (('some.item', ('R.a.dep', 'R.a.dep.other'), None), 'prefixed with root'),

            ((('R.some.item', ), ('R.a.dep', 'R.a.dep.other'), None), 'Bad explicit func_relations'),
            ((123, ('R.a.dep', 'R.a.dep.other'), None), 'Bad explicit func_relations'),
            (('R.some.item', ('R.a.dep', ('R.a.dep.other', )), None), 'Bad explicit func_relations'),
            (('R.some.item', (123, 'R.a.dep.other'), None), 'Bad explicit func_relations'),

#             (('R.some.item', ('R.a.dep', 'R.a.dep.other'), []), 'are DepFunc instances'),
#             ((123, ('R.a.dep', 'R.a.dep.other'), (funcs_fact, -1)), 'are DepFunc instances'),
        ]
        for (i, (rel, err)) in enumerate(cases):
            with self.assertRaisesRegex(DependenciesError, err, msg='Case(%i)'%i):
                _validate_func_relations([rel])



    def test_Dependencies_FAIL(self):
        cases = [
            ((('some.item', ), ('a.dep', 'a.dep.other'), None), 'Failed adding explicit func_relation'),
            ((123, ('a.dep', 'a.dep.other'), None), 'Failed adding explicit func_relation'),
            (('some.item', ('a.dep', ('a.dep.other', )), None), 'Failed adding explicit func_relation'),
            (('some.item', (123, 'a.dep.other'), None), 'Failed adding explicit func_relation'),
        ]

        deps = Dependencies()

        for (i, (rel, err)) in enumerate(cases):
            with self.assertRaisesRegex(DependenciesError, err, msg='Case(%i)'%i):
                deps.add_func_rel(*rel)

    def test_Dependencies_GOOD(self):
        cases = [
            ('some.item', ('a.dep', 'a.dep.other'), None),
            ('R.some.item', ('a.dep', 'a.dep.other'), None),
            ('R.some.item', ('R.a.dep', 'a.dep.other'), None),
            ('some.item', ('R.a.dep', 'R.a.dep.other'), None),

            ('some.item', ('a.dep', 'a.dep.other'), None),
            ('some.item', ('a.dep', 'a.dep.other'), funcs_fact),
            ('some.item', ('a.dep', 'a.dep.other'), (funcs_fact, 1)),
        ]

        deps = Dependencies()

        for rel in cases:
            deps.add_func_rel(*rel)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
