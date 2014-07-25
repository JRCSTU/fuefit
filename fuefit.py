#!/usr/bin/python
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
"""The command-line entry-point for using all functionality of the tool.

Example
=======

    python fuefit \
        -I fuefit/test/FuelFit.xlsx model_path=/engine_points sheetname+=0 header@=None names:='["p","rpm","fc"]' \
        -I fuefit/test/engine.csv file_frmt=SERIES model_path=/engine header@=None \
        -m /engine/fuel=petrol \
        -O ~t1.csv model_path=/engine_points index?=false \
        -O ~t2.csv model_path=/engine_map index?=false \
        -O ~t.csv model_path= -m /params/plot_maps@=True

"""
if __name__ == "__main__":

    from fuefit import cmdline
    cmdline.main()
