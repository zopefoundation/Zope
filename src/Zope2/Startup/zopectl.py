#!python
##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""zopectl -- control Zope using zdaemon.

Usage: zopectl [options] [action [arguments]]

Options:
-h/--help -- print usage message and exit
-b/--backoff-limit SECONDS -- set backoff limit to SECONDS (default 10)
-d/--daemon -- run as a proper daemon; fork a subprocess, close files etc.
-f/--forever -- run forever (by default, exit when backoff limit is exceeded)
-h/--help -- print this usage message and exit
-i/--interactive -- start an interactive shell after executing commands
-l/--logfile -- log file to be read by logtail command
-u/--user -- run the daemon manager program as this user (or numeric id)
-m/--umask -- provide octal umask for files created by the managed process
-s/--socket-name -- socket between zopectl and zdrun
-t/--transcript FILE -- log file where to redirect stdout and stderr
action [arguments] -- see below

Actions are commands like "start", "stop" and "status".  If -i is
specified or no action is specified on the command line, a "shell"
interpreting actions typed interactively is started (unless the
configuration option default_to_interactive is set to false).  Use the
action "help" to find out about available actions.
"""

import csv
import os
import sys
import signal

import pkg_resources

import zdaemon
import Zope2.Startup

from zdaemon.zdctl import ZDCmd
from zdaemon.zdoptions import ZDOptions
from ZConfig.components.logger.handlers import FileHandlerFactory
from ZConfig.datatypes import existing_dirpath

if sys.version_info > (3, 0):
    basestring = str

WIN = False
if sys.platform[:3].lower() == "win":
    WIN = True


def string_list(arg):
    return arg.split()


def quote_command(command):
    print(" ".join(command))
    # Quote the program name, so it works even if it contains spaces
    command = " ".join(['"%s"' % x for x in command])
    if WIN:
        # odd, but true: the windows cmd processor can't handle more than
        # one quoted item per string unless you add quotes around the
        # whole line.
        command = '"%s"' % command
    return command


class ZopeCtlOptions(ZDOptions):
    # Zope controller options.
    #
    # After initialization, this should look very much like a
    # zdaemon.zdctl.ZDCtlOptions instance.  Many of the attributes are
    # initialized from different sources, however.

    __doc__ = __doc__

    positional_args_allowed = 1
    schemadir = os.path.dirname(Zope2.Startup.__file__)
    schemafile = "zopeschema.xml"
    uid = gid = None

    # this indicates that no explict program has been provided.
    # the command line option can set this.
    program = None

    # this indicates that no explict socket name has been provided.
    # the command line option can set this.
    sockname = None

    # XXX Suppress using Zope's <eventlog> section to avoid using the
    # same logging for zdctl as for the Zope appserver.  There still
    # needs to be a way to set a logfile for zdctl.
    logsectionname = None

    def __init__(self):
        ZDOptions.__init__(self)
        self.add("program", "runner.program", "p:", "program=",
                 handler=string_list)
        self.add("backofflimit", "runner.backoff_limit",
                 "b:", "backoff-limit=", int, default=10)
        self.add("daemon", "runner.daemon", "d", "daemon", flag=1, default=1)
        self.add("forever", "runner.forever", "f", "forever",
                 flag=1, default=0)
        self.add("hang_around", "runner.hang_around", default=0)
        self.add("interactive", None, "i", "interactive", flag=1)
        self.add("default_to_interactive", "runner.default_to_interactive",
                 default=1)
        self.add("logfile", None, "l:", "logfile=")
        self.add("user", "runner.user", "u:", "user=")
        self.add("prompt", "runner.prompt", default="zopectl>")
        self.add("umask", "runner.umask", "m:", "umask=")
        self.add("sockname", "runner.socket_name", "s:", "socket-name=",
                 existing_dirpath, default=None)
        self.add("transcript", "runner.transcript", "t:", "transcript=",
                 default="/dev/null")

    def realize(self, *args, **kw):
        ZDOptions.realize(self, *args, **kw)
        # Additional checking of user option; set uid and gid
        if self.user is not None:
            import pwd
            try:
                uid = int(self.user)
            except ValueError:
                try:
                    pwrec = pwd.getpwnam(self.user)
                except KeyError:
                    self.usage("username %r not found" % self.user)
                uid = pwrec[2]
            else:
                try:
                    pwrec = pwd.getpwuid(uid)
                except KeyError:
                    self.usage("uid %r not found" % self.user)
            gid = pwrec[3]
            self.uid = uid
            self.gid = gid

        config = self.configroot
        self.directory = config.instancehome
        self.clienthome = config.clienthome
        if self.program:
            if isinstance(self.program, basestring):
                self.program = [self.program]
        elif config.runner and config.runner.program:
            self.program = config.runner.program
        else:
            self.program = [os.path.join(self.directory, "bin", "runzope")]
        if self.sockname:
            # set by command line option
            pass
        elif config.runner and config.runner.socket_name:
            self.sockname = config.runner.socket_name
        else:
            self.sockname = os.path.join(self.clienthome, "zopectlsock")
        self.python = os.environ.get('PYTHON', config.python) or sys.executable
        self.zdrun = os.path.join(os.path.dirname(zdaemon.__file__),
                                  "zdrun.py")

        self.exitcodes = [0, 2]
        if self.logfile is None and config.eventlog is not None:
            for handler in config.eventlog.handler_factories:
                if isinstance(handler, FileHandlerFactory):
                    self.logfile = handler.section.path
                    if self.logfile not in ("STDERR", "STDOUT"):
                        break


class ZopeCmd(ZDCmd):

    _exitstatus = 0

    def _get_override(self, opt, name, svalue=None, flag=0):
        # Suppress the config file, and pass all configuration via the
        # command line.  This avoids needing to specialize the zdrun
        # script.
        if name == "configfile":
            return []
        value = getattr(self.options, name)
        if value is None:
            return []
        if flag:
            if value:
                args = [opt]
            else:
                args = []
        else:
            if svalue is None:
                svalue = str(value)
            args = [opt, svalue]
        return args

    def get_startup_cmd(self, python, more):
        cmdline = ('%s -c "from Zope2 import configure;'
                   'configure(%r);' %
                   (python, self.options.configfile)
                   )
        return cmdline + more + '\"'

    def do_debug(self, arg):
        cmdline = self.get_startup_cmd(self.options.python + ' -i',
                                       'import Zope2; app=Zope2.app()')
        print('Starting debugger (the name "app" is bound to the top-level '
              'Zope object)')
        os.system(cmdline)

    def do_foreground(self, arg):
        program = self.options.program
        local_additions = []
        if not program.count('-C'):
            local_additions += ['-C', self.options.configfile]
        if not program.count('-X'):
            local_additions += ['-X']
        if not program.count('debug-mode=on'):
            local_additions += ['debug-mode=on']
        program[1:1] = local_additions
        command = quote_command(program)
        try:
            return os.system(command)
        except KeyboardInterrupt:
            pass
        finally:
            for addition in local_additions:
                program.remove(addition)

    def help_debug(self):
        print("debug -- run the Zope debugger to inspect your database")
        print("         manually using a Python interactive shell")

    def __getattr__(self, name):
        """
        Getter to check if an unknown command is implement by an entry point.
        """
        if not name.startswith("do_"):
            raise AttributeError(name)
        data = list(pkg_resources.iter_entry_points(
            "zopectl.command", name=name[3:]))
        if not data:
            raise AttributeError(name)
        if len(data) > 1:
            sys.stderr.write(
                "Warning: multiple entry points found for command")
            return
        func = data[0].load()
        if not callable(func):
            sys.stderr.write("Error: %s is not a callable method" % name)
            return

        return self.run_entrypoint(data[0])

    def run_entrypoint(self, entry_point):
        def go(arg):
            # If the command line was something like
            # """bin/instance run "one two" three"""
            # cmd.parseline will have converted it so
            # that arg == 'one two three'. This is going to
            # foul up any quoted command with embedded spaces.
            # So we have to return to self.options.args,
            # which is a tuple of command line args,
            # throwing away the "run" command at the beginning.
            #
            # Further complications: if self.options.args has come
            # via subprocess, it may look like
            # ['run "arg 1" "arg2"'] rather than ['run','arg 1','arg2'].
            # If that's the case, we'll use csv to do the parsing
            # so that we can split on spaces while respecting quotes.
            tup = self.options.args
            if len(tup) == 1:
                tup = csv.reader(tup, delimiter=' ').next()

            # Remove -c and add command name as sys.argv[0]
            cmd = ['import sys',
                   'sys.argv.pop()',
                   'sys.argv.append(r\'%s\')' % entry_point.name
                   ]
            if len(tup) > 1:
                argv = tup[1:]
                for a in argv:
                    cmd.append('sys.argv.append(r\'%s\')' % a)
            cmd.extend([
                'import pkg_resources',
                'import Zope2',
                'func=pkg_resources.EntryPoint.parse(\'%s\').load(False)'
                % entry_point,
                'app=Zope2.app()',
                'func(app, sys.argv[1:])',
            ])
            cmdline = self.get_startup_cmd(
                self.options.python, ' ; '.join(cmd))
            self._exitstatus = os.system(cmdline)
        return go

    def do_run(self, args):
        if not args:
            print("usage: run <script> [args]")
            return
        # replace sys.argv
        script = args.split(' ')[0]
        cmd = (
            "import sys; sys.argv[:]=%r.split(' ');"
            "import Zope2; app=Zope2.app(); execfile(%r)"
        ) % (args, script)
        cmdline = self.get_startup_cmd(self.options.python, cmd)
        self._exitstatus = os.system(cmdline)

    def help_run(self):
        print("run <script> [args] -- run a Python script with the Zope ")
        print("                       environment set up. The script can use ")
        print("                       the name 'app' access the top-level ")
        print("                       Zope object")

    def do_adduser(self, arg):
        try:
            name, password = arg.split()
        except Exception:
            print("usage: adduser <name> <password>")
            return
        cmdline = self.get_startup_cmd(
            self.options.python,
            'import Zope2; '
            'app = Zope2.app(); '
            'result = app.acl_users._doAddUser('
            '\'%s\', \'%s\', [\'Manager\'], []); '
            'import transaction; '
            'transaction.commit(); '
            'print \'Created user:\', result'
        ) % (name, password)
        os.system(cmdline)

    def help_adduser(self):
        print("adduser <name> <password> -- add a Zope management user")


def main(args=None):
    # This is exactly like zdctl.main(), but uses ZopeCtlOptions and
    # ZopeCmd instead of ZDCtlOptions and ZDCmd, so the default values
    # are handled properly for Zope.
    options = ZopeCtlOptions()
    options.realize(args)
    c = ZopeCmd(options)
    if options.args:
        c.onecmd(" ".join(options.args))
    else:
        options.interactive = 1
    if options.interactive:
        try:
            import readline  # NOQA
        except ImportError:
            pass
        print("program:" + " ".join(options.program))
        c.do_status()
        c.cmdloop()
    else:
        return min(c._exitstatus, 1)


def _ignoreSIGCHLD(*unused):
    while 1:
        try:
            os.waitpid(-1, os.WNOHANG)
        except OSError:
            break


def run():
    # we don't care to be notified of our childrens' exit statuses.
    # this prevents zombie processes from cluttering up the process
    # table when zopectl start/stop is used interactively.
    # DM 2004-11-26: from the Linux "execve(2)" manual page:
    #     Any signals set to be caught by the calling process are reset
    #     to their default behaviour.
    #     The SIGCHLD signal (when set to SIG_IGN) may or may not be reset
    #     to SIG_DFL.
    #   If it is not reset, 'os.wait[pid]' can non-deterministically fail.
    #   Thus, use a way such that "SIGCHLD" is definitely reset in children.
    # signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    if not WIN and os.uname()[0] != 'Darwin':
        # On Windows the os.uname method does not exist.
        # On Mac OS X, setting up a signal handler causes waitpid to
        # raise EINTR, which is not preventable via the Python signal
        # handler API and can't be dealt with properly as we can't pass
        # the SA_RESTART to the signal API. Since Mac OS X doesn't
        # appear to clutter up the process table with zombies if
        # SIGCHILD is unset, just don't bother registering a SIGCHILD
        # signal handler at all.
        signal.signal(signal.SIGCHLD, _ignoreSIGCHLD)
    exitstatus = main()
    sys.exit(exitstatus)

if __name__ == '__main__':
    run()
