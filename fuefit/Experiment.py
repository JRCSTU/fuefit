# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# Imports engine-data from many files and produces the _EngineMaps&trade;_ by robustly fitting them on the _CanonicalModel&reg;_:
#
# $$pme = (a + b \times cm + c \times cm^2) \times pmf + (a2 + b2\times cm) \times pmf^2 + pm1 + pm2 \times cm^2$$

# <codecell>


import pandas as pd
import numpy as np
import json
from collections import OrderedDict
import collections

# <codecell>


FLHV_diesel = 42700
FLHV_gasoline = 43000
def_vehicle = {
    "rpm_idle": 730,
    "rpm_rated": 5400,
}

inpfile = 'TUG/Real/Vehicle_data4FC_mapsV3.xlsx'
xls = pd.ExcelFile(inpfile)
sheets = xls.sheet_names

# <codecell>

## Collect files to read.
#
import os.path, re, glob

def gather_and_parse_names(names, regex, defaults):
    '''Gathers files based on glob-pattern and extracts infos from their fnames using regex's named-groups.

    Params
    ------
    excelObj : pandas.Excel
    sheetname_regex : string,
        the regex pattern use to parse the names, which should contain named-groups,
        ie: `Class(?P<class>[^_]+)_(?P<fuel>[^_]+)_(?P<cert>[^.]+)`
    '''

    data = OrderedDict()
    for name in names:
        match = re.match(regex, name)
        if (match):
            nval = defaults.copy()
            nval.update( match.groupdict())
            data[name] = nval
        else:
            print('Skipped(%s): did not matched pattern!'%name)

    return data

##Expect sheet-names to be named like that: `Veh1_Petrol_EU5_Class1`.
#
sheet_regex = '^Veh(?P<v_id>[^_]+)_(?P<fuel>[^_]+)_(?P<cert>[^_]+)_Class(?P<class>\w+)$'
vehicles = gather_and_parse_names(sheets, sheet_regex, def_vehicle)

## Pretty-print file-data.
#
print(json.dumps(vehicles, indent=4))

# <codecell>

## AD-HOC-Parse 1st-sheet with veh/class params.
#
def extract_vehicle_params(dfs):
    veh_nums = dfs.iloc[:, 0].convert_objects().values
    dfs.index = veh_nums
    dfs = dfs.iloc[:, 1:]
    dfs.columns=('capacity', 'p_max', 'stroke')

    ## Fill-in missing values with Averages.
    #
    dfs = dfs.convert_objects(convert_numeric=True) #copy=False)  BUG #6781!!!
    dfs['stroke'].fillna(dfs['stroke'].mean(), inplace=True)

    return dfs

df=xls.parse(0, header=None)
df = df.iloc[:, :4]

class_vehicles_params = {
    '1':extract_vehicle_params(df.iloc[2:9]),
    '2':extract_vehicle_params(df.iloc[13:21]),
    '3':extract_vehicle_params(df.iloc[27:28]),
}


print(class_vehicles_params)

# <codecell>

## Apply the Vehicle-params extracted above.
#
def apply_vehicle_params(veh):
    v_class = veh['class']
    class_vehs = class_vehicles_params[v_class]
    v_id = int(veh['v_id'])
    veh_params = class_vehs.ix[v_id]
    veh.update(veh_params.to_dict())

for (ifn, fn) in enumerate(vehicles.keys()):
    vehicle = vehicles[fn]
    apply_vehicle_params(vehicle)
    vehicles[fn] = vehicle

# <codecell>

## Read files.
#
import pandas as pd

def read_fc_table(fname):
    df = xls.parse(fname, header=1, skiprows=3)
    ####                           Z          X           Y    ####
    assert  tuple(df.columns) == ('norm', 'norm.1', '(g/h)/kW_rated'), 'BAD HEADER on sheet(%s): %s' % (fname, df.columns)

    df.columns = ('n_norm', 'p_norm', 'fc_norm')

    # Delete rows with NaNs (last row), for fitting to work.
    oldlen = len(df)
    df = df.convert_objects(convert_numeric=True)
    df = df.dropna()
    if (oldlen != len(df)):
        print('Dropped %s lines from with NaNs from file(%s)!'% (oldlen - len(df), fname))

    return df

