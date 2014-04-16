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

import sys, os
import argparse
from textwrap import dedent
import fuefit
from argparse import RawDescriptionHelpFormatter, RawTextHelpFormatter

DEBUG= False
TESTRUN = False
PROFILE = False


def main(argv=None):
    '''The command-line entry-point for using all functionality of fuefit tool. '''

    global DEBUG
    program_name = os.path.basename(sys.argv[0])

    program_version_string = '%%prog %s' % (fuefit._version)
    examples = dedent("""\
            REMARKS:
            --------
                * All strings are case-insensitive.

            EXAMPLES:
            ---------
                Assuming a CSV-file 'engine_fc.csv':
                    CM,PMF,PME
                    12,0.14,180
                    ...

                then the next command would calculate and write the fitted engine map's parameters
                as JSON into 'engine_map.json' file:
                    %(prog)s --in-file engine_fc.csv -out-file engine_map
                and if header-row did not exist, it should become:
                    %(prog)s -i engine_fc.csv -o engine_map --in-columns CM PMF PME
                and if instead of PME we had a column with normalized-Power in Watts (instead of kW):
                    %(prog)s -i engine_fc.csv -o engine_map  -c CM  PMF 'Pnorm (w)'
                Now, if vectors were in 2 separate files:
                    %(prog)s -o engine_map -i=engine_1.csv -c RPM FC -i=engine_2.csv -c Pnorm
    """)

    if argv is None:
        argv = sys.argv[1:]

    try:
        # setup option parser
        parser = argparse.ArgumentParser(prog='fuefit', description=__doc__, epilog=examples, formatter_class=RawTextHelpFormatter)
        parser.add_argument('-i', '--ifile', help=dedent("""\
                the input-file(s) with the data-points (vectors).
                If more than one --data given, the number of each (--in-format, --in-columns, --in-encoding)
                options must either match it, be 1 (meaning use them for all files), or
                be totally absent (meaning use defaults for all files).
                The number of data-points (i.e. rows excluding header) for all data-files must be equal."""),
                            type=argparse.FileType('r'), required=True,
                            action='append', metavar='FILE')
        parser.add_argument('-c', '--icolumns', help=dedent("""\
                describes the contents and the units of input file(s) (see --ifile).
                It can be either a (int) denoting the index of the header-row within the data, or
                a comma-separated list of column-names.
                Each column-name is a concatenation of the quantity name followed
                (optionally) by its units with any surrounding parethensis ignored.
                Accepted quantities and their default units are grouped in 3 quantity-types and
                on each run exactly one from each category  must be present:
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
                Default is  0, implying 1st row"""),
                            action='append', metavar='HEADER')
        parser.add_argument('-t', '--in-format', help=dedent('''\
                the format of input data file(s).
                It can be one of: %(choices)s
                When AUTO, format deduced fro the filename's extension (ie use it with Excel files).
                For explaination on the JSON formats see documentation of 'orient' keyword of Pandas.read_csv() method:
                    http://pandas.pydata.org/pandas-docs/stable/generated/pandas.io.json.read_json.html
                Default: %(default)s'''),
                            choices=[ 'AUTO', 'CSV', 'TXT', 'EXCEL', 'JSON_SPLIT', 'JSON_SPLIT', 'JSON_RECORDS', 'JSON_INDEX', 'JSON_COLUMNS', 'JSON_VALUES'],
                            default='AUTO', metavar='FORMAT')
        parser.add_argument('--in-enc', help='the encoding for input-file(s)', metavar='ENCODING')
        parser.add_argument('-o', '--ofile', help=dedent("""\
                the output-file to write results into.
                Default: %(default)s]"""),
                default=sys.stdout,
                metavar='FILE')
        parser.add_argument('-a', '--append', help=dedent("""\
                append results if output-file already exists.
                Default: %(default)s"""),
                type=bool, default=True)
        parser.add_argument('-r', '--oformat', help=dedent("""\
                the file-format of the results (see --ofile).
                It can be one of: %(choices)s
                When AUTO, format deduced fro the filename's extension (ie use it with Excel files).
                If output-filename's extension omitted, CSV assumed.
                For explaination on the JSON formats see documentation of 'orient' keyword of Pandas.read_csv() method:
                    http://pandas.pydata.org/pandas-docs/stable/generated/pandas.io.json.read_json.html
                Default: %(default)s"""),
                            choices=[ 'AUTO', 'CSV', 'TXT', 'EXCEL', 'JSON_SPLIT', 'JSON_SPLIT', 'JSON_RECORDS', 'JSON_INDEX', 'JSON_COLUMNS', 'JSON_VALUES'],
                            default='AUTO', metavar='FORMAT')
        parser.add_argument('--out-enc', help='the encoding for output-file', metavar='ENCODING')

        parser.add_argument('--fuel', help="the engine's fuel-type.  Default: %(default)s",
                            default='PETROL', choices=['PETROL', 'DIESEL'])
        parser.add_argument('--rpm-idle', help=dedent("""\
                the engine's n_idle.
                Required if RPMnorm exists in input-file's or example-map columns."""))
        parser.add_argument('--rpm-max', help=dedent("""\
                the engine's revolutions where rated power is attained.
                Required if RPMnorm exists in input-file's or example-map columns."""))
        parser.add_argument('--p-max', help=dedent("""\
                the engine's rated-power.
                Required if Pnorm or FCnorm exists in input-file's or example-map's columns."""))
        parser.add_argument('--stroke', help=dedent("""\
                the engine's stroke distance (default units: mm).
                Required if CM is not among the inputs or requested to generate example-map with RPM column."""))
        parser.add_argument('--capacity', help=dedent("""\
                the engine's capacity (default units: cm^2).
                Required if PMF is not among the inputs or requested to generate example-map with FC column."""))
        #parser.add_argument('--gui', help='start in GUI mode', action='store_true')

        parser.add_argument("--debug", action="store_true", help="set debug level [default: %(default)s]", default=False)
        parser.add_argument("--verbose", action="count", default=0, help="set verbosity level [default: %(default)s]")
        parser.add_argument("--version", action="version", version=program_version_string, help="prints version identifier of the program")

        # process options
        opts = parser.parse_args( )

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
