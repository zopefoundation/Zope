# (c) 2005 Ian Bicking and contributors; written for Paste
# (http://pythonpaste.org) Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license.php
#
# For discussion of daemonizing:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/278731
#
# Code taken also from QP: http://www.mems-exchange.org/software/qp/ From
# lib/site.py
#
# Code further taken from:
# https://github.com/Pylons/pyramid/blob/master/pyramid/scripts/pserve.py and
# https://github.com/Pylons/pyramid/blob/master/pyramid/paster.py
# licensed under the BSD-derived Repoze Public License
# (http://repoze.org/license.html).

import configparser
import optparse
import os
import re
import sys
from logging.config import fileConfig

from paste.deploy import loadapp
from paste.deploy import loadserver

import Zope2
from App.config import getConfiguration


def parse_vars(args):
    """
    Given variables like ``['a=b', 'c=d']`` turns it into ``{'a':
    'b', 'c': 'd'}``
    """
    result = {}
    for arg in args:
        if '=' not in arg:
            raise ValueError(
                'Variable assignment %r invalid (no "=")'
                % arg)
        name, value = arg.split('=', 1)
        result[name] = value
    return result


def _getpathsec(config_uri, name):
    if '#' in config_uri:
        path, section = config_uri.split('#', 1)
    else:
        path, section = config_uri, 'main'
    if name:
        section = name
    return path, section


def setup_logging(config_uri, global_conf=None,  # NOQA
                  fileConfig=fileConfig,
                  configparser=configparser):
    """
    Set up logging via :func:`logging.config.fileConfig` with the filename
    specified via ``config_uri`` (a string in the form
    ``filename#sectionname``).
    ConfigParser defaults are specified for the special ``__file__``
    and ``here`` variables, similar to PasteDeploy config loading.
    Extra defaults can optionally be specified as a dict in ``global_conf``.
    """
    path, _ = _getpathsec(config_uri, None)
    parser = configparser.ConfigParser()
    parser.read([path])
    if parser.has_section('loggers'):
        config_file = os.path.abspath(path)
        full_global_conf = dict(
            __file__=config_file,
            here=os.path.dirname(config_file))
        if global_conf:
            full_global_conf.update(global_conf)
        return fileConfig(
            config_file, full_global_conf, disable_existing_loggers=False)


class ServeCommand:

    usage = '%prog config_uri [var=value]'
    description = """\
This command serves a web application that uses a PasteDeploy
configuration file for the server and application.
You can also include variable assignments like 'http_port=8080'
and then use %(http_port)s in your config files.
    """
    default_verbosity = 1

    parser = optparse.OptionParser(
        usage,
        description=description
    )
    parser.add_option(
        '-n', '--app-name',
        dest='app_name',
        metavar='NAME',
        help="Load the named application (default main)")
    parser.add_option(
        '-s', '--server',
        dest='server',
        metavar='SERVER_TYPE',
        help="Use the named server.")
    parser.add_option(
        '--server-name',
        dest='server_name',
        metavar='SECTION_NAME',
        help=("Use the named server as defined in the configuration file "
              "(default: main)"))
    parser.add_option(
        '-v', '--verbose',
        default=default_verbosity,
        dest='verbose',
        action='count',
        help="Set verbose level (default " + str(default_verbosity) + ")")
    parser.add_option(
        '-q', '--quiet',
        action='store_const',
        const=0,
        dest='verbose',
        help="Suppress verbose output")
    parser.add_option(
        '-d', '--debug',
        action='store_const',
        const=1,
        dest='debug',
        help="Enable debug mode.")
    parser.add_option(
        '-e', '--debug-exceptions',
        action='store_const',
        const=1,
        dest='debug_exceptions',
        help="Enable exceptions debug mode.")

    _scheme_re = re.compile(r'^[a-z][a-z]+:', re.I)

    def __init__(self, argv, quiet=False):
        self.options, self.args = self.parser.parse_args(argv[1:])
        if quiet:
            self.options.verbose = 0

    def out(self, msg):
        if self.options.verbose > 0:
            print(msg)

    def get_options(self):
        restvars = self.args[1:]
        return parse_vars(restvars)

    def run(self):
        if not self.args:
            self.out('You must give a config file')
            return 2
        app_spec = self.args[0]
        app_name = self.options.app_name

        vars = self.get_options()

        if not self._scheme_re.search(app_spec):
            app_spec = 'config:' + app_spec
        server_name = self.options.server_name
        if self.options.server:
            server_spec = 'egg:Zope2'
            assert server_name is None
            server_name = self.options.server
        else:
            server_spec = app_spec
        base = os.getcwd()

        log_fn = app_spec
        if log_fn.startswith('config:'):
            log_fn = app_spec[len('config:'):]
        elif log_fn.startswith('egg:'):
            log_fn = None
        if log_fn:
            log_fn = os.path.join(base, log_fn)
            setup_logging(log_fn, global_conf=vars)

        server = self.loadserver(server_spec, name=server_name,
                                 relative_to=base, global_conf=vars)

        if 'debug_mode' not in vars and self.options.debug:
            vars['debug_mode'] = 'true'
        if 'debug_exceptions' not in vars and self.options.debug_exceptions:
            vars['debug_exceptions'] = 'true'
        app = self.loadapp(app_spec, name=app_name, relative_to=base,
                           global_conf=vars)

        if self.options.verbose > 0:
            if hasattr(os, 'getpid'):
                msg = 'Starting server in PID %i.' % os.getpid()
            else:
                msg = 'Starting server.'
            self.out(msg)

        def serve():
            self.makePidFile()

            try:
                server(app)
            except (SystemExit, KeyboardInterrupt) as e:
                if self.options.verbose > 1:
                    raise
                if str(e):
                    msg = ' ' + str(e)
                else:
                    msg = ''
                self.out('Exiting%s (-v to see traceback)' % msg)
            finally:
                for db in Zope2.opened:
                    db.close()
                self.unlinkPidFile()

        serve()

    def loadapp(self, app_spec, name, relative_to, **kw):
        return loadapp(app_spec, name=name, relative_to=relative_to, **kw)

    def loadserver(self, server_spec, name, relative_to, **kw):
        return loadserver(
            server_spec, name=name, relative_to=relative_to, **kw)

    def makePidFile(self):
        options = getConfiguration()
        try:
            IO_ERRORS = (IOError, OSError, WindowsError)
        except NameError:
            IO_ERRORS = (IOError, OSError)

        try:
            if os.path.exists(options.pid_filename):
                os.unlink(options.pid_filename)
            with open(options.pid_filename, 'w') as fp:
                fp.write(str(os.getpid()))
        except IO_ERRORS:
            pass

    def unlinkPidFile(self):
        options = getConfiguration()
        try:
            os.unlink(options.pid_filename)
        except OSError:
            pass


def main(argv=sys.argv, quiet=False):
    command = ServeCommand(argv, quiet=quiet)
    return command.run()


if __name__ == '__main__':
    sys.exit(main() or 0)
