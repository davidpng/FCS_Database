"""
Created on Wed 07 Jan 2015 02:34:58 PM PST 
Assembles analysis scripts and provides top-level script.

Author: David Ng, MD
"""

import argparse
from argparse import RawDescriptionHelpFormatter
import logging
import pkgutil
import sys
from importlib import import_module
from FlowAnal import analysis_scripts, __version__ as version, __doc__ as docstring
from FlowAnal.utils import Opener

import logging
from os import path
import pandas as pd



log = logging.getLogger(__name__)

def action(arg):
    print "hello"

def build_parser(parser):
    """
    Create the argument parser
    """
    argv= sys.argv[1:]
    argv = [i for i in argv if i not in __name__.split('.')]

    #parser = argparse.ArgumentParser(description=docstring)

    parser.add_argument('-V', '--version', action='version',
                        version=version,
                        help='Print the version number and exit')
    parser.add_argument('-v', '--verbose',
                        action='count', dest='verbosity', default=1,
                        help='Increase verbosity of screen output (eg, -v is verbose, '
                        '-vv more so)')
    parser.add_argument('-q', '--quiet',
                        action='store_const', dest='verbosity', const=0,
                        help='Suppress output')
    parser.add_argument('--logfile', default=sys.stderr,
                        type=Opener('w'), metavar='FILE',
                        help='Write logging messages to FILE [default stderr]')

    ##########################
    # Setup all sub-commands #
    ##########################

    subparsers = parser.add_subparsers(dest='subparser_name', title='actions')

    # Begin help sub-command
    parser_help = subparsers.add_parser(
        'help', help='Detailed help for actions using `help <action>`')
    parser_help.add_argument('action', nargs=1)
    # End help sub-command

    # Organize submodules by argv
    modules = [name for _, name, _ in pkgutil.iter_modules(analysis_scripts.__path__)]

    modules = [m for m in modules if not m.startswith('_')]
    run = filter(lambda name: name in argv, modules)

    actions = {}

    # `run` will contain the module corresponding to a single
    # subcommand if provided; otherwise, generate top-level help
    # message from all submodules in `modules`.
    for name in run or modules:
        # set up subcommand help text. The first line of the dosctring
        # in the module is displayed as the help text in the
        # script-level help message (`script -h`). The entire
        # docstring is displayed in the help message for the
        # individual subcommand ((`script action -h`))
        # if no individual subcommand is specified (run_action[False]),
        # a full list of docstrings is displayed
        mod = import_module('{}.{}'.format(analysis_scripts.__name__, name))

        if mod.__doc__.strip():
            helpstr = mod.__doc__.lstrip().split('\n', 1)[0]
        else:
            helpstr = '<add help text in docstring>'
        
        subparser = subparsers.add_parser(name, help=helpstr,
                                          description=mod.__doc__,
                                          formatter_class=RawDescriptionHelpFormatter)

        mod.build_parser(subparser)

        actions[name] = mod.action

    # Determine we have called ourself (e.g. "help <action>")
    # Set arguments to display help if parameter is set
    #           *or*
    # Set arguments to perform an action with any specified options.
    print "IM HERE"
    print argv
    arguments = parser.parse_args(argv)

    # Determine which action is in play.
    action = arguments.subparser_name

    # Support help <action> by simply having this function call itself and
    # translate the arguments into something that argparse can work with.
    if action == 'help':
        return parse_arguments([str(arguments.action[0]), '-h'])

    return actions[action], arguments

"""
#def main(argv=None):
def action(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    action, arguments = parse_arguments(argv)

    loglevel = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }.get(arguments.verbosity, logging.DEBUG)

    if arguments.verbosity > 1:
        logformat = '%(levelname)s %(module)s %(lineno)s %(message)s'
    else:
        logformat = '%(message)s'

    logging.basicConfig(stream=arguments.logfile, format=logformat, level=loglevel)

    return action(arguments)
"""
