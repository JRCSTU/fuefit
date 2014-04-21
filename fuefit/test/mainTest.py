'''
Created on Apr 17, 2014

@author: ankostis
'''
import unittest
from collections import OrderedDict
from .redirect import redirected  # @UnresolvedImport

from ..main import (main, build_args_parser, validate_file_opts, parse_key_value_pair, parse_many_file_args)
import argparse
import functools


class Test(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)

        _exit_code = None
        _exit_msg = None

        self._failColumnsMsg = 'Not a COLUMN_SPEC syntax'
        self._failColumns = ['', '(dd)', 'quant((bad units))', 'quant --> ((bad units))', 'quant (complex ( units ))',
                'quant (open units']
        self._goodColumns = ['quant', 'spaced quant', 'quant (units)', 'quant (spaced units)', 'Pnorm (kJ / sec)']

        self._failKVPairsMsg = 'Not a KEY=VALUE syntax'
        self._failKVPairs = ['no_value', 'miss_value=', 'spa ced', 'spaced key = key', '3number=val']
        self._goodKVPairs = {'k=v':'v', ' Num_3_key = 3 ':'3', 'k = spaced value ':'spaced value',
            'k+=123':123, 'k*=12.3':12.3, 'k?=1':True, 'k?=true':True, 'k?=False':False, 'k?=on':True,
            'k := 3':3, 'k := 3.14':3.14, 'k := ["a", 3.14]':['a', 3.14], 'k:={"a":3.14, "2":[1, "1"]}':{'a':3.14, '2':[1, "1"]}
        }

        self._failFormatsMsg = 'invalid choice:'
        self._failFormats = ['format=', 'format=BAD', 'format=CSV BAD']
        self._goodFormats = ['format=AUTO', 'format=CSV', 'format=XLS']


    def get_args_parser(self):
        def _exit(p, status=0, message=None):
            if message:
                self._exit_msg = message
            self._exit_code = status

#         def _error(p, message):
#             self._exit_msg = message
#             self._exit_code = 2
        parser = build_args_parser('test', 'x.x.x', 'DESC', 'EPILOG')
#         parser.exit = _exit
#         parser.error = _error

        return parser


    def check_exits(self, cmdline, exit_code):
        import io

        mystdout = io.StringIO()
        mystderr = io.StringIO()
        opts = None  # @UnusedVariable
        with redirected(stdout=mystdout, stderr=mystderr):
            with self.assertRaises(SystemExit) as cm:
                parser = self.get_args_parser()
                opts = parser.parse_args(cmdline)

            if (cm.exception.code != exit_code):
                d = OrderedDict({
                     'CMDLNE': cmdline,
                     'STDOUT': mystdout.getvalue(),
                     'STDERR': mystderr.getvalue(),
                     'OPTS': opts,
                 })
                raise AssertionError(d)
        return opts, mystdout, mystderr



    def check_ok(self, cmdline, **kw):
        import io

        mystdout = io.StringIO()
        mystderr = io.StringIO()
        opts = None  # @UnusedVariable
        with redirected(stdout=mystdout, stderr=mystderr, **kw):
            try:
                parser = self.get_args_parser()
                opts = parser.parse_args(cmdline)
            except SystemExit as ex:
                d = OrderedDict({
                     'EX': ex,
                     'CMDLNE': cmdline,
                     'STDOUT': mystdout.getvalue(),
                     'STDERR': mystderr.getvalue(),
                     'OPTS': opts,
                 })
                raise AssertionError(d)

        return opts, mystdout, mystderr


    def checkParseOpt_fail(self, cmdline, bads, badMsg, exit_code = 2):
        for opt in bads:
            (opts, mystdout, mystderr) = self.check_exits(cmdline.split() + [opt], exit_code)

            self.assertIsNone(opts)
            self.assertFalse(mystdout.getvalue(), mystdout.getvalue())
            self.assertTrue(mystderr.getvalue().splitlines()[-1].find(badMsg) > 0, mystderr.getvalue())

        ## Test multiple bads in 1 line
        self.check_exits(cmdline.split() + bads, exit_code)


    def checkParseOpt_good(self, cmdline, goods, testNArgs=True):
        for opt in goods:
            (opts, mystdout, mystderr) = self.check_ok(cmdline.split() + [opt])

            self.assertIsNotNone(opts)
            self.assertFalse(mystderr.getvalue(), mystderr.getvalue())
            self.assertFalse(mystdout.getvalue(), mystdout.getvalue())

        ## Test multiple goods in 1 line
        if testNArgs:
            self.check_ok(cmdline.split() + list(goods))


