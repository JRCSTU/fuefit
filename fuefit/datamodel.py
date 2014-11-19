#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
import io
from textwrap import dedent
from collections import OrderedDict
'''
Function for building and jsonschema-validating input and output model.
'''

from collections.abc import Mapping, Sequence 
import json

import numpy as np
from pandas.core.generic import NDFrame

import jsonschema as jsons
import operator as ops
import pandas as pd


def model_schema(additional_properties = False):
    """The json-schema for input/output of the fuefit experiment.

    :return :dict:
    """

    from textwrap import dedent

    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": model_schema.__doc__,
        "type": "object", "additionalProperties": additional_properties,
        "required": ["engine"],
        "properties": {
            "engine": {
                "oneOf": [{
                        "title": "engine series",
                        "type": "Series",
                    },
                    {
                        "title": "engine model",
                        "type": "object", "additionalProperties": additional_properties,
                        "required": ["fuel"],
                        "description": "The engine attributes and  data-points vectors required for generating a fitted fuel-map.",
                        "properties": {
                            "fuel": {
                                "title": "fuel (petrol | diesel)",
                                "enum": [ "petrol", "diesel" ],
                                "description": "the engine's fuel-type used for selecting specific-temperature and/or load-curve.",
                            },
                            "p_max": {
                                "title": "maximum rated power",
                                "$ref": "#/definitions/positiveQuantityOrNumOrNull",
                                "description": dedent("""
                                    The maximum rated engine power as declared by the manufacturer.
                                    Required if `p_norm` or `fc_norm` exists in input-file's or example-map's columns.""")
                            },
                            "n_rated": {
                                "title": "rated engine revolutions (rad/min)",
                                "$ref": "#/definitions/positiveQuantityOrNumOrNull",
                                "description": dedent("""
                                    The engine's revolutions where maximum-power is attained.
                                    Required if `n_norm` exists in input-file's or example-map columns."""),
                            },
                            "n_idle": {
                                "title": "idling revolutions (rad/min)",
                                "$ref": "#/definitions/positiveQuantityOrNumOrNull",
                                "description": dedent("""
                                    The engine's revolutions when idle.
                                    Required if `n_norm` exists in input-file's or example-map columns."""),
                            },
                            'stroke': {
                                "title": "piston stroke (mm)",
                                "$ref": "#/definitions/positiveQuantityOrNumOrNull",
                                'description': dedent("""
                                    The engine's stroke traveling distance.
                                    Required if CM is not among the inputs or requested to generate example-map with RPM column.""")
                            },
                            'capacity': {
                                "title": "engine capacity (cm^3)",
                                "$ref": "#/definitions/positiveQuantityOrNumOrNull",
                                'description': dedent("""
                                    The total displacement of all engine's pistons.
                                    This value is ignored' if `stroke`, `bore` and `cylinders` are all present.
                                    Required if `pmf` is not among the inputs or requested to generate example-map with `fc` column.""")
                            },
                            'bore': {
                                "title": "piston bore (mm)",
                                "$ref": "#/definitions/positiveQuantityOrNumOrNull",
                                'description': dedent("""
                                    The piston diameter.
                                    The `capacity` is calculated from `stroke`, `bore` and `cylinders` when are all present.""")
                            },
                            'cylinders': {
                                "title": "number of cylinders (mm)",
                                "$ref": "#/definitions/positiveIntegerOrNull",
                                'description': dedent("""
                                    The number of cyclinders in the engine.
                                    The `capacity` is calculated from `stroke`, `bore` and `cylinders` when are all present.""")
                            },
                            'fuel_lhv': {
                                "title": "Fuel's Specific Heat-Value (kjoule/kgr)",
                                "$ref": "#/definitions/positiveNumber",
                                'description': dedent("""
                                    If set, overrides any value that would be selected from `/params/fuel/XXX` based on `/engine/fuel`. """)
                            },
                            'fc_map_coeffs': {
                                "title": "Fitted coefficients",
                                "type": "Series",
                                'description': dedent("""
                                    The result of the fitting: a, b, c, a2, b2, loss0, loss2
                                    """)
                            },
                        }
                    }  #engine-props
                ]
            }, #engine
            'measured_eng_points':{
                "type": "DataFrame"
            }, #measured_eng_points
            "params": {
                "title": "Experiment parameters and constants",
                "type": "object", "additionalProperties": additional_properties,
                "required": ['fuel', 'fitting'],
                "properties": {
                        'fuel': {
                            "title": "fuel-types",
                            "type": "object", "additionalProperties": additional_properties,
                            "required": ['petrol', 'diesel'],
                            "properties": {
                                'diesel': {
                                    "title": "typical diesel params",
                                    "$ref": "#/definitions/fuel_spec",
                                },
                                'petrol': {
                                    "title": "petrol params",
                                    "$ref": "#/definitions/fuel_spec",
                                },
                            } #fuel-props
                        }, #fuel
                        'plot_maps': {
                            "title": "Plot engine-maps?",
                            "type": ["boolean", "number"],
                            "default": False,
                        },
                        'fitting': {
                            "type": "object", "additionalProperties": additional_properties,
                            "properties": {
                                'coeffs': {
                                    "title": "Fitting Coefficient parameters",
                                    "description": "See http://lmfit.github.io/lmfit-py/parameters.html#Parameter",
                                    'type': 'object', "additionalProperties": additional_properties,
                                    'properties':{
                                        'a':{"$ref": "#/definitions/fitting_param"},
                                        'b':{"$ref": "#/definitions/fitting_param"},
                                        'c':{"$ref": "#/definitions/fitting_param"},
                                        'a2':{"$ref": "#/definitions/fitting_param"},
                                        'b2':{"$ref": "#/definitions/fitting_param"},
                                        'loss0':{"$ref": "#/definitions/fitting_param"},
                                        'loss2':{"$ref": "#/definitions/fitting_param"},
                                    },
                                },
                                'is_robust': {
                                    "title": "Robust fitting?",
                                    "description": dedent("""
                                        When `robust`, outliers are excluded from the fitted-data,
                                        by using a non-linear iteratively-reweighted least-squares (IRLS) fitting-method.
                                    """),
                                    "type": ["boolean", "null"],
                                    "default": False,
                                },
                            },
                        }
                }
            },
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
            "numbers": {
                "type": "array",
               "items": { "type": "number" },
            },

            "quantity": {
                "type": "string",
                "pattern": "^\s*[-+]?\s*\d+(\.\d*)?\s*(\([^)]+\))?\s*$",
            },
            "positiveQuantity": {
                "type": "string",
                "pattern": "^\s*\+?\s*\d+(\.\d*)?\s*(\([^)]+\))?\s*$",
            },
            "negativeQuantity": {
                "type": "string",
                "pattern": "^\s*-\s*\d+(\.\d*)?\s*(\([^)]+\))?\s*$",
            },
            "positiveQuantityOrNumOrNull": {
                "oneOf": [
                    { "$ref": "#/definitions/positiveQuantity" },
                    { "$ref": "#/definitions/positiveNumber" },
                    { "type": "null" },
                ],
            },

            "fuel_spec": {
                "type": "object",
                "required": ['lhv'],
                "properties": {
                    'lhv': {'title': "Fuel's Specific Heat-Value (kjoule/kgr)", "$ref": "#/definitions/positiveInteger"}
                }
            },
            "fitting_param": {
                "type": "object",
                "properties": {
                    'value': {'type': ['null', 'number']},
                    'vary': {'type': ['null', 'boolean']},
                    'min': {'type': ['null', 'number']},
                    'max': {'type': ['null', 'number']},
                    'expr': {},
                }
            },
        }
    }

    return schema



