##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
    Zope appserver controller.  This is akin to apache's apachectl,
    except with an interactive interpreter if no commands are specified
    on the command-line.
"""

__version__ = '$Revision: 1.4 $'[11:-2]

import cmd
import getopt
import os
import signal
import sys
import time

try:
    import readline
except:
    readline = None

from Zope.Startup import getOptions, getOptionDescriptions, configure
from Zope.Startup.misc import TextBlockFormatter
from Zope.Startup.misc.lock_file import lock_file

USAGE = """\

zopectl:  Zope appserver controller

Usage:
    zopectl [-h | --help] [--config=filepath or url] [additional options]

Options:
    -h or --help       Print this message.  Not compatible with the 'start'
                       or 'restart' command.

    --config           Use an alternate configuration from a local file.
                       or a URL.  Default: 'zope.conf'.

                       If a URL is specified, it must begin with
                       'http://'.

                       File example: '/home/chrism/zope.conf'
                       URL example:  'http://www.zope.org/zope.conf'

Additional options:

%s

Commands:
    help [<command>]
    start
    stop
    restart
    logopenclose
    status
    show [<info>*]
    run <script_filename>
    debug
    write_inituser username password

    If no commands supplied, runs as an interactive read-eval-print
    interpreter.
"""

def start(config_location):
    """ Called by stub zopectl.py in an instance_home """
    _ZopeCtlCmd().main(config_location)

class ZopeCtl:
    """
        Workhorse engine for controlling the appserver.
    """
    config = None


    def __init__( self, reporter ):
        self._reporter = reporter

    #
    #   Command implementation
    #
    def start( self, arg ):
        """
            Start the Zope appserver.

            Syntax: start [arg1, arg2, ..]

            All arguments are passed to the zope.py command line.
        """
        lock_status = self.lockFile()
        if lock_status:
            self._report('Error:  cannot start Zope.  Another Zope '
                         'instance has locked the "%s" file.  Use "stop" '
                         'to stop it.' % self._getConfigValue('lock_filename'))
            self._report()
            return

        self._report('Starting Zope')
        opts = self._getCommandLineOpts()
        loc = self._getConfigLocation()
        if loc.find(' ') != -1:
            loc = '"%s"' % loc
        config_location = '--config=%s' % loc
        start_script = os.path.join(self._getSoftwareHome(), 'zope.py')
        start_script = cmdquote(start_script)
        args = [start_script] + [config_location] + opts + [arg]
        wait = self._getConfigValue('debug_mode')
        try:
            self._spawnPython(*args, **{'wait':wait})
        except KeyboardInterrupt:
            if not wait:
                raise

    def restart( self, arg ):
        """
            Restart the Zope appserver.

            Syntax:  restart
        """
        self.stop()
        time.sleep(3)
        self.start( arg )

    def quit(self, arg=None):
        """ Exit the controller. """
        self._report('Exiting')
        sys.exit(0)

    def logopenclose( self, arg=None ):
        """
            Open and close the Zope appserver logfiles.  Works only
            under a POSIX-compliant OS and under Zope 2.6+.

            Syntax: logopenclose
        """
        if os.name == 'posix':
            self._report('Opening and closing Zope logfiles')
            status = self._kill( signal.SIGUSR2)
            if status:
                self._report('Could not open and close logfiles (check event '
                             'log for further information)')
            else:
                self._report('Log files opened and closed successfully')
        else:
            self._report(
                'Cannot open and close logfiles on non-Posix platforms.'
                )

    def status( self, arg=None ):
        """
            Print a message showing the status of the Zope appserver,
            including:
            - Whether Zope is up or down
            - PIDs of appserver processes

            Syntax:  status
        """
        """
        Report on process ids
        """
        lock_status = self.lockFile()
        self._report('%-20s : %s' % ('Running', lock_status and 'yes' or 'no'))
        if not lock_status:
            return

        pidfile_name = self._getConfigValue('pid_filename')

        try:
            pids = get_pids(pidfile_name)
        except IOError:
            self._report('Pid file %s could not be found' % pidfile_name)
            self._report('Could not report status (maybe Zope isnt running?)')
            return

        self._report( '%-20s : %s' % ( 'Main PID', pids[0] ))

    def stop(self, arg=None):
        """
            Stop the Zope appserver, using the signal name passed in 'arg'.

            Syntax: stop
        """
        status = self._kill(signal.SIGTERM)
        if status:
            self._report('Could not stop Zope (maybe already stopped or '
                         'pending start?)')
        else:
            self._report('Zope stopped successfully')
        return status

    def shell(self, arg=None):
        """
            Run a command using the system shell.  Commands passed to zopectl
            which start with a '!' will also be interpreted by the
            system shell.

            Syntax: [ shell [command] | !command ]

            Examples:

            'shell vi zope.conf'
            '!vi zope.conf'
        """
        if sys.platform == 'win32':
            os.system('cmd "%s"' % arg)
        elif os.name == 'posix':
            os.system('sh -c "%s"' % arg)
        else:
            self._report('No shell known for system %s' % os.name)

    def _kill( self, sig):
        try:
            pidfile_name = self._getConfigValue('pid_filename')
            pids = get_pids(pidfile_name)
            pid = pids[-1]
        except IOError:
            self._report('Pid file %s could not be found' % pidfile_name)
            return 1
        status = kill(pid, sig)
        return status

    def show( self, what=None ):
        """
            Print a message showing all or part of the current
            Zope configuration.  'show' alone implies 'show config'.

            Syntax: show [option]

            Options:

              config        Combo of 'options', 'python', 'config-path' and
                            'command-line'

              command-line  Command-line opts that will be passed to zope.py
                            when 'start' is invoked

              options       All config-file specified options

              python        Python version and path info

              config-path   Filename or url used to obtain config data.
        """
        if type( what ) is type( '' ):
            what = what.split( ' ' )

        whatsit = {}
        KNOWN = (
            'python',
            'config',
            'command-line',
            'options',
            'config-path',
            )
        unknown = []

        for asked in what:
            if asked in KNOWN:
                whatsit[ asked ] = 1
            elif asked.strip():
                unknown.append( 'Unknown query: %s' % asked )

        if not whatsit:
            whatsit['config'] = 1

        if whatsit.get( 'config' ):
            whatsit[ 'options'   ] = 1
            whatsit[ 'command-line' ] = 1
            whatsit[ 'python'       ] = 1
            whatsit[ 'config-path'  ] = 1

        for unk in unknown:
            self._report( unk )

        if whatsit.get( 'python' ):
            self._showPython()

        if whatsit.get( 'config-path' ):
            self._showConfigPath()

        if whatsit.get( 'command-line' ):
            self._showCommandLine()

        if whatsit.get( 'options' ):
            self._showConfigValues()

    def _getRunCmd(self):
        swhome = self._getSoftwareHome()
        return(
            "import os, sys; os.environ['EVENT_LOG_SEVERITY']='300'; "
            "sys.path.insert(0, '%s'); from Zope.Startup import configure; "
            "configure('%s', %s); import Zope; app=Zope.app()"
            % ( swhome, self._getConfigLocation(), self._getCommandLineOpts())
            )

    def run( self, arg ):
        """
            Run a Python script, connected to the Zope appserver.

            Syntax: run [script_path]
        """
        cmd = self._getRunCmd() + "; execfile( '%s' )" % arg
        cmd = cmdquote(cmd)
        self._report( 'Running script: %s' % arg )
        try:
            status = self._spawnPython('-c', cmd)
        except KeyboardInterrupt:
            pass

    def debug( self, arg ):
        """
            Start a Python interpreter connected to the Zope appserver.

            Syntax: debug
        """
        cmd = self._getRunCmd()
        cmd = cmdquote(cmd)
        msg = ('Starting debugger.  The name "app" will be bound to the Zope '
               '"root object" when you enter interactive mode.')
        self._report( msg )
        try:
            status = self._spawnPython('-i', '-c', cmd)
        except KeyboardInterrupt:
            pass

    def write_inituser( self, args ):
        """
            Write a file named 'inituser' to the current directory with
            the username and password specified as arguments.  Writing this
            file to a new instance home directory will bootstrap the instance
            home for login with an initial username/password combination.

            Syntax: write_inituser username password
        """
        fname = 'inituser'
        from Zope.Startup.misc import zpasswd
        if type( args ) is type( '' ):
            args = args.split( ' ' )
        if len(args) != 2:
            self._report('Syntax:  write_inituser username password')
            return
        username, password = args
        password = zpasswd.generate_passwd(password, 'SHA')
        try:
            inituser = open(fname, 'w')
        except IOError:
            self._report('Could not open %s file (permissions?)' % fname)
            return
        inituser.write('%s:%s' % (username, password))
        self._report('Wrote %s' % os.path.abspath(fname))

    def reload(self, args):
        """
            Reload your Zope configuration file.
        """
        self._reconfigure()
        self._report('Reloaded configuration from %s' %
                     self._getConfigLocation())

    #
    #   Helper functions
    #

    def _report( self, msg='', level=1 ):
        msg = TextBlockFormatter.format(msg, max_width=73, indent=6)
        self._reporter( msg, level )

    def _help( self, method_name ):
        self._report( normalizeDocstring( getattr( self, method_name ) ) )

    def _reconfigure(self):
        self._config = configure(self._config_location,
                                 self._getCommandLineOpts())

    def _setConfigLocation(self, config_location):
        self._config_location = config_location

    def _getConfigLocation(self):
        return self._config_location

    def _getSoftwareHome(self):
        return self._getConfigValue('software_home')

    def _getConfigValue(self, name):
        return getattr(self._config, name)

    def _setCommandLineOpts( self, l ):
        self._cmdline = l

    def _getCommandLineOpts(self):
        return self._cmdline

    def _spawnPython(self, *args, **kw):
        if not kw.has_key('wait'):
            startup = os.P_WAIT
        elif kw.has_key('wait') and kw['wait']:
            startup = os.P_WAIT
        else:
            startup = os.P_NOWAIT
        args = list(args)
        args = [sys.executable] + args
        status = os.spawnv(startup, sys.executable, args)
        return status

    def _checkService( self, host, port, socket_path=None ):
        """
            Return 1 if server is found at (host, port), 0 otherwise.
        """
        import socket

        if socket_path is None:
            address = ( host, int(port) )
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            address = socket_path
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            s.connect( address )
        except socket.error:
            return 0
        else:
            return 1

    def _showDict( self, d ):

        if d:
            keys = [ ( k.lower(), k ) for k in d.keys() ]
            keys.sort()
            for kl, k in keys:
                self._report( '%-20s : %s' % ( k, d[ k ] ) )
        else:
            self._report( 'Unknown!' )

    def _showPython( self ):
        self._report()
        self._report( 'Python Information:' )
        self._report()

        info = sys.version_info
        version = '%d.%d' % ( info[0], info[1] )
        if info[2]:
            version += '.%d' % info[2]
        if info[4]:
            version += ' (%s-%d)' % ( info[3], info[4] )
        else:
            version += ' (%s)' % info[3]
        self._report( '%-20s : %s' % ( 'Version', version ) )
        self._report( '%-20s : %s' % ( 'Platform', sys.platform ) )
        self._report( '%-20s : %s' % ( 'Executable', sys.executable ) )

        self._report( '%-20s : %s' % ( 'Working directory'
                                       , os.getcwd() ) )
        self._report( '%-20s :' % 'Path' )
        self._report()
        for p in sys.path:
            self._report( '    %s' %  p )
        self._report()

    def _showConfigPath( self ):
        self._report()
        self._report('Configuration Path: %s' % self._getConfigLocation())
        self._report()

    def _showConfigValues( self ):
        self._report()
        self._report( 'Config-file specified values:' )
        self._report()
        self._report( str(self._config) )
        self._report()

    def _showCommandLine(self):
        self._report()
        self._report('Command Line:')
        self._report()
        self._report(' '.join(self._getCommandLineOpts()))
        self._report()

    def lockFile(self):
        filename = self._getConfigValue('lock_filename')
        if not os.path.exists(filename):
            return 0
        file = open(filename, 'r+')
        try:
            lock_file(file)
        except:
            return 1
        return 0

def normalizeDocstring(obj):
    """Remove leading and trailing whitespace from each line of a docstring."""
    lines = [line.strip() for line in obj.__doc__.split('\n')]
    return '\n'.join(lines)

def _MAKEDO( command ):
    """
        Work around insistence of 'Cmd.help' on printing docstrings with
        full indentation;  we fabricate a function which has the docstring
        it expects, using the one from ZopeCtl as a starting point;
        the generated function is suitable for use as 'do_command' within
        the Cmd-derived class.
    """

    def xdo( self, args=None, command=command ):
        getattr( self._engine, command )( args )

    xdo.func_doc = normalizeDocstring( getattr( ZopeCtl, command ) )

    return xdo

#
#   Read-eval-print interpreter
#
class _ZopeCtlCmd( cmd.Cmd ):
    """
        Interactive command processor.
    """
    def __init__( self, completekey='tab', prompt='zopectl> ', verbosity=1 ):
        self.cmdqueue = []
        if completekey and readline:
            readline.set_completer(self.complete)
            readline.parse_and_bind(completekey + ': complete')
        self._engine    = ZopeCtl( self._report )
        self.prompt     = prompt
        self._verbosity = verbosity

    def _report( self, msg='', level=1 ):

        if self._verbosity >= level:
            print msg

    def emptyline(self):
        pass

    def default( self, line ):
        if line == 'EOF':
            self._report()
            return 1

        try:
            tokens = line.split()
            method, args = tokens[0], ' '.join( tokens[1:] )
            method = getattr( self._engine, method, None )
            if method is not None:
                method( args )
                return None
        except:
            pass

        return cmd.Cmd.default( self, line )

    def parseline(self, line):
        line = line.strip()
        if not line:
            return None, None, line
        elif line[0] == '?':
            line = 'help ' + line[1:]
        elif line[0] == '!':
            if hasattr(self, 'do_shell'):
                line = 'shell ' + line[1:]
            else:
                return None, None, line
        i, n = 0, len(line)
        while i < n and line[i] in self.identchars: i = i+1
        cmd, arg = line[:i], line[i:].strip()
        return cmd, arg, line

    def completedefault(self, *ignored):
        return []

    def completenames(self, text, *ignored):
        dotext = 'do_'+text
        return [a[3:] for a in self.get_names() if a.startswith(dotext)]

    def complete(self, text, state):
        """Return the next possible completion for 'text'.

        If a command has not been entered, then complete against command list.
        Otherwise try to call complete_<command> to get list of completions.
        """
        if state == 0:
            import readline
            origline = readline.get_line_buffer()
            line = origline.lstrip()
            stripped = len(origline) - len(line)
            begidx = readline.get_begidx() - stripped
            endidx = readline.get_endidx() - stripped
            if begidx>0:
                cmd, args, foo = self.parseline(line)
                if cmd == '':
                    compfunc = self.completedefault
                else:
                    try:
                        compfunc = getattr(self, 'complete_' + cmd)
                    except AttributeError:
                        compfunc = self.completedefault
            else:
                compfunc = self.completenames
            self.completion_matches = compfunc(text, line, begidx, endidx)
        try:
            return self.completion_matches[state]
        except IndexError:
            return None

    def get_names(self):
        # Inheritance says we have to look in class and
        # base classes; order is not important.
        names = []
        classes = [self.__class__]
        while classes:
            aclass = classes[0]
            if aclass.__bases__:
                classes = classes + list(aclass.__bases__)
            names = names + dir(aclass)
            del classes[0]
        return names

    def complete_help(self, *args):
        return self.completenames(*args)

    def complete_show(self, text, *ignored):
        meta = ['config', 'options', 'python', 'command-line',
                'config-path']
        return [a for a in meta if a.startswith(text) ]

    do_start          = _MAKEDO( 'start' )
    do_restart        = _MAKEDO( 'restart' )
    do_logopenclose   = _MAKEDO( 'logopenclose' )
    do_stop           = _MAKEDO( 'stop' )
    do_status         = _MAKEDO( 'status' )
    do_show           = _MAKEDO( 'show' )
    do_run            = _MAKEDO( 'run' )
    do_debug          = _MAKEDO( 'debug' )
    do_quit           = _MAKEDO( 'quit' )
    do_shell          = _MAKEDO( 'shell' )
    do_write_inituser = _MAKEDO( 'write_inituser')
    do_reload         = _MAKEDO( 'reload' )

    #
    #   Command-line processing
    #
    def usage( self ):
        opts = getOptionDescriptions()
        self._report( USAGE % opts)

    def main( self, config_location ):
        # add relevant options to options list
        longopts = [ "help", "config="]
        shortopts = "h"
        start_shortopts, start_longopts = getOptions()
        optcopy = sys.argv[1:]

        try:
            opts, args = getopt.getopt(optcopy, start_shortopts+shortopts,
                                       start_longopts+longopts)
        except getopt.GetoptError, v:
            print v
            self.usage()
            sys.exit(127)

        for k, v in opts:
            if k in ('-h', '--help'):
                self.usage()
                sys.exit(0)
            elif k == '--config':
                config_location = v
                i = 0
                # remove --config= from optcopy
                for item in optcopy:
                    if item.startswith('--config='):
                        break
                    i = i + 1
                optcopy.pop(i)
        self._engine._setConfigLocation(config_location)
        if not args:
            self._engine._setCommandLineOpts(optcopy)
        else:
            self._engine._setCommandLineOpts(optcopy[len(args):])
        self._engine._reconfigure()
        if args:
            self.cmdqueue.append(' '.join(args))
            self.cmdqueue.append('EOF')

        self.cmdloop()

def get_pids(filename):
    for line in open(filename).readlines():
        pids = line.split()
        if pids:
            return [ int(x.strip()) for x in pids ]

def win32kill(pid, sig):
    # we ignore the signal on win32
    try:
        import win32api
        import pywintypes
    except:
        print ("Could not open win32api module, have you installed the "
               "'win32all' package?")
        return 1
    try:
        handle = win32api.OpenProcess(1, 0, pid)
    except pywintypes.error, why:
        # process named by pid not running
        return 1
    try:
        status = win32api.TerminateProcess(handle, 0)
    except:
        return 1
    if status is None:
        return 0
    return 1

def kill(pid, sig):
    try:
        os.kill(pid, sig)
    except OSError, why:
        return 1
    else:
        return 0

def cmdquote(cmd):
    if sys.platform == 'win32':
        # ugh.  win32 requires the command to be quoted.  unix requires
        # that the command *not* be quoted.
        cmd = '"%s"' % cmd
    return cmd

if sys.platform == 'win32':
    kill = win32kill
