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
import argparse
from textwrap import dedent
import re
import fuefit
from argparse import RawTextHelpFormatter

DEBUG= False
TESTRUN = False
PROFILE = False

_key_value_regex = re.compile(r'^\s*([A-Za-z]\w*)\s*=\s*(.*)$')
def key_value_pair(arg):
    """Argument-type for -I and -O, syntaxed like: KEY=VALUE."""

    m = _key_value_regex.match(arg)
    if m:
        return m.groups()
    else:
        raise argparse.ArgumentTypeError("Not a KEY=VALUE syntax: %s"%arg)


_column_specifier_regex = re.compile(r'^\s*([^(]+)\s*(\(([^)]+)\))?\s*$')
def column_specifier(arg):
    """Argument-type for --icolumns, syntaxed like: COL_NAME [(UNITS)]."""

    m = _column_specifier_regex.match(arg)
    if m:
        return m.groups()
    else:
        raise argparse.ArgumentTypeError("Not a COLUMN_SPEC syntax: %s"%arg)


def main(argv=None):
    """The command-line entry-point for using all functionality of fuefit tool.

    REMARKS:
    --------
        * All string-values are case-insensitive.

    EXAMPLES:
    ---------
        Assuming a CSV-file 'engine_fc.csv' like this:
            CM,PMF,PME
            12,0.14,180
            ...

        then the next command  calculates and writes the fitted engine map's parameters
        as JSON into 'engine_map.json' file:
            %(prog)s --in-file engine_fc.csv -out-file engine_map
        and if header-row did not exist, it should become:
            %(prog)s -i engine_fc.csv -o engine_map --icolumns CM PMF PME
        and if instead of PME we had a column with normalized-Power in Watts (instead of kW):
            %(prog)s -i engine_fc.csv -o engine_map  -c CM  PMF 'Pnorm (w)'

        Now, if input vectors are in 2 separate files, the 1st, 'engine_1.xlsx',
        having 5 columns with different headers than expected, like this:
            OTHER1    OTHER2       N        "Fuel waste"     OTHER3
            0        -1            12         0.14           "some text"
            ...

        and the 2nd having 2 columns with no headers at all and the 1st one being 'Pnorm',
        then it would take the following to read them:
            %(prog)s -o engine_map \
                    -i=engine_1.xlsx \
                    -c X   X   N   'Fuel consumption'  X \
                    -r X   X   RPM 'FC(g/s)'           X \
                    -i=engine_2.csv \
                    -c Pnorm X

        To explicitly specify the encoding, the file-type and the separator character:
            %(prog)s -o engine_map.txt -O encoding=UTF-8 -i=engine_data -f csv -I 'sep=;' -I encoding=UTF-8
    """

    global DEBUG
    program_name    = 'fuefit' #os.path.basename(sys.argv[0])
    version_string  = '%%prog %s' % (fuefit._version)
    doc_lines       = main.__doc__.splitlines()
    desc            = doc_lines[0]
    epilog          = dedent('\n'.join(doc_lines[1:]))

    if argv is None:
        argv = sys.argv[1:]

    try:
        # setup option parser
        parser = argparse.ArgumentParser(prog=program_name, description=desc, epilog=epilog, add_help=False,
                                         formatter_class=RawTextHelpFormatter)
        grp_input = parser.add_argument_group('Input', 'Options controlling reading of input-file(s).')
        grp_input.add_argument('-i', '--ifile', help=dedent("""\
                the input-file(s) with the data-points (vectors).
                If more than one --ifile given, the number --iformat, --icolumns, --irename and -I options
                must either match it, be 1 (meaning use them for all files), or be totally absent
                (meaning use defaults for all files).
                The number of data-points (i.e. rows excluding header) for all data-files must be equal.
                Default: %(default)s"""),
                            type=argparse.FileType('r'), required=True,
                            action='append', metavar='FILE')
