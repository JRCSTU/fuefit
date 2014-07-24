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

import argparse
import ast
import collections
import functools
import json
import logging
import os
import re
import sys
from textwrap import dedent

from pandas.core.generic import NDFrame

from fuefit import Lazy
import jsonpointer as jsonp
import jsonschema as jsons
import operator as ops
import pandas as pd

from . import _version, DEBUG, model, str2bool # @UnusedImport
from .model import json_dump, json_dumps, validate_model
from .processor import run_processor


logging.basicConfig(level=logging.DEBUG)
log     = logging.getLogger(__file__)

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
            @=     : parsed as python (with eval())

    EXAMPLES:
    ---------
    Assuming a CSV-file 'engine.csv' like this:
            CM,PME,PMF
            12,0.14,180
            ...

        ## Calculate and print fitted engine map's parameters
        #     for a petrol vehicle with the above engine-point's CSV-table:

        ## ...and if no header existed:
        >> %(prog)s -m fuel=petrol -I engine.csv header@=None

        ## Assume PME column contained normalized-Power in Watts,
        #    instead of P in kW:
        >> %(prog)s -m fuel=petrol -I engine.csv  -irenames X X 'Pnorm (w)'

        ## Read the same table above but without header-row and
        #    store results into Excel file, 1st sheet:
        >> %(prog)s -m fuel=petrol -I engine.csv --icolumns CM PME PMF -I engine_map.xlsx sheetname+=0

        ## Supply as inline-json more model-values required for columns [RPM, P, FC]
        #    read from <stdin> as json 2D-array of values (no headers).
        #    and store results in UTF-8 regardless of platform's default encoding:
        >> %(prog)s -m '/engine:={"fuel":"petrol", "stroke":15, "capacity":1359}' \\
                -I - file_frmt=JSON orient=values -c RPM P FC \\
                -O engine_map.txt encoding=UTF-8


    Now, if input vectors are in 2 separate files, the 1st, 'engine_1.xlsx',
    having 5 columns with different headers than expected, like this:
        OTHER1   OTHER2       N        "Fuel waste"   OTHER3
        0       -1            12       0.14           "some text"
        ...

    and the 2nd having 2 columns with no headers at all and
    the 1st column being 'Pnorm', then it, then use the following command:

        >> %(prog)s -O engine_map -m fuel=petrol \\
                -I=engine_1.xlsx sheetname+=0 \\
                -c X   X   N   'Fuel consumption'  X \\
                -r X   X   RPM 'FC(g/s)'           X \\
                -I=engine_2.csv header@=None \\
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
    except SystemExit:
        log.error('Invalid args: %s', argv)
        raise

    try:
        DEBUG = bool(opts.debug)

        if (DEBUG or opts.verbose > 1):
            opts.strict = True

        if opts.verbose == 1:
            log.setLevel(logging.INFO)
        else:
            log.setLevel(logging.WARNING)

        log.debug("Args: %s\n  +--Opts: %s", argv, opts)

        opts = validate_file_opts(opts)

        infiles     = parse_many_file_args(opts.I, 'r')
        log.info("Input-files: %s", infiles)

        outfiles    = parse_many_file_args(opts.O, 'w')
        log.info("Output-files: %s", outfiles)

    except (ValueError) as ex:
        if DEBUG:
            log.exception('Cmd-line parsing failed!')
        indent = len(program_name) * " "
        parser.exit(3, "%s: %s\n%s  for help use --help\n"%(program_name, ex, indent))

    ## Main program
    #
    try:
        additional_props = not opts.strict
        mdl = assemble_model(infiles, opts.m)
        log.info("Input Model(strict: %s): %s", opts.strict, Lazy(lambda: json_dumps(mdl, 'to_string')))
        mdl = validate_model(mdl, additional_props)

        mdl = run_processor(opts, mdl)

        store_model_parts(mdl, outfiles)

    except jsons.ValidationError as ex:
        if DEBUG:
            log.error('Invalid input model!', exc_info=ex)
        indent = len(program_name) * " "
        parser.exit(4, "%s: Model validation failed due to: %s\n%s\n"%(program_name, ex, indent))

    except jsonp.JsonPointerException as ex:
        if DEBUG:
            log.exception('Invalid model operation!')
        indent = len(program_name) * " "
        parser.exit(4, "%s: Model operation failed due to: %s\n%s\n"%(program_name, ex, indent))




