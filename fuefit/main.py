#!/usr/bin/env python
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
"""The command-line entry-point for using all functionality of fuefit tool. """

import sys, os
import traceback
import collections
import logging
import argparse
from argparse import RawTextHelpFormatter
from textwrap import dedent
import re
import functools
import json
import jsonschema as jsons
import jsonpointer as jsonp
import pandas as pd

from . import model, _version


DEBUG   = False

log = None

## The value of format=VALUE to decide which pandas.read_XXX() method to use.
_pandas_formats = collections.OrderedDict([
    ('AUTO',None),
    ('CSV', pd.read_csv),
    ('TXT', pd.read_csv),
    ('XLS', pd.read_excel),
    ('JSON', pd.read_json),
    ('CLIPBOARD', pd.read_clipboard),
])
_known_file_exts = {
    'XLSX':'XLS'
}
def get_file_format_from_extension(fname):
    ext = os.path.splitext(fname)[1]
    if (ext):
        ext = ext.upper()[1:]
        if (ext in _known_file_exts):
            return _known_file_exts[ext]
        if (ext in _pandas_formats):
            return ext

    return None


_default_pandas_format  = 'AUTO'
_default_df_dest        = '/engine_points'
_default_df_source      = '/engine_map'
_default_append         = False

## When option `-m MODEL_PATH=VALUE` contains a relative path,
# the following is preppended:
_model_default_prefix = '/engine/'

def _json_default(o):
    if (isinstance(o, pd.DataFrame)):
        return pd.DataFrame.to_json(o)
    else:
        return repr(o)

def json_dumps(obj):
    json.dumps(obj, indent=2, default=_json_default)


def str2bool(v):
    vv = v.lower()
    if (vv in ("yes", "true", "on")):
        return True
    if (vv in ("no", "false", "off")):
        return False
    try:
        return float(v)
    except:
        raise argparse.ArgumentTypeError('Invalid boolean(%s)!' % v)

_value_parsers = {
    '+': int,
    '*': float,
    '?': str2bool,
    ':': json.loads,
    ';': eval
}


_key_value_regex = re.compile(r'^\s*([A-Za-z]\w*)\s*([+*?:;]?)=\s*(.+?)\s*$')
def parse_key_value_pair(arg):
    """Argument-type for syntax like: KEY [+*?:]= VALUE."""

    m = _key_value_regex.match(arg)
    if m:
        (key, type_sym, value) = m.groups()
        if type_sym:
            try:
                value   = _value_parsers[type_sym](value)
            except Exception as ex:
                raise argparse.ArgumentTypeError("Failed parsing key(%s)'s %s-VALUE(%s) due to: %s" %(key, type_sym, value, ex)) from ex

        return [key, value]
    else:
        raise argparse.ArgumentTypeError("Not a KEY=VALUE syntax: %s"%arg)


_column_specifier_regex = re.compile(r'^\s*([^(]+)\s*(\(([^)]+)\))?\s*$')
def parse_column_specifier(arg):
    """Argument-type for --icolumns, syntaxed like: COL_NAME [(UNITS)]."""

    m = _column_specifier_regex.match(arg)
    if m:
        return m.groups()
    else:
        raise argparse.ArgumentTypeError("Not a COLUMN_SPEC syntax: %s"%arg)


FileSpec = collections.namedtuple('FileSpec', ('fname', 'file', 'format', 'path', 'append', 'kws'))

