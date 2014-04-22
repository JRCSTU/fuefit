# from unittest.mock import MagicMock, _Call
from fuefit.mymock import MagicMock, _Call
from collections.abc import Iterable
import itertools
import networkx as nx
import sys
import re

# from . import json_dumps
from fuefit import json_dumps, mymock

## Workaround missing __truediv__() BUG fixed in 3.4: http://bugs.python.org/issue20968
def get_instrospector_var_factory():
    pyver = sys.version_info[:2]
    return MagicMock
#     if (pyver[0] >=3 and pyver[1] >=4):
#         return MagicMock
#     else:
#         class DepGrapher(MagicMock):
#             def __truediv__(self, other):
#                 return self.__div__(other)
#         return DepGrapher
make_instrospector_var = get_instrospector_var_factory()


def get_calculations(params, engine, df):
    from math import pi

    engine['fuel_lhv']    = params[engine.fuel]
    df['rpm']   = df.rpm_norm * (engine.rpm_rated - engine.rpm_idle) + engine.rpm_idle
    df['p']     = df.p_norm * engine.p_max
    df['fc']    = df.fc_norm * engine.p_max
    df['rps']   = df.rpm / 60
    df['torque'] = (df.p * 1000) / (df.rps * 2 * pi)
    df['pme']   = (df.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-3)
    df['pmf']   = ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-3)) * (df.fc / (3600 * df.rps * 2 * pi)) * 10e-5
    df['cm']    = df.rps * 2 * engine.stroke / 1000


def harvest_calls(func):
    import inspect

    argspec = inspect.getfullargspec(func)
    if (argspec.varargs or argspec.varkw):
        raise NotImplementedError('Inspecting dependencies for cal-functions with *varags or **keywords not supported!')

    argnames = argspec.args
    (root, mocks) = make_introspect_args(argnames)
    func(*mocks)

#     g = nx.DiGraph()
    deps = [harvest_call(call) for call in root.mock_calls]
#     deps = root.mock_calls

    return deps

#     t=mocks[0].mock_calls[0][1]
#     print(t[0])


def make_introspect_args(args):
    root = make_instrospector_var(name='root')
    mocks = [make_instrospector_var() for arg in args]
    for (mock, arg) in zip(mocks, args):
        root.attach_mock(mock, arg)
    return (root, mocks)

def harvest_call(mock_call):
    (path, args, kw) = mock_call
    attrs = []

    deps_args = [harvest_mock(arg) for arg in args if isinstance(arg, MagicMock)]
    deps_kws = [harvest_mock(v) for v in kw.values() if isinstance(v, MagicMock)]

    ## Consume special_methods
    #    and find any ['index'] items.
    pa_th = path.split('.')
    tail = pa_th[-1]
    if (tail == '__getitem__' or tail == '__setitem__'):
        attrs = gather_item(args[0])
    #path = strip_magick_calls(path)
    path = harvest_mock(mock_call.parent)
    #path = str(parse_mock_str(mock_call.parent))
    if path:
        path = [path]
    return (path, attrs, deps_args, deps_kws)
#     return path + attrs + deps_args + deps_kws


def gather_item(index):
        if isinstance(index, MagicMock):
            deps = [harvest_mock(index)]
        elif isinstance(index, slice):
            deps = gather_item(index.start) + gather_item(index.stop) + gather_item(index.step)
        elif isinstance(index, str):
            deps = [index]
        elif isinstance(index, Iterable):
            deps = list(itertools.chain(*[gather_item(indx) for indx in index]))
        else:
            deps = []
        return deps

def harvest_mock(mock):
    return strip_magick_calls(parse_mock_str(mock)[0])

def strip_magick_calls(path):#Assumes magciks always at tail.
    pa_th = path.split('.')
    while (pa_th[-1].startswith('__')):
        del pa_th[-1]
        if (not pa_th):
            return []
    path = '.'.join(pa_th)
    return path

_mock_id_regex = re.compile(r"name='([^']+)' id='(\d+)'")
def parse_mock_str(m):
    return _mock_id_regex.search(m.__repr__()).groups()


def test_inspect_calc_dependencies():
    def calc(df, params):
        df.hh[['tt','ll', 'i']]    = params.tt
        df.hh['tt':'ll', 'i']    = params.tt
        df.hh['tt']['ll']  = params.OO
        df(params.pp['g'])

    deps = harvest_calls(calc)
    print(deps)
    assert deps[0][1] == ['tt','ll', 'i'], deps[0][1]
    assert deps[1][1] == ['tt','ll', 'i'], deps[0][1]
    assert deps[2][1] == ['tt'], deps[2][1]
    assert deps[3][1] == ['ll'], deps[3][1]

    calc1 = lambda df, params: df.hh[['tt','ll', 'i', params.b]]['g'] + params.tt
    calc2 = lambda df, params: df.hh['tt','ll', 'i', params.b]['g'] + params.tt
    calc3 = lambda df, params: df.hh['tt':'ll', 'i', params.b]['g'] + params.tt

    deps = harvest_calls(calc1); print(deps)
    deps = harvest_calls(calc2); print(deps)
    deps = harvest_calls(calc3); print(deps)



if __name__ == "__main__":
#     test_inspect_calc_dependencies()
    deps = harvest_calls(get_calculations)
    print('\n'.join([str(s) for s in deps]))
    print([d.parent for d in deps[:]])
