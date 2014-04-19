#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2013-2014 ankostis@gmail.com
#
# This file is part of wltc.
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
'''wltc module: Model json-all_schemas for WLTC gear-shift calculator.'''


def model_schema():
    """The json-schema for input/output of the fuefit experiment.

    :return :dict:
    """

    from textwrap import dedent

    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": model_schema.__doc__,
        "type": "object", "additionalProperties": False,
        "required": ["engine"],
        "properties": {
            "engine": {
                "title": "engine model",
                "type": "object", "additionalProperties": False,
                "required": ["fuel", "p_max", "rpm_idle", "rpm_rated"],
                "description": "The engine attributes and  data-points vectors required for generating a fitted fuel-map.",
                "properties": {
                    "fuel": {
                        "title": "fuel (PETROL | DIESEL)",
                        "enum": [ "PETROL", "DIESEL" ],
                        "description": "the engine's fuel-type used for selecting specific-temperature and/or load-curve.",
                    },
                    "p_max": {
                        "title": "maximum rated power",
                        "$ref": "#/definitions/positiveNumberOrNull",
                        "description": dedent("""\
                            The maximum rated engine power as declared by the manufacturer.
                            Required if Pnorm or FCnorm exists in input-file's or example-map's columns.""")
                    },
                    "rpm_rated": {
                        "title": "rated engine revolutions (rad/min)",
                        "$ref": "#/definitions/positiveNumberOrNull",
                        "description": dedent("""\
                            The engine's revolutions where maximum-power is attained.
                            Required if RPMnorm exists in input-file's or example-map columns."""),
                    },
                    "rpm_idle": {
                        "title": "idling revolutions (rad/min)",
                        "$ref": "#/definitions/positiveNumberOrNull",
                        "description": dedent("""\
                            The engine's revolutions when idle.
                            Required if RPMnorm exists in input-file's or example-map columns."""),
                    },
                    'stroke': {
                        "title": "piston stroke (mm)",
                        "$ref": "#/definitions/positiveNumberOrNull",
                        'description': dedent("""\
                            The engine's stroke travelling distance.
                            Required if CM is not among the inputs or requested to generate example-map with RPM column.""")
                    },
                    'capacity': {
                        "title": "engine capacity (cm^3)",
                        "$ref": "#/definitions/positiveNumberOrNull",
                        'description': dedent("""\
                            The total displacement of all engine's pistons.
                            This value is ignored' if 'stroke', 'bore' and 'cylinders' are all present.
                            Required if PMF is not among the inputs or requested to generate example-map with FC column.""")
                    },
                    'bore': {
                        "title": "piston bore (mm)",
                        "$ref": "#/definitions/positiveNumberOrNull",
                        'description': dedent("""\
                            The piston diameter.
                            The 'capacity' is calculated from 'stroke', 'bore' and 'cylinders' when are all present.""")
                    },
                    'cylinders': {
                        "title": "number of cylinders (mm)",
                        "$ref": "#/definitions/positiveIntegerOrNull",
                        'description': dedent("""\
                            The number of cyclinders in the engine.
                            The 'capacity' is calculated from 'stroke', 'bore' and 'cylinders' when are all present.""")
                    },
                }  #engine-props
            }, # engine
#             "params": {
#                 "title": "experiment parameters and constants",
#                 "type": "object", "additionalProperties": False,
#                 "required": [
#                 ],
#                 "properties": {
#                 }
#             },
        },
        "definitions": {
            "positiveInteger": {
                "type": "integer",
                "minimum": 0,
                "exclusiveMinimum": True,
            },
            "positiveIntegerOrNull": {
                "type": ["integer", 'null'],
                "minimum": 0,
                "exclusiveMinimum": True,
            },
            "positiveNumber": {
                "type": "number",
                "minimum": 0,
                "exclusiveMinimum": True,
            },
            "positiveNumberOrNull": {
                "type": ["number", 'null'],
                "minimum": 0,
                "exclusiveMinimum": True,
            },
            "positiveIntegers": {
                "type": "array",
               "items": { "$ref": "#/definitions/positiveInteger" },
            },
            "positiveNumbers": {
                "type": "array",
               "items": { "$ref": "#/definitions/positiveNumber" },
            },
            "mergeableArray": {
                "type": "object", "": False,
                "required": ["$merge", "$list"],
                "properties": {
                    "$merge": {
                        "enum": ["merge", "replace", "append_head", "append_tail", "overwrite_head", "overwrite_tail"],
                        "description": dedent("""\
                            merge       := appends any non-existent elements
                            replace     := (default) all items replaced
                        """),
                    },
                    "$list": {
                        "type": "array",
                    }
                },
            },
            "mergeableObject": {
                "type": "object",
                "properties": {
                    "$merge": {
                        "type": "boolean",
                        "description": dedent("""\
                            true    := (default) merge properties
                            false   := replace properties
                        """),
                    },
                },
            },
           "full_load_curve": {
               "title": "full load power curve",
               "type": "array",
               "items": [
                    {
                        "title": "normalized engine revolutions",
                        "description": dedent("""\
                            The normalized engine revolutions, within [0.0, 0.15]::
                                n_norm = (n - n_idle) / (n_rated  - n_idle) """),
                        "type": "array", "additionalItems": False,
                        "maxItems": 360,
                        "minItems": 7,
                        "items": {
                            "type": "number",
                            "minimum": 0.0,
                            "exclusiveMinimum": False,
                            "maximum": 1.5,
                            "exclusiveMaximum": False,
                        },
                    },
                    {
                        "title": "normalized full-load power curve",
                        "description": dedent("""\
                            The normalised values of the full-power load against the p_rated,
                            within [0, 1]::
                                p_norm = p / p_rated
                        """),
                        "type": "array", "additionalItems": False,
                        "maxItems": 360,
                        "minItems": 7,
                        "items": {
                           "type": "number",
                           "minimum": 0.0,
                           "exclusiveMinimum": False,
                           "maximum": 1.0,
                           "exclusiveMaximum": False,
                        }
                    },
                ],
                "description": dedent("""\
                    A 2-dimensional array holding the full load power curve in 2 rows
                    Example::
                        [
                            [ 0, 10, 20, 30, 40, 50, 60, 70. 80, 90 100, 110, 120 ],
                            [ 6.11, 21.97, 37.43, 51.05, 62.61, 72.49, 81.13, 88.7, 94.92, 98.99, 100., 96.28, 87.66 ]
                        ]

                """),
            },
        }
    }

    return schema



def model_validator():
    from jsonschema import Draft4Validator
    schema = model_schema()
    return Draft4Validator(schema)

def validate_full_load_curve(flc, f_n_max):
    if (min(flc[0]) > 0):
        raise ValueError("The full_load_curve must begin at least from 0%%, not from %f%%!" % min(flc[0]))
    max_x_limit = f_n_max
    if (max(flc[0]) < max_x_limit):
        raise ValueError("The full_load_curve must finish at least on f_n_max(%f%%), not on %f%%!" % (max_x_limit, max(flc[0])))



def base_model():
    '''The base model for running a WLTC experiment.

    It contains some default values for the experiment (ie the default 'full-load-curve' for the vehicles).
    But note that it this model is not valid - you need to override its attributes.

    :return :json_tree: with the default values for the experiment.
    '''

    instance = {
        'engine': {
            "fuel":     None,
            "p_max":  None,
            "rpm_idle":   None,
            "rpm_rated":  None,
            "stroke":    None,
            "capacity":    None,
            "bore":    None,
            "cylinders":    None,
        },
    }

    return instance

if __name__ == "__main__":
    import json
    print("Model: %s" % json.dumps(model_schema(), indent=2))

