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
"""
Zope signal handlers for clean shutdown, restart and log rotation.

$Id: Signals.py,v 1.3 2004/04/13 19:02:25 fdrake Exp $
"""
__version__='$Revision: 1.3 $'[11:-2]

import logging
import sys

import Lifetime

from SignalHandler import SignalHandler

logger = logging.getLogger("Z2")


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
    import signal
    SignalHandler.registerHandler(signal.SIGTERM, shutdownFastHandler)
    SignalHandler.registerHandler(signal.SIGINT, shutdownHandler)
    SignalHandler.registerHandler(signal.SIGHUP, restartHandler)
    SignalHandler.registerHandler(signal.SIGUSR2,
                                  LogfileReopenHandler(loggers))
    # SIGUSR1 is nominally reserved for pack, but we dont have an
    # implementation that is stable yet because if the signal handler
    # fires it will be caught in the main thread and all network operations
    # will cease until it's finished.
    #SignalHandler.registerHandler(signal.SIGUSR1, packHandler)
