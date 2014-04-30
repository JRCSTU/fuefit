import pandas as pd
import numpy as np
import logging

log = logging.getLogger(__file__)

def funcs_fact(params, engine, dfin, dfout):
    from math import pi

    engine['engine.fuel_lhv']    = params[engine.fuel]
    dfin['rpm']   = dfin.rpm_norm * (engine.rpm_rated - engine.rpm_idle) + engine.rpm_idle
    dfin['p']     = dfin.p_norm * engine.p_max
    dfin['fc']    = dfin.fc_norm * engine.p_max
    dfin['rps']   = dfin.rpm / 60
    dfin['torque'] = (dfin.p * 1000) / (dfin.rps * 2 * pi)
    dfin['pme']   = (dfin.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-3)
    dfin['pmf']   = ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-3)) * (dfin.fc / (3600 * dfin.rps * 2 * pi)) * 10e-5
    dfin['cm']    = dfin.rps * 2 * engine.stroke / 1000

    def f1(): engine['fuel_lhv'] = params['fuel'][engine['fuel']]['lhv']
    def f2(): dfin['rpm']     = dfin.rpm_norm * (engine.rpm_rated - engine.rpm_idle) + engine.rpm_idle
    def f3(): dfin['p']       = dfin.p_norm * engine.p_max
    def f4(): dfin['fc']      = dfin.fc_norm * engine.p_max
    def f5(): dfin['rps']     = dfin.rpm / 60
    def f6(): dfin['torque']  = (dfin.p * 1000) / (dfin.rps * 2 * pi)
    def f7(): dfin['pme']     = (dfin.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-6)
    def f8(): dfin['pmf']     = ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-3)) * (dfin.fc / (3600 * dfin.rps * 2 * pi)) * 10e-5
    def f9(): dfin['cm']      = dfin.rps * 2 * engine.stroke / 1000

    ## Out of returned funcs!!
    def f10(): return dfin.cm + dfin.pmf + dfin.pme

    def f11(): engine['fc_map_params'] = f10()
    def f12():
        dfout['rpm']    = engine['fc_map_params']
        dfout['p']      = engine['fc_map_params'] * 2
        dfout['fc']     = engine['fc_map_params'] * 4
    def f13(): dfout['fc_norm']         = dfout.fc / dfout.p

    return (f1, f2, f3, f4, f5, f6, f7, f8, f9, f11, f12, f13)

def proc_vehicle(dfin, model):

    ## Filter values
    #
    nrows       = len(dfin)
    dfin = dfin[(dfin.pme > -1.0) & (dfin.pme < 25.0)]
    log.warning('Filtered %s out of %s rows for BAD  pme.', nrows-len(dfin), nrows)

    return dfin


## Perform normal and ROBUST fit.
#

def fit_map(engine, dfin):
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

    dfin = engine.fc_table
    Y = dfin.pme.values

    (res, _) = curve_fit(fitfunc, dfin, Y, robust=False)
    res_df = pd.DataFrame(res, index=param_names)
    engine['fc_map_params'] = res_df
