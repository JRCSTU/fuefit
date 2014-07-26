#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 ankostis@gmail.com
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


import logging

import jsonpointer as jsonp
import numpy as np
import pandas as pd

from . import pdcalc
from .utils import ensure_modelpath_Series, ensure_modelpath_DataFrame


log = logging.getLogger(__file__)


def run(opts, mdl):
    """
    :param mdl: the model to process, all params and data
    :param map opts: flags controlling non-functional aspects of the process (ie error-handling and logging, gui, etc)
    """

    ensure_modelpath_Series(mdl, '/engine')
#     ensure_modelpath_Series(mdl, '/params')
    ensure_modelpath_DataFrame(mdl, '/engine_points')

    params  = mdl['params']
    engine  = mdl['engine']
    dfin    = mdl['engine_points']
    pdcalc.execute_funcs_factory(norm_to_std_map, ('df.cm', 'df.pme', 'df.pmf'), params, engine, dfin)

    fitted_params = fit_map(dfin)
    engine['fc_map_params'] = fitted_params

    (X1, X2, Y) = reconstruct_enginemap(dfin, fitted_params)

    dfout = dict(zip(['pmf', 'cm', 'pme'], (X1, X2, Y)))

    dfout = std_to_norm_map(params, engine, dfout)

    if jsonp.resolve_pointer(mdl, '/params/plot_maps', False):
        columns = ['pmf', 'cm', 'pme']
#         columns = ['fc', 'rpm', 'pme']
#         columns = ['pmf', 'rpm', 'pme']
#         columns = ['fc_norm', 'cm', 'pme']

#         columns = ['cm', 'pme', 'pmf']
#         columns = ['rpm', 'pme', 'pmf', ]
#         columns = ['rpm', 'p', 'fc']
        plot_map(dfin, dfout, columns)

    ## Flatten 2D-vectors to make a DataFrame
    #
    dfout = {col: vec.flatten() for (col, vec) in dfout.items()}
    mdl['engine_map'] = pd.DataFrame(dfout)

    return mdl


def norm_to_std_map(params, engine, df):
    from math import pi
    def f1():
        engine['fuel_lhv'] = params['fuel'][engine.fuel]['lhv']
    def f2():
        df['rpm']     = df.rpm_norm * (engine.rpm_rated - engine.rpm_idle) + engine.rpm_idle
    def f3():
        df['p']       = df.p_norm * engine.p_max
    def f4():
        df['fc']      = df.fc_norm * engine.p_max
    def f5():
        df['rps']     = df.rpm / 60
    def f6():
        df['torque']  = (df.p * 1000) / (df.rps * 2 * pi)
    def f7():
        df['pme']     = (df.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-6)
    def f8():
        df['pmf']     = ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-3)) * (df.fc / (3600 * df.rps * 2 * pi)) * 10e-5
    def f9():
        df['cm']      = df.rps * 2 * engine.stroke / 1000

    return (f1, f2, f3, f4, f5, f6, f7, f8, f9)

def std_to_norm_map(params, engine, dfout):
    from math import pi

    dfout['rps']       = dfout['cm'] * 1000 / (2 * engine.stroke)
    dfout['rpm']       = dfout['rps'] * 60
    dfout['rpm_norm']  = dfout['rpm'] / (engine.rpm_rated - engine.rpm_idle) + engine.rpm_idle

    dfout['torque']    = dfout['pme'] * (engine.capacity * 10e-3) / (4 * pi * 10e-5)
    dfout['p']         = dfout['torque'] * (dfout['rps'] * 2 * pi) / 1000

    dfout['fc']        = (dfout['pmf'] * (engine.capacity * 10e-2) * (3600 * dfout['rps'] * 2 * pi)) / (4 * pi * engine.fuel_lhv * 10e-5)
    dfout['fc_norm']   = dfout['fc'] / engine.p_max

    dfout['p_norm']    = dfout['p'] / engine.p_max

    return dfout



def fitfunc(X, a, b, c, a2, b2, loss0, loss2):
    pmf = X['pmf']
    cm = X['cm']
    assert not np.any(np.isnan(pmf)), np.any(np.isnan(pmf), axis=1)
    assert not np.any(np.isnan(cm)), np.any(np.isnan(cm), axis=1)
    z = (a + b*cm + c*cm**2)*pmf + (a2 + b2*cm)*pmf**2 + loss0 + loss2*cm**2
    return z


def fit_map(df):
    from scipy.optimize import curve_fit as curve_fit
    #from .robustfit import curve_fit

    param_names = ('a', 'b', 'c', 'a2', 'b2', 'loss0', 'loss2')

    Y = df.pme.values

    (res, _) = curve_fit(fitfunc, df, Y)#, robust=False)
    res_df = pd.Series(res, index=param_names)
    return res_df


def reconstruct_enginemap(dfin, fitted_params):
    ## Construct X.
    #
    dmin = dfin.loc[:, ['pmf', 'cm']].min(axis=0)
    dmax = dfin.loc[:, ['pmf', 'cm']].max(axis=0)
    drng = (dmax - dmin)
    dmin -= 0.05 * drng
    dmax += 0.10 * drng
    dstp = (dmax - dmin) / 40

    X1, X2 = np.mgrid[dmin[0]:dmax[0]:dstp[0], dmin[1]:dmax[1]:dstp[1]]

    X = {'pmf': X1, 'cm': X2}
    Y = fitfunc(X, *fitted_params)


    return (X1, X2, Y)


def plot_map(dfin, dfout, columns):
    (X1, X2, Y) = [dfout[col] for col in columns]

    x1min = X1.min(); x1max = X1.max();
    x2min = X2.min(); x2max = X2.max();
    extent=(x1min, x1max, x2min, x2max)
    levels = np.arange(Y.min(), Y.max(), (Y.max() - Y.min()) / 10.0)

#     import matplotlib
#     matplotlib.use('WebAgg')
    from matplotlib import pyplot as plt

    plt.plot(dfin[columns[0]], dfin[columns[1]], '.c')

    cntr = plt.contourf(X1, X2, Y, cmap=plt.cm.get_cmap(plt.cm.copper, len(levels)-1), extent=extent)  # @UndefinedVariable
    colorbar = plt.colorbar(cntr)
    colorbar.set_label(columns[2], color='blue')

    ax = plt.gca()
    ax.set_title('Fitted normalized engine_map')
    ax.set_aspect('auto'); ax.set_adjustable('box-forced')
    ax.set_xlabel(columns[0], color='red'); ax.set_ylabel(columns[1], color='green')

    plt.show()


def proc_vehicle(dfin, model):

    ## Filter values
    #
    nrows       = len(dfin)
    dfin = dfin[(dfin.pme > -1.0) & (dfin.pme < 25.0)]
    log.warning('Filtered %s out of %s rows for BAD  pme.', nrows-len(dfin), nrows)

    return dfin
