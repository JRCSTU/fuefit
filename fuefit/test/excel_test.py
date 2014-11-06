#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
from unittest.case import skipIf
'''Check xlwings excel functionality.
'''

import unittest
import logging
import os, sys
import xlwings as xw
import pandas as pd
from pandas.util import testing as pdt
from fuefit.excel.fuefit_excel_runner import resolve_excel_ref
from pandas.core.generic import NDFrame


DEFAULT_LOG_LEVEL   = logging.INFO
def _init_logging(loglevel):
    logging.basicConfig(level=loglevel)
    logging.getLogger().setLevel(level=loglevel)

    log = logging.getLogger(__name__)
    log.trace = lambda *args, **kws: log.log(0, *args, **kws)
    
    return log
log = _init_logging(DEFAULT_LOG_LEVEL)


def from_my_path(*parts):
    return os.path.join(os.path.dirname(__file__), *parts)

class TestExcel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        log.info('CWD: %s', os.getcwd())
        excel_fname = from_my_path('..', 'excel', 'fuefit_excel_runner.xlsm' )
        wb_path = os.path.abspath(excel_fname)
        cls.workbook = xw.Workbook(wb_path)

    @skipIf(not 'darwin' in sys.platform and not 'win32' in sys.platform, "Cannot test xlwings in Linux")
    def test_excel_refs(self):
        my_pd1 = pd.DataFrame([['veh_3',  'petrol'], ['veh_4', 'diesel']])
        my_pd2 = pd.DataFrame.from_items([
                ('id',           ['veh_1', 'veh_2', 'veh_3', 'veh_4']), 
                ('/engine/fuel', ['petrol', 'diesel', 'petrol', 'diesel'])
        ])
        cases = [
            ("@d2",                         'id'),
            ("@D2",                         'id'),
            ("@D2:f2",                      pd.DataFrame(['id', '/engine/fuel', '/engine/p_max'])),
            ("@1!D2:f2",                      pd.DataFrame(['id', '/engine/fuel', '/engine/p_max'])),
            ("@1!D5:e5.vertical",           my_pd1),
            ("@Input!D2:e5.vertical(strict=True, header=True)",          my_pd2),
        ]
        
        for i, (inp, exp) in enumerate(cases):
            out = None
            try:
                out = resolve_excel_ref(inp)
                log.debug('%i: INP(%s), OUT(%s), EXP(%s)', i, inp, out, exp)
                if not exp is None:
                    if isinstance(exp, NDFrame) or isinstance(out, NDFrame):
                        pdt.assert_frame_equal(out, exp, '%i: INP(%s), OUT(%s), EXP(%s)' % (i, inp, out, exp))
                    else:
                        self.assertEqual(out, exp, '%i: INP(%s), OUT(%s), EXP(%s)' % (i, inp, out, exp))
            except Exception as ex:
                log.exception('%i: INP(%s), OUT(%s), EXP(%s), FAIL: %s' % (i, inp, out, exp, ex))
                raise
                
        
        
    @classmethod
    def tearDownClass(cls):
        try:
            cls.workbook.close()
        except Exception:
            log.warning('Minor failure while cleaning up!', exc_info=True)



if __name__ == "__main__":
    unittest.main()
