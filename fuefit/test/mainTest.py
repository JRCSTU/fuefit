'''
Created on Apr 17, 2014

@author: ankostis
'''
import unittest
from collections import OrderedDict
import json
from .redirect import redirected

from ..main import main as fuefit_main


class Test(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self._badColumnsMsg = 'Not a COLUMN_SPEC syntax'
        self._badColumns = ['', '(dd)', 'quant((bad units))', 'quant --> ((bad units))', 'quant (complex ( units ))',
                'quant (open units']
        self._goodColumns = ['quant', 'spaced quant', 'quant (units)', 'quant (spaced units)', 'Pnorm (kJ / sec)']

        self._badPandasMsg = 'Not a KEY=VALUE syntax'
        self._badPandas = ['', 'no_value', 'spa ced', 'spaced key = key', '3number=val']
        self._goodPandas = ['k=v', ' k = v ', 'k = spaced value', 'Num_3_key = spaced value']



    def checkMainExits(self, cmdline, exit_code, **kw):
        import io

        mystdout = io.StringIO()
        mystderr = io.StringIO()
        opts = None  # @UnusedVariable
        with redirected(stdout=mystdout, stderr=mystderr, **kw):
            with self.assertRaises(SystemExit) as cm:
                opts = fuefit_main(cmdline)
            if (cm.exception.code != exit_code):
                d = OrderedDict({
                     'CMDLNE': cmdline,
                     'STDOUT': mystdout.getvalue(),
                     'STDERR': mystderr.getvalue(),
                 })
                raise AssertionError(json.dumps(d, indent=2))
        return opts, mystdout, mystderr


    def checkMainOk(self, cmdline, **kw):
        import io

        mystdout = io.StringIO()
        mystderr = io.StringIO()
        opts = None  # @UnusedVariable
        with redirected(stdout=mystdout, stderr=mystderr, **kw):
            opts = fuefit_main(cmdline)
        return opts, mystdout, mystderr


    def testHelpMsg(self):

        cmdline = 'someprog --help'
        exit_code = 0

        (opts, mystdout, mystderr) = self.checkMainExits(cmdline.split(), exit_code)

        self.assertIsNone(opts)
        self.assertFalse(mystderr.getvalue(), mystderr.getvalue())
        ## On errors, help-msg is not printed.
        self.assertTrue(mystdout.getvalue().find(fuefit_main.__doc__.splitlines()[0]) > 0, mystdout.getvalue())


    def testReqOpt(self):

        cmdline = 'some opts'
        exit_code = 2

        (opts, mystdout, mystderr) = self.checkMainExits(cmdline.split(), exit_code)

        self.assertIsNone(opts)
        self.assertFalse(mystdout.getvalue(), mystdout.getvalue())
        self.assertTrue(mystderr.getvalue().splitlines()[-1].find("the following arguments are required: -i/--ifile") > 0, mystderr.getvalue())


    def checkOpts_bad(self, opt_name, bads, badMsg):
        cmdline = '-i mainTest.py %s ' % opt_name
        exit_code = 2

        for opt in bads:
            (opts, mystdout, mystderr) = self.checkMainExits(cmdline.split() + [opt], exit_code)

            self.assertIsNone(opts)
            self.assertFalse(mystdout.getvalue(), mystdout.getvalue())
            self.assertTrue(mystderr.getvalue().splitlines()[-1].find(badMsg) > 0, mystderr.getvalue())

        ## Test multiple bads in 1 line
        self.checkMainExits(cmdline.split() + bads, exit_code)
        self.checkMainExits(cmdline.split() + bads +[opt_name] + bads, exit_code)


    def checkOpts_good(self, opt_name, goods):
        cmdline = '-i mainTest.py %s ' % opt_name

        for opt in goods:
            (opts, mystdout, mystderr) = self.checkMainOk(cmdline.split() + [opt])

            self.assertIsNone(opts)
            self.assertFalse(mystderr.getvalue(), mystderr.getvalue())

        ## Test multiple goods in 1 line
        self.checkMainOk(cmdline.split() + goods)
        self.checkMainOk(cmdline.split() + goods  +[opt_name] + goods)

    def testColumnsSpecifiers_nameBad(self):
        self.checkOpts_bad('-c', self._badColumns, self._badColumnsMsg)
    def testColumnsSpecifiers_nameGood(self):
        self.checkOpts_good('-c', self._goodColumns)

    def testColumnsSpecifiers_renameBad(self):
        self.checkOpts_bad('-r', self._badColumns, self._badColumnsMsg)
    def testColumnsSpecifiers_renameGood(self):
        self.checkOpts_good('-r', self._goodColumns)


    def testPandasOpts_inputBad(self):
        self.checkOpts_bad('-I', self._badPandas, self._badPandasMsg)
    def testPandasOpts_inputGood(self):
        self.checkOpts_good('-I', self._goodPandas)

    def testPandasOpts_outputBad(self):
        self.checkOpts_bad('-O', self._badPandas, self._badPandasMsg)
    def testPandasOpts_outputGood(self):
        self.checkOpts_good('-O', self._goodPandas)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()