## The value of file_frmt=VALUE to decide which
#    pandas.read_XXX() and write_XXX() methods to use.
#
#_io_file_modes = {'r':0, 'rb':0, 'w':1, 'wb':1, 'a':1, 'ab':1}
_io_file_modes = {'r':0, 'w':1}
_read_clipboard_methods = (pd.read_clipboard, 'to_clipboard')
_default_pandas_format  = 'AUTO'
_pandas_formats = collections.OrderedDict([
    ('AUTO', None),
    ('CSV', (pd.read_csv, 'to_csv')),
    ('TXT', (pd.read_csv, 'to_csv')),
    ('XLS', (pd.read_excel, 'to_excel')),
    ('JSON', (pd.read_json, 'to_json')),
    ('SERIES', (pd.Series.from_csv, 'to_json')),
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


_default_df_path            = ('/engine_points', '/engine_map')
_default_out_file_append    = False
## When option `-m MODEL_PATH=VALUE` contains a relative path,
# the following is preppended:
_default_model_overridde_path = '/engine/'


_value_parsers = {
    '+': int,
    '*': float,
    '?': str2bool,
    ':': json.loads,
    '@': ast.literal_eval ## best-effort security: http://stackoverflow.com/questions/3513292/python-make-eval-safe
}


_key_value_regex = re.compile(r'^\s*([/_A-Za-z][\w/\.]*)\s*([+*?:@]?)=\s*(.*?)\s*$')
def parse_key_value_pair(arg):
    """Argument-type for syntax like: KEY [+*?:]= VALUE."""

    m = _key_value_regex.match(arg)
    if m:
        (key, type_sym, value) = m.groups()
        if type_sym:
            try:
                value   = _value_parsers[type_sym](value)
            except Exception as ex:
                raise argparse.ArgumentTypeError("Failed parsing key(%s)%s=VALUE(%s) due to: %s" %(key, type_sym, value, ex)) from ex

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


FileSpec = collections.namedtuple('FileSpec', ('io_method', 'fname', 'file', 'frmt', 'path', 'append', 'kws'))

def parse_many_file_args(many_file_args, filemode):
    io_file_indx = _io_file_modes[filemode]

    def parse_file_args(fname, *kv_args):
        frmt    = _default_pandas_format
        dest    = _default_df_path[io_file_indx]
        append  = _default_out_file_append

        kv_pairs = [parse_key_value_pair(kv) for kv in kv_args]
        pandas_kws = dict(kv_pairs)

        if ('file_frmt' in pandas_kws):
            frmt = pandas_kws.pop('file_frmt')
            if (frmt not in _pandas_formats):
                raise argparse.ArgumentTypeError("Unsupported pandas file_frmt: %s\n  Set 'file_frmt=XXX' to one of %s" % (frmt, list(_pandas_formats.keys())[1:]))


        if (frmt == _default_pandas_format):
            if ('-' == fname or fname == '+'):
                frmt = 'CSV'
            else:
                frmt = get_file_format_from_extension(fname)
            if (not frmt):
                raise argparse.ArgumentTypeError("File(%s) has unknown extension, file_frmt is required! \n  Set 'file_frmt=XXX' to one of %s" % (fname, list(_pandas_formats.keys())[1:]))


        if (fname == '+'):
            method = _read_clipboard_methods[io_file_indx]
            file = ''
        else:
            methods = _pandas_formats[frmt]
            assert isinstance(methods, tuple), methods
            method = methods[io_file_indx]

            if (method == pd.read_excel):
                file = fname
            else:
                file = argparse.FileType(filemode)(fname)

        try:
            dest = pandas_kws.pop('model_path')
            if (len(dest) > 0 and not dest.startswith('/')):
                raise argparse.ArgumentTypeError('Only absolute dest-paths supported: %s' % (dest))
        except KeyError:
            pass

        try:
            append = pandas_kws.pop('file_append')
            append = str2bool(append)
        except KeyError:
            pass

        return FileSpec(method, fname, file, frmt, dest, append, pandas_kws)

    return [parse_file_args(*file_args) for file_args in many_file_args]


def load_file_as_df(filespec):
# FileSpec(io_method, fname, file, frmt, path, append, kws)
    method = filespec.io_method
    log.debug('Reading file with: pandas.%s(%s, %s)', method.__name__, filespec.fname, filespec.kws)
    if filespec.file is None:       ## ie. when reading CLIPBOARD
        dfin = method(**filespec.kws)
    else:
        dfin = method(filespec.file, **filespec.kws)

    dfin = dfin.convert_objects(convert_numeric=True)

    return dfin



def assemble_model(infiles, model_overrides):

    mdl = model.base_model()

    for filespec in infiles:
        try:
            dfin = load_file_as_df(filespec)
            log.debug("  +-input-file(%s):\n%s", filespec.fname, dfin)
            if filespec.path:
                jsonp.set_pointer(mdl, filespec.path, dfin)
            else:
                mdl = dfin
        except Exception as ex:
            raise Exception("Failed reading %s due to: %s" %(filespec.path, filespec, ex)) from ex

    if (model_overrides):
        model_overrides = functools.reduce(lambda x,y: x+y, model_overrides) # join all -m
        for (json_path, value) in model_overrides:
            try:
                if (not json_path.startswith('/')):
                    json_path = _default_model_overridde_path + json_path
                jsonp.set_pointer(mdl, json_path, value)
            except Exception as ex:
                raise Exception("Failed setting model-value(%s) due to: %s" %(json_path, value, ex)) from ex

    return mdl




def store_part_as_df(filespec, part):
    '''If part is Pandas, store it as it is, else, store it as json recursively.

        :param FileSpec filespec: named_tuple
        :param part: what to store, originating from model(filespec.path))
    '''

    if isinstance(part, NDFrame):
        log.debug('Writing file with: pandas.%s(%s, %s)', filespec.io_method, filespec.fname, filespec.kws)
        if filespec.file is None:       ## ie. when reading CLIPBOARD
            method = ops.methodcaller(filespec.io_method, **filespec.kws)
        else:
            method = ops.methodcaller(filespec.io_method, filespec.file, **filespec.kws)
        method(part)
    else:
        json_dump(part, filespec.file, pd_method=None, **filespec.kws)


_no_part=object()
def store_model_parts(mdl, outfiles):
    for filespec in outfiles:
        try:
            part = jsonp.resolve_pointer(mdl, filespec.path, _no_part)
            if part is _no_part:
                log.warning('Nothing found at model(%s) to write to file(%s).', filespec.path, filespec.fname)
            else:
                store_part_as_df(filespec, part)
        except Exception as ex:
            raise Exception("Failed storing %s due to: %s" %(filespec, ex)) from ex

class RawTextHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Help message formatter which retains formatting of all help text.

    Only the name of this class is considered a public API. All the methods
    provided by the class are considered an implementation detail.
    """

    def _split_lines(self, text, width):
        return text.splitlines()


def build_args_parser(program_name, version, desc, epilog):
    version_string  = '%%prog %s' % (version)

    parser = argparse.ArgumentParser(prog=program_name, description=desc, epilog=epilog, add_help=False,
                                     formatter_class=RawTextHelpFormatter)


    grp_io = parser.add_argument_group('Input/Output', 'Options controlling reading/writting of file(s) and for specifying model values.')
    grp_io.add_argument('-I', help=dedent("""\
            import file(s) into the model utilizing pandas-IO methods, see
                http://pandas.pydata.org/pandas-docs/stable/io.html
            Default: %(default)s]
            * The syntax of this option is like this:
                    FILENAME [KEY=VALUE ...]]
            * The FILENAME can be '-' to designate <stdin> or '+' to designate CLIPBOARD.
            * Any KEY-VALUE pairs pass directly to pandas.read_XXX() options,
              except from the following keys, which are consumed before reaching pandas:
                ** file_frmt = [ AUTO | CSV | TXT | XLS | JSON | SERIES ]
                  selects which pandas.read_XXX() method to use:
                    *** AUTO: the format is deduced from the filename's extension (ie Excel files).
                    *** JSON: different sub-formats are selected through the 'orient' keyword
                      of Pandas specified with a key-value pair
                      (see: http://pandas.pydata.org/pandas-docs/dev/generated/pandas.io.json.read_json.html).
                    *** SERIES: uses `pd.Series.from_csv()`.
                    *** Defaults to AUTO, unless reading <stdin> or <clipboard>, which then is CSV.
                ** model_path = MODEL_PATH
                  specifies the destination (or source) of the dataframe within the model
                  as json-pointer path (see -m option).
                  concatenated horizontally therefore the number of rows (excluding header)
                  If many input-files have the same --model_path, the dataframes are
                  for all those data-files must be equal.
            * When more input-files given, the number --icolumns and --irenames options,
              must either match them, be 1 (meaning use them for all files), or be totally absent
              (meaning use defaults for all files).
            * see REMARKS at the bottom regarding the parsing of KEY-VAULE pairs. """),
                        action='append', nargs='+', required=True,
                        #default=[('- file_frmt=%s model_path=%s'%('CSV', _default_df_dest)).split()],
                        metavar='ARG')
    grp_io.add_argument('-c', '--icolumns', help=dedent("""\
            describes the columns-contents of input file(s) along with their units (see --I).
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
            Default when files include headers is 0 (1st row), otherwise it is 'RPM,P,FC'."""),
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
    grp_io.add_argument('--strict', help=dedent("""\
            validate model more strictly, ie no additional-properties allowed.
            [default: %(default)s]"""),
            default=False, type=str2bool,
            metavar='[TRUE | FALSE]')
    grp_io.add_argument('-M', help=dedent("""\
            get help description for the specfied model path.
            If no path specified, gets the default model-base. """),
                        action='append', nargs='*',
                        type=parse_key_value_pair, metavar='MODEL_PATH')


    grp_io.add_argument('-O', help=dedent("""\
            specifies output-file(s) to write model-portions into after calculations.
            The syntax is indentical to -I, with these differences:
            * Instead of <stdin>, <stdout> and write_XXX() methods are used wherever.
            * One extra key-value pair:
            ** file_append = [ TRUE | FALSE ]
                    specify whether to augment pre-existing files, or overwrite them.
            * Default: - file_frmt=CSV model_path=/engine_map """),
                        action='append', nargs='+',
                        #default=[('- file_frmt=%s model_path=%s file_append=%s'%('CSV', _default_df_path[1],  _default_out_file_append)).split()],
                        metavar='ARG')


    grp_various = parser.add_argument_group('Various', 'Options controlling various other aspects.')
    #parser.add_argument('--gui', help='start in GUI mode', action='store_true')
    grp_various.add_argument('-d', "--debug", action="store_true", help=dedent("""\
            set debug-mode with various checks and error-traces
            Suggested combining with --verbose counter-flag.
            Implies --strict true
            [default: %(default)s] """),
                        default=False)
    grp_various.add_argument('-v', "--verbose", action="count", default=0, help="set verbosity level [default: %(default)s]")
    grp_various.add_argument("--version", action="version", version=version_string, help="prints version identifier of the program")
    grp_various.add_argument("--help", action="help", help='show this help message and exit')

    return parser


if __name__ == "__main__":
    sys.exit(main())