def main(argv=None):
    """Calculates an engine-map by fitting data-points vectors, use --help for gettting help.

    REMARKS:
    --------
        * All string-values are case-sensitive.
        * Boolean string-values are case insensitive:
            False  : false, off, no,  == 0
            True   : true,  on,  yes, != 0
        * In KEY=VALUE pairs, the values are passed as string.  For other types,
          substitute '=' with:.
            +=     : integer
            *=     : float
            ?=     : boolean
            :=     : parsed as json
            ;=     : parsed as python (with eval())

    EXAMPLES:
    ---------
    Assuming a CSV-file 'engine.csv' like this:
            CM,PME,PMF
            12,0.14,180
            ...

        ## Calculate and print fitted engine map's parameters
        #     for a PETROL vehicle with the above engine-point's CSV-table:
        >> %(prog)s -m fuel=PETROL -I engine.csv

        ## Assume PME column contained normalized-Power in Watts,
        #    instead of P in kW:
        >> %(prog)s -m fuel=PETROL -I engine.csv  -irenames X X 'Pnorm (w)'

        ## Read the same table above but without header-row and
        #    store results into Excel file:
        >> %(prog)s -m fuel=PETROL -I engine.csv --icolumns CM PME PMF -O engine_map.xlsx

        ## Supply as inline-json more model-values required for columns [RPM, P, FC]
        #    read from <stdin> as json 2D-array of values (no headers).
        #    and store results in UTF-8 regardless of platform's default encoding:
        >> %(prog)s -m '/engine:={"fuel":"PETROL", "stroke":15, "capacity":1359}' \\
                -I - format=JSON orient=values -c RPM P FC \\
                -O engine_map.txt encoding=UTF-8


    Now, if input vectors are in 2 separate files, the 1st, 'engine_1.xlsx',
    having 5 columns with different headers than expected, like this:
        OTHER1   OTHER2       N        "Fuel waste"   OTHER3
        0       -1            12       0.14           "some text"
        ...

    and the 2nd having 2 columns with no headers at all and
    the 1st column being 'Pnorm', then it, then use the following command:

        >> %(prog)s -O engine_map -m fuel=PETROL \\
                -I=engine_1.xlsx \\
                -c X   X   N   'Fuel consumption'  X \\
                -r X   X   RPM 'FC(g/s)'           X \\
                -I=engine_2.csv \\
                -c Pnorm X
    """

    global log, DEBUG

    program_name    = 'fuefit' #os.path.basename(sys.argv[0])

    if argv is None:
        argv = sys.argv[1:]

    doc_lines       = main.__doc__.splitlines()
    desc            = doc_lines[0]
    epilog          = dedent('\n'.join(doc_lines[1:]))
    parser = build_args_parser(program_name, _version, desc, epilog)

    try:

        opts = parser.parse_args(argv)

        DEBUG = bool(opts.debug)

        if (DEBUG):
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        log = logging.getLogger(__file__)
        log.info("Args: argv\nOpts: %s", opts)

        opts = validate_file_opts(opts)

        infiles     = parse_many_file_args(opts.I, 'r')
        log.info("Input-files: %s", json_dumps(infiles))

        outfiles    = parse_many_file_args(opts.O, 'w')
        log.info("Output-files: %s", json_dumps(outfiles))

        mdl = build_and_validate_model(opts, infiles)
        log.info("Input Model: %s", json_dumps(mdl))

    except (SystemExit) as ex:
        if DEBUG:
            log.error(traceback.format_exception())
        raise
    except (ValueError) as ex:
        if DEBUG:
            log.error(traceback.format_exception())
        indent = len(program_name) * " "
        parser.exit(3, "%s: %s\n%s  for help use --help\n"%(program_name, ex, indent))
    except jsons.ValidationError as ex:
        if DEBUG:
            log.error(traceback.format_exception())
        indent = len(program_name) * " "
        parser.exit(4, "%s: Model validation failed due to: %s\n%s  for help use --help\n"%(program_name, ex, indent))


def validate_file_opts(opts):
    ## Check number of input-files <--> related-opts
    #
    dopts = vars(opts)

    if (not opts.I):
        n_infiles = 1
    else:
        n_infiles = len(opts.I)
    rel_opts = ['icolumns', 'irenames']
    for ropt in rel_opts:
        opt_val = dopts[ropt]
        if (opt_val):
            n_ropt = len(opt_val)
            if( n_ropt > 1 and n_ropt != n_infiles):
                raise argparse.ArgumentTypeError("Number of --%s(%i) mismatches number of -I(%i)!"%(ropt, n_ropt, n_infiles))


    return opts


