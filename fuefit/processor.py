#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
"""
The core calculations required for transforming the Input-model to the Output one.

Uses *pandalon*'s automatic dependency extraction from calculation functions.
"""
import logging

from fuefit.model import resolve_jsonpointer
import numpy as np
import pandas as pd

from . import pdcalc, model
from collections import OrderedDict


log = logging.getLogger(__name__)


def run(mdl, opts=None):
    """
    :param mdl: the model to process, all params and data
    :param map opts: flags controlling non-functional aspects of the process (ie error-handling and logging, gui, etc)
    """

    model.ensure_modelpath_Series(mdl, '/engine')
    model.ensure_modelpath_Series(mdl, '/params')
    model.ensure_modelpath_DataFrame(mdl, '/measured_eng_points')

    params              = mdl['params']
    engine              = mdl['engine']
    measured_eng_points = mdl['measured_eng_points']

    ## Identify quantities necessary for the FITTING, 
    #    and calculate them.
    outcomes = ('eng_points.cm', 'eng_points.pme', 'eng_points.pmf', 'engine.fuel_lhv')
    pdcalc.execute_funcs_factory(eng_points_2_std_map, outcomes, params, engine, measured_eng_points)

    ## FIT
    #
    fitted_coeffs = fit_map(measured_eng_points)
    engine['fc_map_coeffs'] = fitted_coeffs

    fitted_eng_points   = reconstruct_eng_points_fitted(engine, fitted_coeffs, measured_eng_points)
    std_to_norm_map(engine, fitted_eng_points)

    if resolve_jsonpointer(mdl, '/params/plot_maps', False):
        mesh_eng_points     = generate_mesh_eng_points_fitted(measured_eng_points, fitted_coeffs, measured_eng_points)
        columns = ['pmf', 'cm', 'pme']
        plot_map(measured_eng_points, mesh_eng_points, columns)
        
        ## Flatten 2D-vectors to make a DataFrame
        #
        mesh_eng_points = {col: vec.flatten() for (col, vec) in mesh_eng_points.items()}
        mesh_eng_points = pd.DataFrame(mesh_eng_points)
        ## Fill calced columns.
        #
        std_to_norm_map(engine, mesh_eng_points)
        
        mdl['mesh_eng_points'] = pd.DataFrame(mesh_eng_points)
        

    mdl['measured_eng_points'] = measured_eng_points
    mdl['fitted_eng_points'] = pd.DataFrame(fitted_eng_points)

    #model.validate_model(mdl, additional_properties=False) TODO: Make OUT-MODEL pass validation. 
    
    return mdl


def eng_points_2_std_map(params, engine, eng_points):
    """
    A factory of the calculation functions for reaching to the data necessary for the Fitting.

    The order of the functions below not important, and the actual order of execution 
    is calculated from their dependencies, based on the data-frame's column access.
    """
    from math import pi
    
    funcs = [
        lambda: engine.__setitem__('fuel_lhv',           params['fuel'][engine.fuel]['lhv']),
        lambda: eng_points.__setitem__('n',      eng_points.n_norm * (engine.n_rated - engine.n_idle) + engine.n_idle),
        lambda: eng_points.__setitem__('p',      eng_points.p_norm * engine.p_max),
        lambda: eng_points.__setitem__('fc',     eng_points.fc_norm * engine.p_max),
        lambda: eng_points.__setitem__('rps',    eng_points.n / 60),
        #lambda: eng_points.__setitem__('rps',     eng_points.cm * 1000 / (2 * engine.stroke)),
        lambda: eng_points.__setitem__('torque', (eng_points.p * 1000) / (eng_points.rps * 2 * pi)),
        lambda: eng_points.__setitem__('pme',    (eng_points.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-6)),
        lambda: eng_points.__setitem__('pmf',    ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-6)) * (eng_points.fc / (3600 * eng_points.rps * 2 * pi)) * 10e-5),
        lambda: eng_points.__setitem__('cm',     eng_points.rps * 2 * engine.stroke / 1000),
    ]

    return funcs

def std_to_norm_map(engine, eng_points):
    from math import pi

    eng_points['rps']       = eng_points.cm * 1000 / (2 * engine.stroke)
    eng_points['n']         = eng_points.rps * 60
    eng_points['n_norm']    = eng_points.n / (engine.n_rated - engine.n_idle) + engine.n_idle
    
    eng_points['torque']    = eng_points.pme * (engine.capacity * 10e-3) / (4 * pi * 10e-5)
    eng_points['p']         = eng_points.torque * (eng_points.rps * 2 * pi) / 1000

    eng_points['fc']        = (eng_points.pmf * (engine.capacity * 10e-2) * (3600 * eng_points.rps * 2 * pi)) / (4 * pi * engine.fuel_lhv * 10e-5)
    eng_points['fc_norm']   = eng_points.fc / engine.p_max

    eng_points['p_norm']    = eng_points.p / engine.p_max



def fitfunc(X, a, b, c, a2, b2, loss0, loss2):
    pmf = X['pmf']
    cm = X['cm']
    z = (a + b*cm + c*cm**2)*pmf + (a2 + 0*b2*cm)*pmf**2 + loss0 + loss2*cm**2
    return z


def fit_map(df):
    from scipy.optimize import curve_fit as curve_fit
    #from .robustfit import curve_fit

    assert not np.any(np.isnan(df['pmf'])), \
            "Cannot fit with NaNs in `pmf` data! \n%s" % np.any(np.isnan(df['pmf']), axis=1)
    assert not np.any(np.isnan(df['cm'])), \
            "Cannot fit with NaNs in `cm` data! \n%s" % np.any(np.isnan(df['cm']), axis=1)

    param_names = ('a', 'b', 'c', 'a2', 'b2', 'loss0', 'loss2')
    p0=[0.45,0.0154,-0.00093,-0.0027,0,-2.17,-0.0037]

    Y = df.pme.values

    (res, _) = curve_fit(fitfunc, df, Y, p0=p0)#, robust=False)
    res_df = pd.Series(res, index=param_names)
    return res_df


def reconstruct_eng_points_fitted(engine, fitted_coeffs, eng_points):
    pme = fitfunc(eng_points, *fitted_coeffs)

    fitted_eng_points = pd.DataFrame.from_items(zip(['pmf', 'cm', 'pme'], (eng_points.pmf, eng_points.cm, pme)))

    return fitted_eng_points

def generate_mesh_eng_points_fitted(engine, fitted_coeffs, eng_points):
    ## Construct X.
    #
    dmin = eng_points.loc[:, ['pmf', 'cm']].min(axis=0)
    dmax = eng_points.loc[:, ['pmf', 'cm']].max(axis=0)
    drng = (dmax - dmin)
    dmin -= 0.05 * drng
    dmax += 0.10 * drng
    dstp = (dmax - dmin) / 40

    X1, X2 = np.mgrid[dmin[0]:dmax[0]:dstp[0], dmin[1]:dmax[1]:dstp[1]]

    X = {'pmf': X1, 'cm': X2}
    Y = fitfunc(X, *fitted_coeffs)


    mesh_eng_points = OrderedDict(zip(['pmf', 'cm', 'pme'], (X1, X2, Y)))

    return mesh_eng_points


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
