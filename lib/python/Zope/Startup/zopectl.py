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
action [arguments] -- see below

Actions are commands like "start", "stop" and "status".  If -i is
specified or no action is specified on the command line, a "shell"
interpreting actions typed interactively is started (unless the
configuration option default_to_interactive is set to false).  Use the
action "help" to find out about available actions.
"""

import os
import sys

import zdaemon
import Zope.Startup

from zdaemon.zdctl import ZDCmd
from zdaemon.zdoptions import ZDOptions
from zLOG.datatypes import FileHandlerFactory


class ZopeCtlOptions(ZDOptions):
    """Zope controller options.

    After initialization, this should look very much like a
    zdaemon.zdctl.ZDCtlOptions instance.  Many of the attributes are
    initialized from different sources, however.
    """

    positional_args_allowed = 1
    program = "zopectl"
    schemadir = os.path.dirname(Zope.Startup.__file__)
    schemafile = "zopeschema.xml"

    # XXX Suppress using Zope's <eventlog> section to avoid using the
    # same logging for zdctl as for the Zope appserver.  There still
    # needs to be a way to set a logfile for zdctl.
    logsectionname = None

    def __init__(self):
        ZDOptions.__init__(self)
        self.add("backofflimit", "runner.backoff_limit",
                 "b:", "backoff-limit=", int, default=10)
        self.add("daemon", "runner.daemon", "d", "daemon", flag=1, default=0)
        self.add("forever", "runner.forever", "f", "forever",
                 flag=1, default=0)
        self.add("hang_around", "runner.hang_around", default=0)
        self.add("interactive", None, "i", "interactive", flag=1)
        self.add("default_to_interactive", "runner.default_to_interactive",
                 default=1)
        self.add("logfile", None, "l:", "logfile=")
        self.add("prompt", "runner.prompt", default="zopectl>")

    def realize(self, *args, **kw):
        ZDOptions.realize(self, *args, **kw)
        config = self.configroot
        self.directory = config.instancehome
        self.program = [os.path.join(self.directory, "bin", "runzope")]
        self.sockname = os.path.join(config.clienthome, "zopectlsock")
        self.user = None
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


def main(args=None):
    # This is exactly like zdctl.main(), but uses ZopeCtlOptions and
    # ZopeCmd instead of ZDCtlOptions and ZDCmd, so the default values
    # are handled properly for Zope.
    options = ZopeCtlOptions()
    options.realize(args)
    c = ZopeCmd(options)
    if options.args:
        c.onecmd(" ".join(options.args))
    if options.interactive:
        try:
            import readline
        except ImportError:
            pass
        print "program:", " ".join(options.program)
        c.do_status()
        c.cmdloop()


if __name__ == "__main__":
    main()
