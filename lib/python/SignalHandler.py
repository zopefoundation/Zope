##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

"""Signal handling dispatcher."""

__version__='$Revision: 1.3 $'[11:-2]

from ZServer import asyncore
import sys, os, zdaemon, ZLogger
import signal, zLOG


class SignalHandler:

    def __init__(self):
        self.registry = {}
        self.registerHandler(signal.SIGTERM, self.shutdownHandler)
        self.registerHandler(signal.SIGINT, self.shutdownHandler)
        self.registerHandler(signal.SIGHUP, self.restartHandler)
        self.registerHandler(signal.SIGUSR2, self.sigusr2Handler)

    def registerHandler(self, signum, handler):
        """Register a handler function that will be called when the process
           recieves the signal signum. The signum argument must be a signal
           constant such as SIGTERM. The handler argument must be a function
           or method that takes no arguments. Note that handlers will not
           be called on non-posix platforms."""
        if os.name != 'posix':
            return
        items = self.registry.get(signum)
        if items is None:
            items = self.registry[signum] = []
            signal.signal(signum, self.signalHandler)
            signame = zdaemon.Daemon.get_signal_name(signum)
            zLOG.LOG('Z2', zLOG.BLATHER, "Installed sighandler for %s" % (
                      signame
                      ))
        items.insert(0, handler)

    def getRegisteredSignals(self):
        """Return a list of the signals that have handlers registered. This
           is used to pass the signals through to the ZDaemon code."""
        return self.registry.keys()

    def signalHandler(self, signum, frame):
        """Meta signal handler that dispatches to registered handlers."""
        signame = zdaemon.Daemon.get_signal_name(signum)
        zLOG.LOG('Z2', zLOG.INFO , "Caught signal %s" % signame)

        for handler in self.registry.get(signum, []):
            # Never let a bad handler prevent the standard signal
            # handlers from running.
            try: handler()
            except SystemExit:
                # if we trap SystemExit, we can't restart
                raise
            except:
                zLOG.LOG('Z2', zLOG.WARNING,
                         'A handler for %s failed!' % signame,
                         error=sys.exc_info())

    # Builtin signal handlers for clean shutdown, restart and log rotation.

    def shutdownHandler(self):
        """Shutdown cleanly on SIGTERM, SIGINT. This is registered first,
           so it should be called after all other handlers."""
        self.closeall()
        zLOG.LOG('Z2', zLOG.INFO , "Shutting down")
        sys.exit(0)

    def restartHandler(self):
        """Restart cleanly on SIGHUP. This is registered first, so it
           should be called after all other SIGHUP handlers."""
        self.closeall()
        zLOG.LOG('Z2', zLOG.INFO , "Restarting")
        sys.exit(1)

    def sigusr2Handler(self):
        """Reopen log files on SIGUSR2. This is registered first, so it
           should be called after all other SIGUSR2 handlers."""
        zLOG.LOG('Z2', zLOG.INFO , "Reopening log files")
        reopen = getattr(getattr(sys, '__lg', None), 'reopen', None)
        if reopen is not None:
            reopen()
            zLOG.LOG('Z2', zLOG.BLATHER, "Reopened access log")
        reopen = getattr(getattr(sys, '__detailedlog', None), 'reopen', None)
        if reopen is not None:
            reopen()
            zLOG.LOG('Z2', zLOG.BLATHER,"Reopened detailed request log")
        if hasattr(zLOG, '_set_stupid_dest'):
            zLOG._set_stupid_dest(None)
        else:
            zLOG._stupid_dest = None
        ZLogger.stupidFileLogger._stupid_dest = None
        zLOG.LOG('Z2', zLOG.BLATHER, "Reopened event log")
        zLOG.LOG('Z2', zLOG.INFO, "Log files reopened successfully")
    
    def closeall(self):
        """Helper method to close network and database connections."""
        import Globals
        zLOG.LOG('Z2', zLOG.INFO, "Closing all open network connections")
        for socket in asyncore.socket_map.values():
            try: socket.close()
            except: pass

        zLOG.LOG('Z2', zLOG.INFO, "Closing all open ZODB databases")
        for db in Globals.opened:
            try: db.close()
            finally: pass



# The SignalHandler is actually a singleton.
SignalHandler = SignalHandler()


