#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2014 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
"""
The core calculations required for transforming the Input-datamodel to the Output one.

Uses *pandalon*'s automatic dependency extraction from calculation functions.
"""
import logging

import numpy as np
import pandas as pd
import lmfit 

from . import pdcalc
from . import datamodel
from collections import OrderedDict
from operator import setitem


log = logging.getLogger(__name__)


def run(mdl, opts=None):
    """
    :param mdl: the datamodel to process, all params and data
    :param map opts: flags controlling non-functional aspects of the process (ie error-handling and logging, gui, etc)
    """

    datamodel.ensure_modelpath_Series(mdl, '/engine')
    #datamodel.ensure_modelpath_Series(mdl, '/params')
    datamodel.ensure_modelpath_DataFrame(mdl, '/measured_eng_points')

    params              = mdl['params']
    engine              = mdl['engine']
    measured_eng_points = mdl['measured_eng_points']

    ## Identify quantities necessary for the FITTING, 
    #    and calculate them.
    outcomes = ('eng_points.cm', 'eng_points.bmep', 'eng_points.pmf', 'engine.fuel_lhv')
    pdcalc.execute_funcs_factory(eng_points_2_std_map, outcomes, params, engine, measured_eng_points)

    ## FIT
    #
    coeffs = datamodel.resolve_jsonpointer(mdl, '/params/fitting/coeffs')
    coeffs = [lmfit.parameter.Parameter(name, **kws) for (name, kws) in coeffs.items()]
    is_robust = datamodel.resolve_jsonpointer(mdl, '/params/fitting/is_robust', False)
    fitted_coeffs = fit_engine_map(measured_eng_points, is_robust, coeffs)
    
    engine['fc_map_coeffs'] = fitted_coeffs

    fitted_eng_points   = reconstruct_eng_points_fitted(engine, fitted_coeffs, measured_eng_points)
    std_to_norm_map(engine, fitted_eng_points)

    if datamodel.resolve_jsonpointer(mdl, '/params/plot_maps'):
        mesh_eng_points     = generate_mesh_eng_points_fitted(measured_eng_points, fitted_coeffs, measured_eng_points)
        columns = ['pmf', 'cm', 'bmep']
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

    #datamodel.validate_model(mdl, additional_properties=False) TODO: Make OUT-MODEL pass validation. 
    
    return mdl


def eng_points_2_std_map(params, engine, eng_points):
    """
    A factory of the calculation functions for reaching to the data necessary for the Fitting.

    The order of the functions below not important, and the actual order of execution 
    is calculated from their dependencies, based on the data-frame's column access.
    """
    from math import pi
    
    funcs = [
        lambda: setitem(engine,     'fuel_lhv',           params['fuel'][engine.fuel]['lhv']),
        lambda: setitem(eng_points, 'n',      eng_points.n_norm * (engine.n_rated - engine.n_idle) + engine.n_idle),
        lambda: setitem(eng_points, 'p',      eng_points.p_norm * engine.p_max),
        lambda: setitem(eng_points, 'fc',     eng_points.fc_norm * engine.p_max),
        lambda: setitem(eng_points, 'rps',    eng_points.n / 60),
        #lambda: setitem(eng_points, 'rps',     eng_points.cm * 1000 / (2 * engine.stroke)),
        lambda: setitem(eng_points, 'torque', (eng_points.p * 1000) / (eng_points.rps * 2 * pi)),
        lambda: setitem(eng_points, 'bmep',   (eng_points.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-6)),
        lambda: setitem(eng_points, 'pmf',    ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-6)) * (eng_points.fc / (3600 * eng_points.rps * 2 * pi)) * 10e-5),
        lambda: setitem(eng_points, 'cm',     eng_points.rps * 2 * engine.stroke / 1000),
    ]

    return funcs

def std_to_norm_map(engine, eng_points):
    from math import pi

    eng_points['rps']       = eng_points.cm * 1000 / (2 * engine.stroke)
    eng_points['n']         = eng_points.rps * 60
    eng_points['n_norm']    = eng_points.n / (engine.n_rated - engine.n_idle) + engine.n_idle
    
    eng_points['torque']    = eng_points.bmep * (engine.capacity * 10e-3) / (4 * pi * 10e-5)
    eng_points['p']         = eng_points.torque * (eng_points.rps * 2 * pi) / 1000

    eng_points['fc']        = (eng_points.pmf * (engine.capacity * 10e-2) * (3600 * eng_points.rps * 2 * pi)) / (4 * pi * engine.fuel_lhv * 10e-5)
    eng_points['fc_norm']   = eng_points.fc / engine.p_max

    eng_points['p_norm']    = eng_points.p / engine.p_max



