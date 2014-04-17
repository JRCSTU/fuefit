'''
Created on Apr 17, 2014

@author: ankostis
'''
import unittest
from ..main import main as fuefit_main
from .redirect import redirected


class Test(unittest.TestCase):


    def testHelpMsg(self):
        import io

        cmdline = 'someprog --help'

        mystdout = io.StringIO()
        mystderr = io.StringIO()
        with redirected(stdout=mystdout, stderr=mystderr):
            with self.assertRaises(SystemExit) as cm:
                fuefit_main(cmdline.split())

            self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mystderr.getvalue(), '')
        ## On errors, help-msg is not printed.
        self.assertTrue(mystdout.getvalue().find(fuefit_main.__doc__.splitlines()[0]) > 0, )

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()