for (ifn, fn) in enumerate(vehicles.keys()):
    try:
        vehicle = vehicles[fn]
        vehicle['fc_table'] = read_fc_table(fn)
        vehicles[fn] = vehicle
        print('Read %i out of %i: file(%s)' % (ifn, len(vehicles), fn))
    except Exception as ex:
        print('Skipped %i out of %i: file(%s) due to: %s' % (ifn, len(vehicles), fn, ex))


# <codecell>

##Plot imported data-points in 2D.
#
fig = plt.figure(figsize=(16,4.5))
for (ifn, (fn, vehicle)) in enumerate(vehicles.items()):
    df = vehicle['fc_table']
    ax = fig.add_subplot(2, (len(vehicles) + 1)/2, ifn+1)
    ax.set_title(fn)
    plt.scatter(df.n_norm.values, df.p_norm.values)
    ax.grid('on')

ax = fig.get_axes()[int((len(vehicles) + 1)/2)]
ax.set_xlabel('n_norm', color='red'); ax.set_ylabel('p_norm', color='green')

fig.subplots_adjust(wspace=0.15, hspace=0.25)

# <codecell>

def funcs_fact(params, engine, dfin):
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


def proc_vehicle(fn, model):
    from math import pi

    engine      = model['engine']
    df          = model['engine_points']

    rpm_idle    = engine['rpm_idle']
    rpm_rated   = engine['rpm_rated']
    p_max       = engine['p_max']
    capacity    = engine['capacity'] * 1000
    stroke      = engine['stroke']
    fuel        = engine['fuel'].lower()
    if (fuel in ('diesel')):
        fuel_lhv = FLHV_diesel
    elif (fuel in ('petrol', 'gasoline')):
        fuel_lhv = FLHV_gasoline
    else:
        raise ValueError('Fuel(%s) not one of: diesel | gasoline'%engine['fuel'])
    engine['fuel_lhv'] = fuel_lhv

    df['rpm']   = df.rpm_norm * (rpm_rated - rpm_idle) + rpm_idle
    df['p']     = df.p_norm * p_max
    df['fc']    = df.fc_norm * p_max
    df['rps']   = df.rpm / 60
    df['torque'] = (df.p * 1000) / (df.rps * 2 * pi)
    df['pme']   = (df.torque * 10e-5 * 4 * pi) / (capacity * 10e-6)
    df['pmf']   = ((4 * pi * fuel_lhv) / (capacity * 10e-6)) * (df.fc / (3600 * df.rps * 2 * pi)) * 10e-5
    df['cm']    = df.rps * 2 * stroke / 1000

    ## Filter values
    #
    nrows       = len(df)
    df = df[(df.pme > -1.0) & (df.pme < 25.0)]
    print ('%s: Filtered %s out of %s rows for BAD  pme.'%(fn, nrows-len(df), nrows))

    return df


## Append calulated columns.
#
for (ifn, fn) in enumerate(vehicles.keys()):
    vehicle = vehicles[fn]
    df = proc_vehicle(fn, vehicle)
    vehicle['fc_table'] = df
    vehicles[fn] = vehicle

# print(vehicles)

# <codecell>

## Monitor selected vehicle.
#
veh = list(vehicles.values())[5]
tab=veh['fc_table']
# pd.concat((tab.min(axis=0), tab.max(axis=0)), axis=1, keys=('min','max'))
tab.describe()

# <codecell>

## Plot de-normalized and filtered data-points in 3D.
#
from mpl_toolkits.mplot3d.axes3d import Axes3D

fig = plt.figure(figsize=(16,4.5))
for (ifn, (fn, vehicle)) in enumerate(vehicles.items()):
    df = vehicle['fc_table']
    ax = fig.add_subplot(2, (len(vehicles) + 1)/2, ifn+1, projection='3d')
    ax.set_title(fn)
    ax.plot(df.n, df.p, list(df.fc), '.b')
    ax.view_init(60, -20)

