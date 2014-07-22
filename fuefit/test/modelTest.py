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
'''Check validity of json-schemas themselfs.

@author: ankostis@gmail.com
@since 19 Apr 2014
'''
import jsonschema
import unittest
from .. import model


class Test(unittest.TestCase):

    @unittest.expectedFailure #Due to extra types: DataFrame, Series
    def testSchema(self):
        validator = model.model_validator()
        validator.check_schema(model.model_schema())

    def testShema_emptyInstanceFail(self):
        validator = model.model_validator()
        instance = {}

        self.assertRaises(jsonschema.ValidationError, validator.validate, instance)

    def testModelBase_fail(self):
        import jsonpointer as jsonp

        mdl = model.base_model()

        self.assertRaises(jsonschema.ValidationError, model.model_validator().validate, mdl)

        jsonp.set_pointer(mdl, '/engine/fuel', 'BAD_FUEL')
        self.assertRaisesRegex(jsonschema.ValidationError, "Failed validating 'oneOf' in schema.*properties.*engine", model.model_validator().validate, mdl)


    def testModel_FAIL_extraFuel(self):
        import jsonpointer as jsonp

        mdl = model.base_model()
        jsonp.set_pointer(mdl, '/engine/fuel', 'diesel')
        mdl['params']['fuel']['EXTRA_FUEL'] = 'somethign'

        self.assertRaisesRegex(jsonschema.ValidationError, "Additional properties .*EXTRA_FUEL", model.model_validator().validate, mdl)

    def testModel_FAIL_missLhv(self):
        import jsonpointer as jsonp

        mdl = model.base_model()
        jsonp.set_pointer(mdl, '/engine/fuel', 'diesel')
        mdl['params']['fuel']['petrol'] = {}

        self.assertRaisesRegex(jsonschema.ValidationError, "'lhv' is a required", model.model_validator().validate, mdl)


    def testModel_GOOD(self):
        import jsonpointer as jsonp

        mdl = model.base_model()
        jsonp.set_pointer(mdl, '/engine/fuel', 'diesel')

        validator = model.model_validator()
        validator.validate(mdl)

    def testModel_units_GOOD(self):
        import jsonpointer as jsonp
        from pint import UnitRegistry
        ureg = UnitRegistry()

        cases = [
            [['/engine/bore', None], 0.14 * ureg.meter],
            [['/engine/bore', 0.14], 0.14 * ureg.meter],
            [['/engine/bore', '0.14 (m)'], 0.14 * ureg.meter],
            [['/engine/bore', '+0.14 (m)'], 0.14 * ureg.meter],
            [['/engine/bore', '14 (mm)'], 0.14 * ureg.meter],
            [['/engine/bore', '14'], 0.14 * ureg.meter],
            [['/engine/bore', ' +14 '], 0.14 * ureg.meter],
        ]

        validator = model.model_validator()

        for (args, res) in cases:
            mdl = model.base_model()
            jsonp.set_pointer(mdl, '/engine/fuel', 'diesel')

            jsonp.set_pointer(mdl, *args)
            validator.validate(mdl)




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
