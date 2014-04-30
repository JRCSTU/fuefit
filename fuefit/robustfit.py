# Robust least squares (starting with the least squares solution).
# Implementation was based on the `scipy.optimize.curve_fit()`,
# which was modified according to Alexey Abramov's suggestions on his blog:
#     http://salzis.wordpress.com/2012/10/01/robust-least-squares-for-fitting-data/
# # TODO: Reduce wighet on high-everage data-points using __hat_vector__.
#
from numpy import (array, isscalar, asarray, median, inf, sqrt)
from scipy.optimize import leastsq


_default_robust = 4.685

def curve_fit(f, xdata, ydata, p0=None, sigma=None, robust=4.685, **kw):
    '''Uses s non-linear iteratively-reweighted least-squares (IRLS) to robustly fit a function, f, to the data.

    This method applies weights on each iteration so as to downscale any outliers and high-leverage data-points
    based on the 'bisquare' standardized adjusted residuals:[#]_
    :math:`\frac{r}{K \times \hat{\sigma} \times \sqrt{1 - h}}`
    where:

    :math:`r` : vector
        the residuals :math:`\hat{y} - y`
    :math:`K` : scalar
        the *robust percentile* tuning constant used on each iteration to filter-out
        adjusted-standarized-weights above 1.
    :math:`\hat{\sigma}` : scalar
        the robust estimate of the *standard deviation* of the residuals
        based on MAD[#]_ like this: :math:`\hat{\sigma}=1.4826\times\operatorname{MAD}`
    :math:`h` : vector
        the *hat vector*, the diagonal of the *hat matrix*,[#]_
        which is used to reduce the weight of high-leverage data points
        that are having a large effect on the least-squares fit.


    Parameters
    ----------
    iterations : integer
        Re-weight iterations to run.
    robust : None, False or float
        The re-weighting *robust percentile* tuning constant.
        The default value filters-out approximately 5% of the residuals as outliers.
        If `False`, no robust-reweighting applied.
    p0 : None, scalar, or M-length sequence
        See ``scipy.curve_fit()`` function.
    sigma : None or N-length sequence
        Note that any sigma-weights are also applied after calculating the robust ones.
        See ``scipy.curve_fit()`` function.
    **kw : <keywords>
        Additional keyword arguments are passed directly to ``scipy.leastsq()`` function.

    Returns
    -------
    See ``scipy.curve_fit()`` function.

    See Also
    --------
    curve_fit, leastsq


    .. [#] http://www.mathworks.com/help/stats/robustfit.html
    .. [#] https://en.wikipedia.org/wiki/Median_absolute_deviation
    .. [#] https://en.wikipedia.org/wiki/Hat_matrix
    '''

    if robust is None:
        robust = _default_robust

    if p0 is None:
        # determine number of parameters by inspecting the function
        import inspect
        args, varargs, varkw, defaults = inspect.getargspec(f)  # @UnusedVariable
        if len(args) < 2:
            msg = "Unable to determine number of fit parameters."
            raise ValueError(msg)
        if 'self' in args:
            p0 = [1.0] * (len(args)-2)
        else:
            p0 = [1.0] * (len(args)-1)

    if isscalar(p0):
        p0 = array([p0])

    if sigma is None:
        weights = 1.0
    else:
        weights = 1.0/asarray(sigma)

    if robust == False:
        args = (xdata, ydata, f, weights)
        f = _weighted_residual_function
    else:
        args = (xdata, ydata, f, weights, robust)
        f = _reweighted_residual_function

    # Remove full_output from kw, otherwise we're passing it in twice.
    return_full = kw.pop('full_output', False)
    res = leastsq(f, p0, args=args, full_output=1, **kw)
    (popt, pcov, infodict, errmsg, ier) = res

    if ier not in [1, 2, 3, 4]:
        msg = "Optimal parameters not found: " + errmsg
        raise RuntimeError(msg)

    if (len(ydata) > len(p0)) and pcov is not None:
        s_sq = (f(popt, *args)**2).sum()/(len(ydata)-len(p0))
        pcov = pcov * s_sq
    else:
        pcov = inf

    if return_full:
        return popt, pcov, infodict, errmsg, ier
    else:
        return popt, pcov


def _weighted_residual_function(params, xdata, ydata, function, weights):
    return weights * (function(xdata, *params) - ydata)

def _reweighted_residual_function(params, xdata, ydata, function, s_weights, robust):
    yfitted     = function(xdata, *params)
    residual    = yfitted - ydata
    r_a         = abs(residual)

    #
    ## Deleverage and standardize absolute-residuals based on a robust-stdev (based on MAD).
    r       = r_a / (robust * 1.4826 * median(r_a)) # TODO * sqrt(1 - hat_vector))
    # Calc the robust bisquared-residuals excluding outliers.
    w       = (r < 1) * (1 - r**2)**2

    return w * s_weights * residual



if __name__ == "__main__":
    import sys

    curve_fit(sys.argv[1:])
    from scipy import optimize
    optimize.curve_fit
