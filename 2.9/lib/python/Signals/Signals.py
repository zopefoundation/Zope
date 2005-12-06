##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
Zope signal handlers for clean shutdown, restart and log rotation.

$Id$
"""
__version__='$Revision: 1.3 $'[11:-2]

import logging
import sys, os

import Lifetime

logger = logging.getLogger("Z2")

if os.name == 'nt':
    try:
        from WinSignalHandler import SignalHandler
    except ImportError:
        msg = ('Can not install signal handlers.  Please install '
               '(or upgrade) your pywin32 installation '
               '(https://sf.net/projects/pywin32)')
        logger.warning(msg)
        SignalHandler = None
else:
    from SignalHandler import SignalHandler

def shutdownFastHandler():
    """Shutdown cleanly on SIGTERM. This is registered first,
       so it should be called after all other handlers."""
    logger.info("Shutting down fast")
    Lifetime.shutdown(0,fast=1)


def shutdownHandler():
    """Shutdown cleanly on SIGINT. This is registered first,
       so it should be called after all other handlers."""
    logger.info("Shutting down")
    sys.exit(0)

def restartHandler():
    """Restart cleanly on SIGHUP. This is registered first, so it
       should be called after all other SIGHUP handlers."""
    logger.info("Restarting")
    Lifetime.shutdown(1)

class LogfileReopenHandler:
    """Reopen log files on SIGUSR2.

    This is registered first, so it should be called after all other
    SIGUSR2 handlers.
    """
    def __init__(self, loggers):
        self.loggers = [log for log in loggers if log is not None]

    def __call__(self):
        for log in self.loggers:
            log.reopen()
        logger.info("Log files reopened successfully")

# On Windows, a 'reopen' is useless - the file can not be renamed
# while open, so we perform a trivial 'rotate'.
class LogfileRotateHandler:
    """Rotate log files on SIGUSR2. Only called on Windows. This is 
       registered first, so it should be called after all other SIGUSR2 
       handlers."""
    def __init__(self, loggers):
        self.loggers = [log for log in loggers if log is not None]

    def __call__(self):
        logger.debug("Log files rotation starting...")
        for log in self.loggers:
            for f in log.handler_factories:
                handler = f()
                if hasattr(handler, 'rotate') and callable(handler.rotate):
                    handler.rotate()
        logger.info("Log files rotation complete")

def packHandler():
    """ Packs the main database.  Not safe to call under a signal
    handler, because it blocks the main thread """
    logger.info('Packing main ZODB database')
    import Globals
    try:
        db = Globals.opened[0]
        db.pack()
        logger.info('Database packing launched or completed successfully')
    except:
        logger.exception('Call to pack failed!')
        

def registerZopeSignals(loggers):
    from signal import SIGTERM, SIGINT
    try:
        from signal import SIGHUP, SIGUSR1, SIGUSR2
    except ImportError:
        # Windows doesn't have these (but also doesn't care what the exact
        # numbers are)
        SIGHUP = 1
        SIGUSR1 = 10
        SIGUSR2 = 12

    if not SignalHandler:
        return
    SignalHandler.registerHandler(SIGTERM, shutdownFastHandler)
    SignalHandler.registerHandler(SIGINT, shutdownHandler)
    if os.name != 'nt':
        SignalHandler.registerHandler(SIGHUP, restartHandler)
        SignalHandler.registerHandler(SIGUSR2, LogfileReopenHandler(loggers))
    else:
        # no restart handler on windows.
        # Log files get 'rotated', not 'reopened'
        SignalHandler.registerHandler(SIGUSR2, LogfileRotateHandler(loggers))
    # SIGUSR1 is nominally reserved for pack, but we dont have an
    # implementation that is stable yet because if the signal handler
    # fires it will be caught in the main thread and all network operations
    # will cease until it's finished.
    # (The above is *not* True for Windows - a different thread is used to
    # catch the signals.  This probably could be switched on for Windows
    # if anyone cares)
    #SignalHandler.registerHandler(SIGUSR1, packHandler)