def model_validator(additional_properties=False):
    from jsonschema import Draft4Validator
    schema = model_schema(additional_properties)
    validator = Draft4Validator(schema)
    validator._types.update({"object": (dict, pd.Series, pd.DataFrame), "DataFrame" : pd.DataFrame, 'Series':pd.Series})

    return validator

def validate_model(mdl, additional_properties=False):
    validator = model_validator(additional_properties=False)
    try:
        validator.validate(mdl)
    except jsons.ValidationError as ex:
        ## Attempt to workround BUG: https://github.com/Julian/jsonschema/issues/164
        #
        if isinstance(ex.instance, NDFrame):
            ex.instance = str(ex.instance)
        raise



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
            "n_idle":   None,
            "n_rated":  None,
            "stroke":    None,
            "capacity":    None,
            "bore":    None,
            "cylinders":    None,
        },
        'params': {
            'fuel': {
                'diesel':   {'lhv':42700},
                'petrol':   {'lhv':43000},
            },
            'fitting': {
                'is_robust':    False,
                'coeffs': OrderedDict([
                    ('a',     dict(value=0.45)),
                    ('b',     dict(value=0.0154)),
                    ('c',     dict(value=-0.00093)),
                    ('a2',    dict(value=-0.0027)),
                    ('b2',    dict(value=0)),
                    ('loss0', dict(value=-2.17)),
                    ('loss2', dict(value=-0.0037)),
                ]), 
            },
            'plot_maps':        False,
        }
    }

    return instance


