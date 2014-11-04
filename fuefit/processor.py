#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl

import logging

from fuefit.model import resolve_jsonpointer
import numpy as np
import pandas as pd

from . import pdcalc
from .model import ensure_modelpath_Series, ensure_modelpath_DataFrame


log = logging.getLogger(__file__)


def run(mdl, opts=None):
    """
    :param mdl: the model to process, all params and data
    :param map opts: flags controlling non-functional aspects of the process (ie error-handling and logging, gui, etc)
    """

    ensure_modelpath_Series(mdl, '/engine')
    ensure_modelpath_Series(mdl, '/params')
    ensure_modelpath_DataFrame(mdl, '/measured_eng_points')

    params  = mdl['params']
    engine  = mdl['engine']
    dfin    = mdl['measured_eng_points']
    pdcalc.execute_funcs_factory(norm_to_std_map, ('measured_eng_points.cm', 'measured_eng_points.pme', 'measured_eng_points.pmf'), params, engine, dfin)

    fitted_params = fit_map(dfin)
    engine['fc_map_params'] = fitted_params

    (X1, X2, Y) = reconstruct_enginemap(dfin, fitted_params)

    fitted_eng_points = dict(zip(['pmf', 'cm', 'pme'], (X1, X2, Y)))

    fitted_eng_points = std_to_norm_map(params, engine, fitted_eng_points)

    if resolve_jsonpointer(mdl, '/params/plot_maps', False):
        columns = ['pmf', 'cm', 'pme']
#         columns = ['fc', 'n', 'pme']
#         columns = ['pmf', 'n', 'pme']
#         columns = ['fc_norm', 'cm', 'pme']

#         columns = ['cm', 'pme', 'pmf']
#         columns = ['n', 'pme', 'pmf', ]
#         columns = ['n', 'p', 'fc']
        plot_map(dfin, fitted_eng_points, columns)

    ## Flatten 2D-vectors to make a DataFrame
    #
    fitted_eng_points = {col: vec.flatten() for (col, vec) in fitted_eng_points.items()}
    mdl['engine_map'] = pd.DataFrame(fitted_eng_points)
    mdl['measured_eng_points'] = pd.DataFrame(dfin)

    return mdl


def norm_to_std_map(params, engine, measured_eng_points):
    from math import pi
    def f1():
        engine['fuel_lhv'] = params['fuel'][engine.fuel]['lhv']
    def f2():
        measured_eng_points['n']     = measured_eng_points.n_norm * (engine.n_rated - engine.n_idle) + engine.n_idle
    def f3():
        measured_eng_points['p']       = measured_eng_points.p_norm * engine.p_max
    def f4():
        measured_eng_points['fc']      = measured_eng_points.fc_norm * engine.p_max
    def f5():
        measured_eng_points['rps']     = measured_eng_points.n / 60
    def f6():
        measured_eng_points['torque']  = (measured_eng_points.p * 1000) / (measured_eng_points.rps * 2 * pi)
    def f7():
        measured_eng_points['pme']     = (measured_eng_points.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-6)
    def f8():
        measured_eng_points['pmf']     = ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-6)) * (measured_eng_points.fc / (3600 * measured_eng_points.rps * 2 * pi)) * 10e-5
    def f9():
        measured_eng_points['cm']      = measured_eng_points.rps * 2 * engine.stroke / 1000

    return (f1, f2, f3, f4, f5, f6, f7, f8, f9)

def std_to_norm_map(params, engine, fitted_eng_points):
    from math import pi

    fitted_eng_points['rps']       = fitted_eng_points['cm'] * 1000 / (2 * engine.stroke)
    fitted_eng_points['n']       = fitted_eng_points['rps'] * 60
    fitted_eng_points['n_norm']  = fitted_eng_points['n'] / (engine.n_rated - engine.n_idle) + engine.n_idle

    fitted_eng_points['torque']    = fitted_eng_points['pme'] * (engine.capacity * 10e-3) / (4 * pi * 10e-5)
    fitted_eng_points['p']         = fitted_eng_points['torque'] * (fitted_eng_points['rps'] * 2 * pi) / 1000

    fitted_eng_points['fc']        = (fitted_eng_points['pmf'] * (engine.capacity * 10e-2) * (3600 * fitted_eng_points['rps'] * 2 * pi)) / (4 * pi * engine.fuel_lhv * 10e-5)
    fitted_eng_points['fc_norm']   = fitted_eng_points['fc'] / engine.p_max

    fitted_eng_points['p_norm']    = fitted_eng_points['p'] / engine.p_max

    return fitted_eng_points



def fitfunc(X, a, b, c, a2, b2, loss0, loss2):
    pmf = X['pmf']
    cm = X['cm']
    assert not np.any(np.isnan(pmf)), np.any(np.isnan(pmf), axis=1)
    assert not np.any(np.isnan(cm)), np.any(np.isnan(cm), axis=1)
    z = (a + b*cm + c*cm**2)*pmf + (a2 + 0*b2*cm)*pmf**2 + loss0 + loss2*cm**2
    return z


def fit_map(df):
    from scipy.optimize import curve_fit as curve_fit
    #from .robustfit import curve_fit

    param_names = ('a', 'b', 'c', 'a2', 'b2', 'loss0', 'loss2')
    p0=[0.45,0.0154,-0.00093,-0.0027,0,-2.17,-0.0037]


    Y = df.pme.values

    (res, _) = curve_fit(fitfunc, df, Y, p0=p0)#, robust=False)
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


def plot_map(dfin, fitted_eng_points, columns):
    (X1, X2, Y) = [fitted_eng_points[col] for col in columns]

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