def parse_many_file_args(many_file_args, filetype):
    def parse_file_args(fname, *kv_args):
        frmt    = _default_pandas_format
        dest    = _default_df_dest
        append  = _default_append

        kv_pairs = [parse_key_value_pair(kv) for kv in kv_args]
        pandas_kws = dict(kv_pairs)

        if ('format' in pandas_kws):
            frmt = pandas_kws.pop('format')
            if (frmt not in _pandas_formats):
                raise argparse.ArgumentTypeError("Unsupported pandas-format: %s\n  Set 'format=XXX' to one of %s" % (frmt, list(_pandas_formats.keys())[1:]))

        if (frmt == 'CLIPBOARD'):
            file    = None
            fname   = '<CLIPBOARD>'
        else:
            if (frmt == _default_pandas_format):
                if ('-' == fname):
                    raise argparse.ArgumentTypeError("With <stdio> a concrete pandas-format is required! \n  Set 'format=XXX' to one of %s" % (list(_pandas_formats.keys())[1:]))
                frmt = get_file_format_from_extension(fname)
                if (not frmt):
                    raise argparse.ArgumentTypeError("File(%s) has unknown extension, pandas-format is required! \n  Set 'format=XXX' to one of %s" % (fname, list(_pandas_formats.keys())[1:]))
            file = argparse.FileType(filetype)(fname)


        if ('model_path' in pandas_kws):
            dest = pandas_kws.pop('model_path')
            if (not dest.startswith('/')):
                raise argparse.ArgumentTypeError('Only absolute dest-paths supported: %s' % (dest))

        if ('file_append' in pandas_kws):
            append = pandas_kws.pop('append')
            append = str2bool(append)

        return FileSpec(fname, file, frmt, dest, append, pandas_kws)

    return [parse_file_args(*file_args) for file_args in many_file_args]


def build_and_validate_model(opts, infiles):
    mdl = model.base_model()

#     ## TODO: Merge models.
#     if (opts.model):
#         model.merge(mdl, opts.model)

    model_overrides = opts.m
    if (model_overrides):
        model_overrides = functools.reduce(lambda x,y: x+y, model_overrides) # join all -m
        for (json_path, value) in model_overrides:
            if (not json_path.startswith('/')):
                json_path = _model_default_prefix + json_path
            jsonp.set_pointer(mdl, json_path, value)

    validator = model.model_validator()
    validator.validate(mdl)

    return mdl