def make_json_defaulter(pd_method):
    def defaulter(o):
        if (isinstance(o, NDFrame)):
            if pd_method is None:
                s = json.loads(pd.DataFrame.to_json(o))
            else:
                method = ops.methodcaller(pd_method)
                s = '%s:%s'%(type(o).__name__, method(o))
        else:
            s =repr(o)
        return s

    return defaulter

def json_dumps(obj, pd_method=None):
    return json.dumps(obj, indent=2, default=make_json_defaulter(pd_method))
def json_dump(obj, fp, pd_method=None):
    json.dump(obj, fp, indent=2, default=make_json_defaulter(pd_method))


try:
    from enum import Enum       # @UnresolvedImport @UnusedImport
except:
    from enum34 import Enum     # @UnresolvedImport @UnusedImport @Reimport

class MergeMode(Enum):
    REPLACE       = 1
    APPEND_HEAD   = 2
    APPEND_TAIL   = 3
    OVERLAP_HEAD  = 4
    OVERLAP_TAIL  = 5


def islist(obj):
    return isinstance(obj, Sequence) and not isinstance(obj, str)

def merge(a, b, path=[], list_merge_mode = MergeMode.REPLACE, raise_struct_mismatches = False):
    ''''Merges b into a.

    List merge modes: REPLACE, APPEND_HEAD, APPEND_TAIL, OVERLAP_HEAD, OVERLAP_TAIL
    '''

    def issue_struct_mismatch(mismatch_type, key, a_value, b_value):
        raise ValueError("%s-values conflict at '%s'! a(%s) != b(%s)" %
                                (mismatch_type, '/'.join(path + [str(key)]), type(av), type(bv)))

    for key in b:
        bv = b[key]
        if key in a:
            av = a[key]
            if av == bv:
                continue # same leaf value

            if raise_struct_mismatches:
                if isinstance(av, Mapping) != isinstance(bv, Mapping):
                    issue_struct_mismatch('Dict', key, av, bv)
                elif islist(av) != islist(bv):
                    issue_struct_mismatch('List', key, av, bv)

            if isinstance(av, Mapping):
                merge(av, bv, path + [str(key)])
                continue

            if islist(av) and list_merge_mode > MergeMode.REPLACE:
                # TODO: merge/append lists
                #continue
                pass

        a[key] = bv
    return a

# works
# print(merge({1:{"a":"A"},2:{"b":"B"}}, {2:{"c":"C"},3:{"d":"D"}}))
# # has conflict
# merge({1:{"a":"A"},2:{"b":"B"}}, {1:{"a":"A"},2:{"b":"C"}})



class JsonPointerException(Exception):
    pass


