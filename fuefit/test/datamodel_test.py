#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
'''
Check validity of json-schemas themselves.
'''
import unittest

import jsonschema

from .. import datamodel


class Test(unittest.TestCase):

    @unittest.expectedFailure #Due to extra types: DataFrame, Series
    def testSchema(self):
        validator = datamodel.model_validator()
        validator.check_schema(datamodel.model_schema())

    def testShema_emptyInstanceFail(self):
        validator = datamodel.model_validator()
        instance = {}

        self.assertRaises(jsonschema.ValidationError, validator.validate, instance)

    def testModelBase_fail(self):
        mdl = datamodel.base_model()

        self.assertRaises(jsonschema.ValidationError, datamodel.model_validator().validate, mdl)

        datamodel.set_jsonpointer(mdl, '/engine/fuel', 'BAD_FUEL')
        self.assertRaisesRegex(jsonschema.ValidationError, "Failed validating 'oneOf' in schema.*properties.*engine", datamodel.model_validator().validate, mdl)


    def testModel_FAIL_extraFuel(self):
        mdl = datamodel.base_model()
        datamodel.set_jsonpointer(mdl, '/engine/fuel', 'diesel')
        mdl['params']['fuel']['EXTRA_FUEL'] = 'somethign'

        self.assertRaisesRegex(jsonschema.ValidationError, "Additional properties .*EXTRA_FUEL", datamodel.model_validator().validate, mdl)

    def testModel_FAIL_missLhv(self):
        mdl = datamodel.base_model()
        datamodel.set_jsonpointer(mdl, '/engine/fuel', 'diesel')
        mdl['params']['fuel']['petrol'] = {}

        self.assertRaisesRegex(jsonschema.ValidationError, "'lhv' is a required", datamodel.model_validator().validate, mdl)


    def testModel_GOOD(self):
        mdl = datamodel.base_model()
        datamodel.set_jsonpointer(mdl, '/engine/fuel', 'diesel')

        validator = datamodel.model_validator()
        validator.validate(mdl)

    def testModel_units_GOOD(self):
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

        validator = datamodel.model_validator()

        for (args, res) in cases:
            mdl = datamodel.base_model()
            datamodel.set_jsonpointer(mdl, '/engine/fuel', 'diesel')

            datamodel.set_jsonpointer(mdl, *args)
            validator.validate(mdl)




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