#     def test0(self):
#         main('-mfuel=DIESEL'.split())


    def testHelpMsg(self):

        cmdline = '--help'
        exit_code = 0

        (opts, mystdout, mystderr) = self.check_exits(cmdline.split(), exit_code)

        self.assertIsNone(opts)
        self.assertFalse(mystderr.getvalue(), mystderr.getvalue())
        ## On errors, help-msg is not printed.
        self.assertTrue(mystdout.getvalue().find('DESC') > 0, mystdout.getvalue())  # @UndefinedVariable


    def testModelOverrides_fail(self):
        self.checkParseOpt_fail('-m', [''] + self._failKVPairs, self._failKVPairsMsg)
    def testModelOverrides_good(self):
        self.checkParseOpt_good('-m', self._goodKVPairs.keys())

    def testColumnNames_fail(self):
        self.checkParseOpt_fail('-c', self._failColumns, self._failColumnsMsg)
    def testColumnNames_good(self):
        self.checkParseOpt_good('-c', self._goodColumns)

    def testColumnRenames_fail(self):
        self.checkParseOpt_fail('-r', self._failColumns, self._failColumnsMsg)
    def testColumnRenames_good(self):
        self.checkParseOpt_good('-r', self._goodColumns)


    def testKVPairs_fail(self):
        self._failKVPairs
        for opt in self._failKVPairs:
            self.assertRaises(argparse.ArgumentTypeError, parse_key_value_pair, opt)
    def testKVPairs_good(self):
        self._goodKVPairs
        for (arg, val) in self._goodKVPairs.items():
            (_, v) = parse_key_value_pair(arg)
            self.assertEqual(v, val, arg)

    def testFileSpec_fail(self):
        cases = [
            [['']],
            [['missing.file']],
            [['mainTest.py', 'format=BAD']],
            [['mainTest.py', 'model_path=']],
            [['mainTest.py', 'model_path=rel_path']],
            [['mainTest.py', '2_bad=key']],
        ]
        for many_file_args in cases:
            self.assertRaises(argparse.ArgumentTypeError, parse_many_file_args, many_file_args, 'r')

        self.assertRaises(argparse.ArgumentTypeError, parse_many_file_args, functools.reduce(lambda x, y: x+y, cases), 'r')

    def testFileSpec_good(self):
        cases = [
            [['mainTest.py', 'format=AUTO']],
            [['mainTest.py', 'format=CSV', 'model_path=/gjhgj']],
            [['mainTest.py', 'some=other', 'keys+=4', 'fun:=[1, {"a":2}]']],
        ]
        for many_file_args in cases:
            parse_many_file_args(many_file_args, 'r')

        argparse.ArgumentTypeError(parse_many_file_args, functools.reduce(lambda x, y: x+y, cases), 'r')


    def testNumOfFileOpts_fail(self):
        cases = [
               {'I':None, 'icolumns':[1,2], 'irenames':None},
               {'I':[1], 'icolumns':[1,2], 'irenames':None},
               {'I':[1,2], 'icolumns':[1,2,3], 'irenames':None},

               {'I':None, 'irenames':[1,2], 'icolumns':None},
               {'I':[1], 'irenames':[1,2], 'icolumns':None},
               {'I':[1,2, 3], 'irenames':[1,2], 'icolumns':None},

               {'I':None, 'irenames':[1,2], 'icolumns':[1,2]},
               {'I':None, 'irenames':[1,2], 'icolumns':[1]},
               {'I':[1], 'irenames':[1,2], 'icolumns':[1]},
               {'I':[1], 'irenames':[1,2], 'icolumns':[1,2,3]},
               {'I':[1,2], 'irenames':[1,2,3], 'icolumns':None},
               {'I':[1,2,3], 'irenames':[1,2], 'icolumns':[1,2,3,4]},
               {'I':[1,2,3], 'irenames':[1], 'icolumns':[1,2,3,4]},
       ]
        for opts in cases:
            opts = argparse.Namespace(**opts)
            self.assertRaises(argparse.ArgumentTypeError, validate_file_opts, opts)

    def testNumOfFileOpts_good(self):
        cases = [
               {'I':[1], 'icolumns':[1], 'irenames':None},
               {'I':[1,2], 'icolumns':None, 'irenames':[1,2]},
               {'I':[1,2], 'icolumns':[1,2], 'irenames':[1,2]},
               {'I':[1,2], 'icolumns':[1,2], 'irenames':[1]},
               {'I':[1,2], 'icolumns':[1], 'irenames':[1]},
       ]
        for opts in cases:
            opts = argparse.Namespace(**opts)
            validate_file_opts(opts)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()