def jsonpointer_parts(jsonpointer):
    """
    Iterates over the ``jsonpointer`` parts.

    :param str jsonpointer: a jsonpointer to resolve within document
    :return: a generator over the parts of the json-pointer

    :author: Julian Berman, ankostis
    """

    if jsonpointer:
        parts = jsonpointer.split(u"/")
        if parts.pop(0) != '':
            raise JsonPointerException('Location must starts with /')
    
        for part in parts:
            part = part.replace(u"~1", u"/").replace(u"~0", u"~")
    
            yield part

_scream = object()
def resolve_jsonpointer(doc, jsonpointer, default=_scream):
    """
    Resolve a ``jsonpointer`` within the referenced ``doc``.
    
    :param doc: the referrant document
    :param str jsonpointer: a jsonpointer to resolve within document
    :return: the resolved doc-item or raises :class:`JsonPointerException` 

    :author: Julian Berman, ankostis
    """
    for part in jsonpointer_parts(jsonpointer):
        if isinstance(doc, Sequence):
            # Array indexes should be turned into integers
            try:
                part = int(part)
            except ValueError:
                pass
        try:
            doc = doc[part]
        except (TypeError, LookupError):
            if default is _scream:
                raise JsonPointerException(
                    "Unresolvable JSON pointer(%r)@(%s)" % (jsonpointer, part)
                )
            else:
                return default
        
    return doc

        
def set_jsonpointer(doc, jsonpointer, value, object_factory=dict):
    """
    Resolve a ``jsonpointer`` within the referenced ``doc``.
    
    :param doc: the referrant document
    :param str jsonpointer: a jsonpointer to the node to modify 
    :raises: JsonPointerException (if jsonpointer empty, missing, invalid-contet)
    """
    
    
    parts = list(jsonpointer_parts(jsonpointer))
        
    ## Will scream if used on 1st iteration.
    #
    pdoc = None
    ppart = None
    for i, part in enumerate(parts):
        if isinstance(doc, Sequence) and not isinstance(doc, str):
            ## Array indexes should be turned into integers
            #
            doclen = len(doc)
            if part == '-':
                part = doclen
            else:
                try:
                    part = int(part)
                except ValueError:
                    raise JsonPointerException("Expected numeric index(%s) for sequence at (%r)[%i]" % (part, jsonpointer, i))
                else:
                    if part > doclen:
                        raise JsonPointerException("Index(%s) out of bounds(%i) of (%r)[%i]" % (part, doclen, jsonpointer, i))
        try:
            ndoc = doc[part]
        except (LookupError):
            break  ## Branch-extension needed.
        except (TypeError): # Maybe indexing a string...
            ndoc = object_factory()
            pdoc[ppart] = ndoc
            doc = ndoc
            break  ## Branch-extension needed.
    
        doc, pdoc, ppart = ndoc, doc, part 
    else:
        doc = pdoc # If loop exhausted, cancel last assignment.

    ## Build branch with value-leaf.
    #
    nbranch = value
    for part2 in reversed(parts[i+1:]):
        ndoc = object_factory()
        ndoc[part2] = nbranch
        nbranch = ndoc
        
    ## Attach new-branch. 
    try:
        doc[part] = nbranch
    except IndexError: # Inserting last sequence-element raises IndexError("list assignment index out of range")
        doc.append(nbranch)
    
#    except (IndexError, TypeError) as ex:
#        #if isinstance(ex, IndexError) or 'list indices must be integers' in str(ex):
#        raise JsonPointerException("Incompatible content of JSON pointer(%r)@(%s)" % (jsonpointer, part))
#        else:
#            doc = {}
#            parent_doc[parent_part] = doc 
#            doc[part] = value 



def ensure_modelpath_Series(mdl, json_path):
    part = resolve_jsonpointer(mdl, json_path, None)
    if not isinstance(part, pd.Series):
        part = pd.Series(part)
        set_jsonpointer(mdl, json_path, part)

def ensure_modelpath_DataFrame(mdl, json_path):
    part = resolve_jsonpointer(mdl, json_path, None)
    if not isinstance(part, pd.Series):
        part = pd.DataFrame(part) 
        set_jsonpointer(mdl, json_path, part)



if __name__ == "__main__":
    print("Model: %s" % json.dumps(model_schema(), indent=2))