def engine_map_modelfunc(coeff_values, X):
    """
    The function that models the engine-map.
    """
    
    a       = coeff_values['a']
    b       = coeff_values['b']
    c       = coeff_values['c']
    a2      = coeff_values['a2']
    b2      = coeff_values['b2']
    loss0   = coeff_values['loss0']
    loss2   = coeff_values['loss2']

    pmf     = X['pmf']
    cm      = X['cm']
    
    bmep = (a + b*cm + c*cm**2)*pmf + (a2 + b2*cm)*pmf**2 + loss0 + loss2*cm**2
    
    return bmep


def fit_engine_map(df, is_robust, coeffs):
    assert len({'cm', 'bmep', 'pmf'} - set(df.columns)) == 0, \
            "Missing fit-columns: %s" % {'cm', 'bmep', 'pmf'} - set(df.columns)
    assert not np.any(np.isnan(df['pmf'])), \
            "Cannot fit with NaNs in `pmf` data! \n%s" % np.any(np.isnan(df['pmf']), axis=1)
    assert not np.any(np.isnan(df['cm'])), \
            "Cannot fit with NaNs in `cm` data! \n%s" % np.any(np.isnan(df['cm']), axis=1)

    residualfunc_args   = (engine_map_modelfunc, df, df['bmep'])
    residualfunc_kws    = dict(is_robust=is_robust)
    minimizer = lmfit.minimize(_robust_residualfunc, coeffs, 
                args=residualfunc_args, 
                kws=residualfunc_kws)
    res_df = pd.Series(minimizer.params.valuesdict())

    return res_df


def reconstruct_eng_points_fitted(engine, fitted_coeffs, eng_points):
    bmep = engine_map_modelfunc(fitted_coeffs, eng_points)

    fitted_eng_points = pd.DataFrame.from_items(zip(['pmf', 'cm', 'bmep'], (eng_points.pmf, eng_points.cm, bmep)))

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
    Y = engine_map_modelfunc(fitted_coeffs, X)


    mesh_eng_points = OrderedDict(zip(['pmf', 'cm', 'bmep'], (X1, X2, Y)))

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


def proc_vehicle(dfin, datamodel):

    ## Filter values
    #
    nrows       = len(dfin)
    dfin = dfin[(dfin.bmep > -1.0) & (dfin.bmep < 25.0)]
    log.warning('Filtered %s out of %s rows for BAD  bmep.', nrows-len(dfin), nrows)

    return dfin



def _robust_residualfunc(coeffs, modelfunc, X, YData, is_robust=False, robust_prcntile=None):
    """
    A non-linear iteratively-reweighted least-squares (IRLS) residual function (objective-function) 
    that robustly fits ``YData = modelfunc(X)``.

    This method applies weights on each iteration so as to downscale any outliers and high-leverage data-points
    based on the 'bisquare' standardized adjusted residuals:[#]_
    
    .. math::
    
            \frac{r}{K \times \hat{\sigma} \times \sqrt{1 - h}}
    
    where:

    :math:`r` (vector)
        the residuals :math:`\hat{y} - y`
        
    :math:`K` (scalar)
        the *robust percentile* tuning constant used on each iteration to filter-out
        adjusted-standardized-weights above 1, expressed as the Bisquare M-estimator efficiency 
        under Gaussian model. 
        
    :math:`\hat{\sigma}` (scalar)
        the robust estimate of the *standard deviation* of the residuals
        based on MAD[#]_ like this: :math:`\hat{\sigma}=1.4826\times\operatorname{MAD}`
        
    :math:`h` : (vector)
        the *hat vector*, the diagonal of the *hat matrix*,[#]_
        which is used to reduce the weight of high-leverage data points
        that are having a large effect on the least-squares fit.


    :param modelfunc:             The modeling function that accepts the dict of coeffs
    :param nparray X:             
    :param nparray YData:         measured-data points
    :param boolean is_robust:     Whether to deleverage outlier YData.
    :param float robust_prcntile: The `K` percentile of the MAD, 
                             [default: 4.68, filters-out approximately 5% of the residuals as outliers]

    .. Seealso::
        curve_fit, leastsq


    .. [#] http://www.mathworks.com/help/stats/robustfit.html
    .. [#] https://en.wikipedia.org/wiki/Median_absolute_deviation
    .. [#] https://en.wikipedia.org/wiki/Hat_matrix
    """
    YFitted = engine_map_modelfunc(coeffs.valuesdict(), X)
    Residual    = YFitted - YData

    ## Robust:
    ## Deleverage and standardize absolute-residuals based on a robust-MAD.
    ##
    if is_robust:
        R_abs       = Residual.abs()
        if not robust_prcntile:
            robust_prcntile = 4.685     ##  Bisquare M-estimator with 95% efficiency under the Gaussian model.
        R_deleved   = R_abs / (robust_prcntile * 1.4826 * np.median(R_abs))  ## * sqrt(1 - hat_vector))
        ## Calc the robust bisquared-residuals excluding outliers.
        R_weights   = (R_deleved < 1) * (1 - R_deleved**2)**2

        Residual = R_weights * Residual
        
    return Residual