#                             type=argparse.FileType('r'), default=sys.stdin,
#                             action='append', metavar='FILE')
        grp_input.add_argument('-c', '--icolumns', help=dedent("""\
                describes the contents and the units of input file(s) (see --ifile).
                It must be followed either by an integer denoting the index of the header-row
                within the tabular data, or by a list of column-names specifications,
                obeying the following syntax:
                    COL_NAME [(UNITS)]
                Accepted quantities and their default units are grouped in 3+1 quantity-types and
                on each run exactly one from each of the 3 first categories must be present:
                1. engine-speed:
                    RPM      (rad/min)
                    RPMnorm  (rad/min)  : normalized against RPMnorm * RPM_IDLE + (RPM_RATED - RPM_RATED)
                    Omega    (rad/sec)
                    CM       (m/sec)
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
                            type=column_specifier, metavar='COLUMN_SPEC')
        grp_input.add_argument('-r', '--irename', help=dedent("""\
                renames the columns of input-file(s)  (see --ifile).
                It must be followed by a list of column-names specifications like --columns,
                but without accepting integers.
                The number of renamed-columns for each input-file must match those in the --icolumns.
                Use 'X' for columns not to be renamed."""),
                            action='append', nargs='+',
                            type=column_specifier, metavar='COLUMN_SPEC')
        grp_input.add_argument('-f', '--iformat', help=dedent("""\
                the format of input data file(s).
                It can be one of: %(choices)s
                When AUTO, format deduced fro the filename's extension (ie use it with Excel files).
                For explaination on the JSON formats see documentation of 'orient' keyword of Pandas.read_csv() method:
                    http://pandas.pydata.org/pandas-docs/stable/generated/pandas.io.json.read_json.html
                Default: %(default)s"""),
                            choices=[ 'AUTO', 'CSV', 'TXT', 'EXCEL', 'JSON_SPLIT', 'JSON_SPLIT', 'JSON_RECORDS', 'JSON_INDEX', 'JSON_COLUMNS', 'JSON_VALUES'],
                            default='AUTO', metavar='FORMAT')
        grp_input.add_argument('-I', help=dedent("""\
                Pass option(s) directly to pandas when reading input-file with syntax: -I 'opt=value, ...'"""),
                            nargs='+', type=key_value_pair, metavar='KEY=VALUE')


        grp_output = parser.add_argument_group('Output', 'Options controlling writting of output-file.')
        grp_output.add_argument('-o', '--ofile', help=dedent("""\
                the output-file to write results into.
                Default: %(default)s]"""),
                            default=sys.stdout,
                            metavar='FILE')
        grp_output.add_argument('-a', '--append', help=dedent("""\
                append results if output-file already exists.
                Default: %(default)s"""),
                            type=bool, default=True)
        grp_output.add_argument('-t', '--oformat', help=dedent("""\
                the file-format of the results (see --ofile).
                It can be one of: %(choices)s
                When AUTO, format deduced fro the filename's extension (ie use it with Excel files).
                If output-filename's extension omitted, CSV assumed.
                For explaination on the JSON formats see documentation of 'orient' keyword of Pandas.read_csv() method:
                    http://pandas.pydata.org/pandas-docs/stable/generated/pandas.io.json.read_json.html
                Default: %(default)s"""),
                            choices=[ 'AUTO', 'CSV', 'TXT', 'EXCEL', 'JSON_SPLIT', 'JSON_SPLIT', 'JSON_RECORDS', 'JSON_INDEX', 'JSON_COLUMNS', 'JSON_VALUES'],
                            default='AUTO', metavar='FORMAT')
        grp_input.add_argument('-O', help=dedent("""\
                Pass option(s) directly to pandas when reading input-file with syntax: -O 'opt=value, ...'"""),
                            nargs='+', type=key_value_pair, metavar='KEY=VALUE')


        grp_model = parser.add_argument_group('Model', 'Options specifying calculation constants and scalar model-values.')
        grp_model.add_argument('--model', help=dedent("""\
                read model base-values as JSON.
                Specific values can be overriden by options below.",
                """))
        grp_model.add_argument('--fuel', help="the engine's fuel-type used for selecting specific-temperature.  Default: %(default)s",
                            default='PETROL', choices=['PETROL', 'DIESEL'])
        grp_model.add_argument('--rpm-idle', help=dedent("""\
                the engine's n_idle.
                Required if RPMnorm exists in input-file's or example-map columns."""))
        grp_model.add_argument('--rpm-max', help=dedent("""\
                the engine's revolutions where rated power is attained.
                Required if RPMnorm exists in input-file's or example-map columns."""))
        grp_model.add_argument('--p-max', help=dedent("""\
                the engine's rated-power.
                Required if Pnorm or FCnorm exists in input-file's or example-map's columns."""))
        grp_model.add_argument('--stroke', help=dedent("""\
                the engine's stroke distance (default units: mm).
                Required if CM is not among the inputs or requested to generate example-map with RPM column."""))
        grp_model.add_argument('--capacity', help=dedent("""\
                the engine's capacity (default units: cm^2).
                Required if PMF is not among the inputs or requested to generate example-map with FC column."""))


        grp_various = parser.add_argument_group('Various', 'Options controlling various other aspects.')
        #parser.add_argument('--gui', help='start in GUI mode', action='store_true')
        grp_various.add_argument("--debug", action="store_true", help="set debug level [default: %(default)s]", default=False)
        grp_various.add_argument("--verbose", action="count", default=0, help="set verbosity level [default: %(default)s]")
        grp_various.add_argument("--version", action="version", version=version_string, help="prints version identifier of the program")
        grp_various.add_argument("--help", action="help", help='show this help message and exit')

        # process options
        opts = parser.parse_args(argv)

        if opts.debug:
            DEBUG = opts.debug
            print("debug = %d" % DEBUG)
        if opts.verbose > 0:
            print("verbosity level = %d" % opts.verbose)

        # MAIN BODY #
        print(opts)

    except (argparse.ArgumentError, argparse.ArgumentTypeError) as e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__ == "__main__":
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'twanky_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
