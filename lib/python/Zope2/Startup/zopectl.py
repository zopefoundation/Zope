#!python
##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
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
action [arguments] -- see below

Actions are commands like "start", "stop" and "status".  If -i is
specified or no action is specified on the command line, a "shell"
interpreting actions typed interactively is started (unless the
configuration option default_to_interactive is set to false).  Use the
action "help" to find out about available actions.
"""

import os
import sys
import signal

import zdaemon
import Zope2.Startup

from zdaemon.zdctl import ZDCmd
from zdaemon.zdoptions import ZDOptions
from ZConfig.components.logger.handlers import FileHandlerFactory
from ZConfig.datatypes import existing_dirpath


def string_list(arg):
    return arg.split()

class ZopeCtlOptions(ZDOptions):
    """Zope controller options.

    After initialization, this should look very much like a
    zdaemon.zdctl.ZDCtlOptions instance.  Many of the attributes are
    initialized from different sources, however.
    """

    positional_args_allowed = 1
    program = "zopectl"
    schemadir = os.path.dirname(Zope2.Startup.__file__)
    schemafile = "zopeschema.xml"
    uid = gid = None

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
        if config.runner and config.runner.program:
            self.program = config.runner.program
        else:
            self.program = [os.path.join(self.directory, "bin", "runzope")]
        if config.runner and config.runner.socket_name:
            self.sockname = config.runner.socket_name
        else:
            self.sockname = os.path.join(self.clienthome, "zopectlsock")
        self.python = sys.executable
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

    def do_start(self, arg):
        # signal to Zope that it is being managed
        #(to indicate it's web-restartable)
        os.putenv('ZMANAGED', '1')
        ZDCmd.do_start(self, arg)

    def get_startup_cmd(self, python, more):
        cmdline = ( '%s -c "from Zope2 import configure;'
                    'configure(\'%s\');' %
                    (python, self.options.configfile)
                    )
        return cmdline + more + '\"'

    def do_debug(self, arg):
        cmdline = self.get_startup_cmd(self.options.python + ' -i',
                                       'import Zope2; app=Zope2.app()')
        print ('Starting debugger (the name "app" is bound to the top-level '
               'Zope object)')
        os.system(cmdline)

    def do_foreground(self, arg):
        self.options.program[1:1] = ["-X", "debug-mode=on"]
        try:
            ZDCmd.do_foreground(self, arg)
        finally:
            self.options.program.remove("-X")
            self.options.program.remove("debug-mode=on")

    def help_debug(self):
        print "debug -- run the Zope debugger to inspect your database"
        print "         manually using a Python interactive shell"

    def do_run(self, arg):
        tup = arg.split(' ')
        if not arg:
            print "usage: run <script> [args]"
            return
        # remove -c and add script as sys.argv[0]
        script = tup[0]
        cmd = 'import sys; sys.argv.pop(); sys.argv.append(\'%s\');'  % script
        if len(tup) > 1:
            argv = tup[1:]
            cmd += '[sys.argv.append(x) for x in %s];' % argv
        cmd += 'import Zope2; app=Zope2.app(); execfile(\'%s\')' % script
        cmdline = self.get_startup_cmd(self.options.python, cmd)
        os.system(cmdline)

    def help_run(self):
        print "run <script> [args] -- run a Python script with the Zope "
        print "                       environment set up.  The script can use "
        print "                       the name 'app' access the top-level Zope"
        print "                       object"

    def do_adduser(self, arg):
        try:
            name, password = arg.split()
        except:
            print "usage: adduser <name> <password>"
            return
        cmdline = self.get_startup_cmd(
            self.options.python ,
            'import Zope2; '
            'app = Zope2.app(); '
            'app.acl_users._doAddUser(\'%s\', \'%s\', [\'Manager\'], []); '
            'import transaction; '
            'transaction.commit(); '
            ) % (name, password)
        os.system(cmdline)

    def help_adduser(self):
        print "adduser <name> <password> -- add a Zope management user"

    def do_test(self, arg):
        args = filter(None, arg.split(' '))

        # test.py lives in $ZOPE_HOME/bin
        zope_home = os.getenv('ZOPE_HOME')

        if zope_home is None:
            software_home = os.getenv('SOFTWARE_HOME')
            zope_home = os.path.abspath('%s/../..' % software_home)

        if not os.path.isdir(zope_home):
            print "Can't find test.py -- set ZOPE_HOME before running!"
            return

        script = os.path.join(zope_home, 'bin', 'test.py')
        if not os.path.exists(script):
            script = os.path.join(zope_home, 'test.py') # no inplace build!
        assert os.path.exists(script)

        # If --libdir is not supplied, use $INSTANCE_HOME/Products
        # (rather than $INSTANCE_HOME/lib/python)
        if '--libdir' not in args:
            args.insert(0, 'Products')
            args.insert(0, '--libdir')

        # Supply our config file by default.
        if '--config-file' not in args and '-C' not in args:
            args.insert(0, self.options.configfile)
            args.insert(0, '--config-file')

        # Default to dots.
        if '-v' not in args and '-q' not in args:
            args.insert(0, '-v')

        args.insert(0, script)
        args.insert(0, self.options.python)

        print 'Running tests via: %s' % ' '.join(args)
        pid = os.fork()
        if pid == 0:  # child
            os.execv(self.options.python, args)
        else:
            os.waitpid(pid, 0)

    def help_test(self):
        print "test [args]+ -- run unit / functional tests."
        print "                See $ZOPE_HOME/bin/test.py --help for syntax."


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
            import readline
        except ImportError:
            pass
        print "program:", " ".join(options.program)
        c.do_status()
        c.cmdloop()

def _ignoreSIGCHLD(*unused):
    while 1:
        try: os.waitpid(-1, os.WNOHANG)
        except OSError: break


if __name__ == "__main__":
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
    #signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    if os.uname()[0] != 'Darwin':
        # On Mac OS X, setting up a signal handler causes waitpid to
        # raise EINTR, which is not preventable via the Python signal
        # handler API and can't be dealt with properly as we can't pass
        # the SA_RESTART to the signal API. Since Mac OS X doesn't
        # appear to clutter up the process table with zombies if
        # SIGCHILD is unset, just don't bother registering a SIGCHILD
        # signal handler at all.
        signal.signal(signal.SIGCHLD, _ignoreSIGCHLD)
    main()
