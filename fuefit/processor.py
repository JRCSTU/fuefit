import pandas as pd
import numpy as np
import logging
from fuefit import pdcalc

log = logging.getLogger(__file__)


def run_processor(opts, mdl):
    funcs_map = {
        norm_to_std_map: True
    }
    params  = mdl['params']
    engine  = mdl['engine']
    dfin      = mdl['engine_points']
    pdcalc.execute_funcs_map(funcs_map, ('df.cm', 'df.pme', 'df.pmf'), params, engine, dfin)

    engine['fc_map_params'] = fit_map(engine, dfin)

    dfout = std_to_norm_map(params, engine, dfin)

    mdl['engine_map'] = dfout

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

def std_to_norm_map(params, engine, df):
    from math import pi

    df['rps']       = df.cm * 1000 / (2 * engine.stroke)
    df['rpm']       = df.rps * 60
    df['rpm_norm']  = df['rpm'] / (engine.rpm_rated - engine.rpm_idle) + engine.rpm_idle

    df['torque']    = df.pme * (engine.capacity * 10e-3) / (4 * pi * 10e-5)
    df['p']         = df.torque * (df.rps * 2 * pi) / 1000

    df['fc']        = (df.pmf * (engine.capacity * 10e-2) * (3600 * df.rps * 2 * pi)) / (4 * pi * engine.fuel_lhv * 10e-5)
    df['fc_norm']   = df.fc / engine.p_max

    df['p_norm']    = df.p / engine.p_max




## Perform normal and ROBUST fit.
#

def fit_map(engine, df):
    from scipy.optimize import curve_fit as curve_fit
    #from .robustfit import curve_fit

    param_names = ('a', 'b', 'c', 'a2', 'b2', 'loss0', 'loss2')

    def fitfunc(X, a, b, c, a2, b2, loss0, loss2):
        pmf = X['pmf']
        cm = X['cm']
        assert not any(np.isnan(pmf)), np.any(np.isnan(pmf), axis=1)
        assert not any(np.isnan(cm)), np.any(np.isnan(cm), axis=1)
        z = (a + b*cm + c*cm**2)*pmf + (a2 + b2*cm)*pmf**2 + loss0 + loss2*cm**2
        return z

    Y = df.pme.values

    (res, _) = curve_fit(fitfunc, df, Y)#, robust=False)
    res_df = pd.DataFrame(res, index=param_names)
    return res_df


def proc_vehicle(dfin, model):

    ## Filter values
    #
    nrows       = len(dfin)
    dfin = dfin[(dfin.pme > -1.0) & (dfin.pme < 25.0)]
    log.warning('Filtered %s out of %s rows for BAD  pme.', nrows-len(dfin), nrows)

    return dfin