def build_args_parser(program_name, version, desc, epilog):
    version_string  = '%%prog %s' % (version)

    parser = argparse.ArgumentParser(prog=program_name, description=desc, epilog=epilog, add_help=False,
                                     formatter_class=RawTextHelpFormatter)


    grp_io = parser.add_argument_group('Input/Output', 'Options controlling reading/writting of file(s) and for specifying model values.')
    grp_io.add_argument('-I', help=dedent("""\
            import file(s) into the model utilizing pandas-dataframes.
            Default: %(default)s]
            * The syntax of this option is like this:
                    FILENAME [KEY=VALUE ...]]
            * The FILENAME can be '-' to designate <stdin>.
            * Most KEY-VALUE pairs pass option(s) directly to pandas.read_XXX() methods, see:
                    http://pandas.pydata.org/pandas-docs/stable/io.html
              See REMARKS below for the parsing of KEY-VAULE pairs.
            * The following keys are consumed before reaching pandas:
            ** format = [ AUTO | CSV | TXT | XLS | JSON | CLIPBOARD ]
                    selects which pandas.read_XXX() method to use.
                    When AUTO (default), file-format deduced from filename's extension
                    (ie use it with Excel files). For  JSON, different sub-formats are selected
                    through the 'orient' keyword of Pandas, specified with a later key-value pair.
                    When CLIPBOARD, file ignored
            ** model_path = MODEL_PATH
                    specifies the destination (or source) of the dataframe within the model
                    as json-pointer path (see -m option).
                    If many input-files have the same --model_path, the dataframes are
                    concatenated horizontally therefore the number of rows (excluding header)
                    for all those data-files must be equal.
            * When more input-files given, the number --icolumns and --irenames options,
              must either match them, be 1 (meaning use them for all files), or be totally absent
              (meaning use defaults for all files). """),
                        action='append', nargs='+',
                        default=[('- format=%s model_path=%s'%(_default_pandas_format, _default_df_dest)).split()],
                        metavar='ARG')
    grp_io.add_argument('-c', '--icolumns', help=dedent("""\
            describes the contents and the units of input file(s) (see --I).
            It must be followed either by an integer denoting the index of the header-row
            within the tabular data, or by a list of column-names specifications,
            obeying the following syntax:
                COL_NAME [(UNITS)]
            Accepted quantities and their default units are grouped in 3+1 quantity-types and
            for each file exactly one from each of the 3 first categories must be present:
            1. engine-speed:
                RPM      (rad/min)
                RPMnorm  (rad/min)  : normalized against RPMnorm * RPM_IDLE + (RPM_RATED - RPM_IDLE)
                Omega    (rad/sec)
                CM       (m/sec)    : Mean Piston speed
            2. work-capability:
                P        (kW)
                Pnorm    (kW)       : normalized against P_MAX
                T        (Nm)
                PME      (bar)
            3. fuel-consumption:
                FC       (g/h)
                FCnorm   (g/h)      : normalized against P_MAX
                PMF      (bar)
            4. Irellevant column:
                X
            Default when files include heqders is 0 (1st row), otherwise it is 'RPM,P,FC'."""),
                        action='append', nargs='+',
                        type=parse_column_specifier, metavar='COLUMN_SPEC')
    grp_io.add_argument('-r', '--irenames', help=dedent("""\
            renames the columns of input-file(s)  (see --I).
            It must be followed by a list of column-names specifications like --icolumns,
            but without accepting integers.
            The number of renamed-columns for each input-file must be equal or less
            than those in the --icolumns for the respective inpute-file.
            Use 'X' for columns to be left intact."""),
                        action='append', nargs='+',
                        type=parse_column_specifier, metavar='COLUMN_SPEC')
    grp_io.add_argument('-m', help=dedent("""\
            override a model value.
            * The MODEL_PATH is a json-pointer absolute or relative path, see:
                    https://python-json-pointer.readthedocs.org/en/latest/tutorial.html
              Relative paths are resolved against '/engine', for instance:
                    -Mrpm_idle=850   -M/engine/p_max=660
              would set the following model's property:
                    {
                      "engine": {
                          "rpm_idle": 850,
                          "p_max": 660,
                          ...
                      }
                    }
            * Any values from -m options are applied AFTER any files read by -I option.
            * See REMARKS below for the parsing of KEY-VAULE pairs.
            """),
                        action='append', nargs='+',
                        type=parse_key_value_pair, metavar='MODEL_PATH=VALUE')
    grp_io.add_argument('--lax', help=dedent("""\
            validate model more relaxed (additional-properties allowed)."""),
            default=True, type=str2bool,
            metavar='[TRUE | FALSE]')
    grp_io.add_argument('-M', help=dedent("""\
            get help description for the specfied model path.
            If no path specified, gets the default model-base. """),
                        action='append', nargs='*',
                        type=parse_key_value_pair, metavar='MODEL_PATH')


    grp_io.add_argument('-O', help=dedent("""\
            specifies output-file(s) to write model-portions into after calculations.
            The syntax is indentical to -I, with these differences:
            * When FILENAME is '-', <stdout> is used.
            * One extra key-value pair:
            ** file_append = [ TRUE | FALSE ]
                    specify whether to augment pre-existing files, or overwrite them.
            * Default: %(default)s] """),
                        action='append', nargs='+',
                        default=[('- format=%s model_path=%s file_append=%s'%(_default_pandas_format, _default_df_source,  _default_append)).split()],
                        metavar='ARG')


    grp_various = parser.add_argument_group('Various', 'Options controlling various other aspects.')
    #parser.add_argument('--gui', help='start in GUI mode', action='store_true')
    grp_various.add_argument("--debug", action="store_true", help="set debug level [default: %(default)s]", default=False)
    grp_various.add_argument("--verbose", action="count", default=0, help="set verbosity level [default: %(default)s]")
    grp_various.add_argument("--version", action="version", version=version_string, help="prints version identifier of the program")
    grp_various.add_argument("--help", action="help", help='show this help message and exit')

    return parser


if __name__ == "__main__":
    sys.exit(main())