ax = fig.get_axes()[int((len(vehicles) + 1)/2)]
ax.set_xlabel('RPM', color='red'); ax.set_ylabel('Power', color='green'); ax.set_zlabel('FC', color='blue');

# fig.subplots_adjust(wspace=0.45, hspace=0.45)
plt.tight_layout()

# <codecell>

## Perform normal and ROBUST fit.
#

#from scipy.optimize import curve_fit as curve_fit
from robustfit import curve_fit
import numpy as np

param_names = ('a', 'b', 'c', 'a2', 'b2', 'loss0', 'loss2')

def fitfunc(X, a, b, c, a2, b2, loss0, loss2):
    pmf = X['pmf']
    cm = X['cm']
    assert not any(np.isnan(pmf)), np.any(np.isnan(pmf), axis=1)
    assert not any(np.isnan(cm)), np.any(np.isnan(cm), axis=1)
    z = (a + b*cm + c*cm**2)*pmf + (a2 + b2*cm)*pmf**2 + loss0 + loss2*cm**2
    return z

for (ifn, (fn, vehicle)) in enumerate(vehicles.items()):
    df = vehicle['fc_table']
    Y = df.pme.values

    (res, _) = curve_fit(fitfunc, df, Y, robust=False)
    res_df = pd.DataFrame(res, index=param_names)
    vehicle['eng_map'] = res_df

    (res_rob, _) = curve_fit(fitfunc, df, Y, robust=None)
    res_df = pd.DataFrame(res_rob, index=param_names)
    vehicle['eng_map_robust'] = res_df

    all_res = pd.DataFrame(vstack((res, res_rob)),
                           columns=param_names, index=('normal', 'robust'))
    print('%s out of %i: \n%s'%(fn, len(vehicles), all_res))


# <codecell>

## Print Python's solutions.
#
#print(results, results_rob, mat_fits)





# <codecell>


# <codecell>

## Print differences between MATLAB's and Python's solutions .
#
#print((results - mat_fits).to_string(float_format=lambda n: '{: .6f}'.format(n)))
#print((results_rob - mat_fits).to_string(float_format=lambda n: '{: .6f}'.format(n)))

# <codecell>

def make_grid(df):
    ## Provide some space arounf data-points.
    #
    dmin = df.loc[:, ['pmf', 'cm']].min(axis=0)
    dmax = df.loc[:, ['pmf', 'cm']].max(axis=0)
    drng = (dmax - dmin)
    dmin -= 0.05 * drng
    dmax += 0.10 * drng
    dstp = (dmax - dmin) / 40

    XY = np.mgrid[dmin[0]:dmax[0]:dstp[0], dmin[1]:dmax[1]:dstp[1]]
    return XY


def plot_results_2d(ax, XY, p_params, df):
    (X, Y) = XY
    Z = fitfunc({'pmf':X, 'cm':Y}, *p_params)
    plt.plot(df.pmf, df.cm, '.c', alpha=0.4)
    plt.contour(X, Y, Z, cmap=plt.cm.coolwarm)

    xmin = X.min(); xmax = X.max();
    ymin = Y.min(); ymax = Y.max();
    plt.imshow(Z, cmap=plt.cm.copper, extent=(xmin, xmax, ymin, ymax))
    ax.set_aspect('auto'); ax.set_adjustable('box-forced')
    ax.set_xlabel('pmf', color='red'); ax.set_ylabel('cm', color='green')


fig = plt.figure(figsize=(16,9))
for (ifn, (fn, vehicle)) in enumerate(vehicles.items()):
    df = vehicle['fc_table']
#     m_params = mat_fits[fn]
    p_params = vehicle['eng_map'].values
    p_params_rob = vehicle['eng_map_robust'].values

    XY = make_grid(df)

