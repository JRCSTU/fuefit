'''
Created on Apr 17, 2014

@author: ankostis
'''
import unittest
from collections import OrderedDict
import json
from .redirect import redirected

from ..main import main as fuefit_main, setup_args_parser


class Test(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self._failColumnsMsg = 'Not a COLUMN_SPEC syntax'
        self._failColumns = ['', '(dd)', 'quant((bad units))', 'quant --> ((bad units))', 'quant (complex ( units ))',
                'quant (open units']
        self._goodColumns = ['quant', 'spaced quant', 'quant (units)', 'quant (spaced units)', 'Pnorm (kJ / sec)']

        self._failPandasMsg = 'Not a KEY=VALUE syntax'
        self._failPandas = ['', 'no_value', 'spa ced', 'spaced key = key', '3number=val']
        self._goodPandas = ['k=v', ' k = v ', 'k = spaced value', 'Num_3_key = spaced value']

        self._failFormatsMsg = 'invalid choice:'
        self._failFormats = [None, '', 'BAD', 'CSV BAD']
        self._goodFormats = ['AUTO', 'CSV', 'XLS']


    def test0(self):
        fuefit_main('-i mainTest.py -f TXT -f CSV -I k=v k2=kv -I k3=v3 -i test_table.csv'.split())


    def checkArgsParser_exits(self, cmdline, exit_code, **kw):
        return self.check_exits(False, cmdline, exit_code, **kw)
    def checkMain_exits(self, cmdline, exit_code, **kw):
        return self.check_exits(True, cmdline, exit_code, **kw)

    def check_exits(self, also_validate_args, cmdline, exit_code, **kw):
        import io

        mystdout = io.StringIO()
        mystderr = io.StringIO()
        opts = None  # @UnusedVariable
        with redirected(stdout=mystdout, stderr=mystderr, **kw):
            with self.assertRaises(SystemExit) as cm:
                if (also_validate_args):
                    opts = fuefit_main(cmdline)
                else:
                    parser = setup_args_parser('test_main')
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



    def checkArgsParser_ok(self, cmdline, **kw):
        return self.check_ok(False, cmdline, **kw)
    def checkMain_ok(self, cmdline, **kw):
        return self.check_ok(True, cmdline, **kw)

    def check_ok(self, also_validate_args, cmdline, **kw):
        import io

        mystdout = io.StringIO()
        mystderr = io.StringIO()
        opts = None  # @UnusedVariable
        with redirected(stdout=mystdout, stderr=mystderr, **kw):
            try:
                if (also_validate_args):
                    opts = fuefit_main(cmdline)
                else:
                    parser = setup_args_parser('test_main')
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


    def testHelpMsg(self):

        cmdline = '--help'
        exit_code = 0

        (opts, mystdout, mystderr) = self.checkArgsParser_exits(cmdline.split(), exit_code)

        self.assertIsNone(opts)
        self.assertFalse(mystderr.getvalue(), mystderr.getvalue())
        ## On errors, help-msg is not printed.
        self.assertTrue(mystdout.getvalue().find(fuefit_main.__doc__.splitlines()[0]) > 0, mystdout.getvalue())  # @UndefinedVariable


    def testReqOpt(self):

        cmdline = 'some opts'
        exit_code = 2

        (opts, mystdout, mystderr) = self.checkArgsParser_exits(cmdline.split(), exit_code)

        self.assertIsNone(opts)
        self.assertFalse(mystdout.getvalue(), mystdout.getvalue())
        self.assertTrue(mystderr.getvalue().splitlines()[-1].find("the following arguments are required: -i/--ifile") > 0, mystderr.getvalue())


    def checkParseOpt_fail(self, opt, bads, badMsg):
        cmdline = '-i mainTest.py %s ' % opt
        exit_code = 2

        for opt in bads:
            (opts, mystdout, mystderr) = self.checkArgsParser_exits(cmdline.split() + [opt], exit_code)

            self.assertIsNone(opts)
            self.assertFalse(mystdout.getvalue(), mystdout.getvalue())
            self.assertTrue(mystderr.getvalue().splitlines()[-1].find(badMsg) > 0, mystderr.getvalue())

        ## Test multiple bads in 1 line
        self.checkArgsParser_exits(cmdline.split() + bads, exit_code)
        self.checkArgsParser_exits(cmdline.split() + bads +[opt] + bads, exit_code)


    def checkParseOpt_good(self, opt, goods, testNArgs=True):
        cmdline = '-i mainTest.py %s ' % opt

        for opt in goods:
            (opts, mystdout, mystderr) = self.checkArgsParser_ok(cmdline.split() + [opt])

            self.assertIsNotNone(opts)
            self.assertFalse(mystderr.getvalue(), mystderr.getvalue())
            self.assertFalse(mystdout.getvalue(), mystdout.getvalue())

        ## Test multiple goods in 1 line
        if testNArgs:
            self.checkArgsParser_ok(cmdline.split() + goods)
            self.checkArgsParser_ok(cmdline.split() + goods  +[opt] + goods)


    def testColumnNames_fail(self):
        self.checkParseOpt_fail('-c', self._failColumns, self._failColumnsMsg)
    def testColumnNames_good(self):
        self.checkParseOpt_good('-c', self._goodColumns)

    def testColumnRenames_fail(self):
        self.checkParseOpt_fail('-r', self._failColumns, self._failColumnsMsg)
    def testColumnRenames_good(self):
        self.checkParseOpt_good('-r', self._goodColumns)


    def testPandasInputs_fail(self):
        self.checkParseOpt_fail('-I', self._failPandas, self._failPandasMsg)
    def testPandasInputs_good(self):
        self.checkParseOpt_good('-I', self._goodPandas)

    def testPandasOutputs_fail(self):
        self.checkParseOpt_fail('-O', self._failPandas, self._failPandasMsg)
    def testPandasOutputs_good(self):
        self.checkParseOpt_good('-O', self._goodPandas)

    def testIFormat_fail(self):
        self.checkParseOpt_fail('-f', self._failFormats, self._failFormatsMsg)
    def testIFormat_good(self):
        self.checkParseOpt_good('-f', self._goodFormats, testNArgs=False)

    def testOFormat_fail(self):
        self.checkParseOpt_fail('-t', self._failFormats, self._failFormatsMsg)
    def testOFormat_good(self):
        self.checkParseOpt_good('-t', self._goodFormats, testNArgs=False)


    def testNumOfFileOpts_fail(self):
        exitcode = 3
        cmdlines = [
               '-i mainTest.py -I k=v -I k=v',
               '-i mainTest.py -I k=v k2=v2 -I k=v',
               '-i mainTest.py -i mainTest.py -I k=v k2=v2 -I k=v k3=v3 -I k=v ',
               '-i mainTest.py -I k=v k2=v2 -i mainTest.py -I k=v k3=v3 -I k=v ',

               '-i mainTest.py -c col1 -c col2',
               '-i mainTest.py -c col1 -i mainTest.py -c col2 -c col3 ',

               '-i mainTest.py -c col1 -c col2',
               '-i mainTest.py -c col1 -i mainTest.py --icolumns col2 -c col3 ',

               '-i mainTest.py -f AUTO -f CSV',
               '-i mainTest.py -f TXT -i mainTest.py -f XLS --iformat CSV ',
       ]
        for cmdline in cmdlines:
            print(cmdline)
            self.checkMain_exits(cmdline.split(), exitcode)

    def testNumOfFileOpts_good(self):
        cmdlines = [
               '-i mainTest.py',
               '-i mainTest.py -I k=v',
               '-i mainTest.py -i mainTest.py -I k=v  -I k=v  ',
               '-i mainTest.py -I k=v k2=v2  -i mainTest.py -I k=v k3=v3 ',
               '-i mainTest.py -I k=v k2=v2 -i mainTest.py -I k=v k3=v3 -I k=v -i mainTest.py -i mainTest.py -I k5=5',
               '-i mainTest.py -i mainTest.py -i mainTest.py',
               '-i mainTest.py -I k=v k2=v2 -i mainTest.py -i mainTest.py',
       ]
        for cmdline in cmdlines:
            print(cmdline)
            self.checkMain_ok(cmdline.split())


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()