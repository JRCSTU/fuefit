#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
# Copyright 2014  ankostis@gmail.com
#
# This file is part of fuelfit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
import argparse
import pandas as pd


##############
#  Utilities
#
def str2bool(v):
    vv = v.lower()
    if (vv in ("yes", "true", "on")):
        return True
    if (vv in ("no", "false", "off")):
        return False
    try:
        return float(v)
    except:
        raise argparse.ArgumentTypeError('Invalid boolean(%s)!' % v)


def pairwise(t):
    '''From http://stackoverflow.com/questions/4628290/pairs-from-single-list'''
    it1 = iter(t)
    it2 = iter(t)
    try:
        next(it2)
    except:
        return []
    return zip(it1, it2)


def ensure_modelpath_Series(mdl, json_path):
    import jsonpointer as jsonp

    part = jsonp.resolve_pointer(mdl, json_path)
    if not isinstance(part, pd.Series):
        part = pd.Series(part)
        jsonp.set_pointer(mdl, json_path, part)

def ensure_modelpath_DataFrame(mdl, json_path):
    import jsonpointer as jsonp

    part = jsonp.resolve_pointer(mdl, json_path)
    if not isinstance(part, pd.Series):
        part = pd.DataFrame(part)
        jsonp.set_pointer(mdl, json_path, part)


## From http://stackoverflow.com/a/4149190/548792
#
class Lazy(object):
    def __init__(self,func):
        self.func=func
    def __str__(self):
        return self.func()