#     ## MATLAB results
#     #
#     ax = fig.add_subplot(3, len(dfs), ifn+1)
#     ax.set_title('MATLAB: '+fn)
#     m_Z = fitfunc(X, *m_params)
#     plot_results_2d(ax, XY, m_Z, df)

    ## Python fit results
    #
    ax = fig.add_subplot(3, len(vehicles), len(vehicles) + ifn+1)#, aspect='auto', adjustable='box')
    ax.set_title('Python: '+fn)
    plot_results_2d(ax, XY, p_params, df)

    ## Python ROBUST results
    #
    ax = fig.add_subplot(3, len(vehicles), 2*len(vehicles) + ifn+1)
    ax.set_title('PyROB: '+fn)
    plot_results_2d(ax, XY, p_params_rob, df)


# <codecell>

def plot_results_3d(ax, XY, p_params, df):
    (X, Y) = XY
    Z = fitfunc({'pmf':X, 'cm':Y}, *p_params)


    ax.plot_surface(X, Y, Z, cmap=plt.cm.copper, alpha=0.3,  rstride=4, cstride=4)
    plt.plot(df.pmf, df.cm, list(df.pme), '.c')

    cset = ax.contour(X, Y, Z, zdir='z', offset=0, cmap=plt.cm.coolwarm)
    cset = ax.contour(X, Y, Z, zdir='x', offset=pi, cmap=plt.cm.coolwarm)
#     cset = ax.contour(X, Y, Z, zdir='y', offset=-2*pi, cmap=plt.cm.coolwarm)
    #ax.view_init(30, -100)
    ax.set_xlabel('pmf', color='red'); ax.set_ylabel('cm', color='green'); ax.set_zlabel('pme', color='blue')


fig = plt.figure(figsize=(16,9))
for (ifn, (fn, vehicle)) in enumerate(vehicles.items()):
    df = vehicle['fc_table']
#     m_params = mat_fits[fn]
    p_params = vehicle['eng_map'].values
    p_params_rob = vehicle['eng_map_robust'].values

    XY = make_grid(df)

#     ## MATLAB results
#     #
#     ax = fig.add_subplot(3, len(dfs), ifn+1, projection='3d')
#     ax.set_title('MATLAB: '+fn)
#     m_Z = fitfunc(X, *m_params)
#     plot_results_3d(ax, XY, m_Z, df)

    ## Python fit results
    #
    ax = fig.add_subplot(3, len(vehicles), len(vehicles) + ifn+1, projection='3d')
    ax.set_title('Python: '+fn)
    plot_results_3d(ax, XY, p_params, df)

    ## Python ROBUST results
    #
    ax = fig.add_subplot(3, len(vehicles), 2*len(vehicles) + ifn+1, projection='3d')
    ax.set_title('PyROB: '+fn)
    plot_results_3d(ax, XY, p_params_rob, df)

#plt.tight_layout()

# <markdowncell>

# The IRLS robust fitting method
# ------------------------------
# For the ** Reweighted Least Square** (IRLS) method, all residuals on each iteration are multiplied
# with `bisquare` weights so as to downscale (or even filter-out completely) any _outliers_ and/or
# _high-leverage_ data-points.
#
# $$w_i = \begin{cases}
#     (1 - u_i^2)^2, & \text{if } u_i < 1 \\
#     0, & \text{otherwise}
#   \end{cases}
# $$
#
# where:
#
# * $w_i$ : _vector_,
#     the **weights** to multiply each least-square resiual on each iteration
#
# * $u_i = \frac{r_i}{K \times \hat{\sigma} \times \sqrt{1 - h}}$ : _vector_,
#     the **studentized residuals**, that is, standardized, scaled and deleveraged
#     residuals
#
# and:
#
# * $r_i = \hat{y_i} - y_i$ : _vector_,
#     the **residuals**
#
# * $K$ : _scalar_,
#     the **tuning constant** governing the robust percentile of the residuals
#     to be filtered-out; the smaller it is, more outliers are exclude from the fitting.
#
# * $\hat{\sigma} = 1.4826\times\ \operatorname{MAD}(r_i)$ : _scalar_,
#     the **robust stdev** estimate of the residuals
#
# * $h$ : _vector_,
#     the **hat vector** (the diagonal of the _hat matrix_ og the fitting)
#     used to reduce the weight of high-leverage data points
#     that are having a large effect on the least-squares fit.
#

