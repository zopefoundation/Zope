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

$Id: Signals.py,v 1.2 2003/11/12 20:42:22 chrism Exp $
"""
__version__='$Revision: 1.2 $'[11:-2]

from SignalHandler import SignalHandler
import zLOG
import sys
import Lifetime

def shutdownFastHandler():
    """Shutdown cleanly on SIGTERM. This is registered first,
       so it should be called after all other handlers."""
    zLOG.LOG('Z2', zLOG.INFO , "Shutting down fast")
    Lifetime.shutdown(0,fast=1)


def shutdownHandler():
    """Shutdown cleanly on SIGINT. This is registered first,
       so it should be called after all other handlers."""
    zLOG.LOG('Z2', zLOG.INFO , "Shutting down")
    sys.exit(0)

def restartHandler():
    """Restart cleanly on SIGHUP. This is registered first, so it
       should be called after all other SIGHUP handlers."""
    zLOG.LOG('Z2', zLOG.INFO , "Restarting")
    Lifetime.shutdown(1)

def logfileReopenHandler():
    """Reopen log files on SIGUSR2. This is registered first, so it
       should be called after all other SIGUSR2 handlers."""
    from zLOG.EventLogger import event_logger
    from ZServer.AccessLogger import access_logger
    from ZServer.DebugLogger import debug_logger
    for logger in (event_logger, access_logger, debug_logger):
        logger.reopen()
    zLOG.LOG('Z2', zLOG.INFO, "Log files reopened successfully")

def packHandler():
    """ Packs the main database.  Not safe to call under a signal
    handler, because it blocks the main thread """
    zLOG.LOG('Z2', zLOG.INFO, 'Packing main ZODB database')
    import Globals
    try:
        db = Globals.opened[0]
        db.pack()
        zLOG.LOG('Z2', zLOG.INFO,
                'Database packing launched or completed successfully')
    except:
        zLOG.LOG('Z2', zLOG.INFO,
                 'Call to pack failed!', error=sys.exc_info())
        

def registerZopeSignals():
    import signal
    SignalHandler.registerHandler(signal.SIGTERM, shutdownFastHandler)
    SignalHandler.registerHandler(signal.SIGINT, shutdownHandler)
    SignalHandler.registerHandler(signal.SIGHUP, restartHandler)
    SignalHandler.registerHandler(signal.SIGUSR2, logfileReopenHandler)
    # SIGUSR1 is nominally reserved for pack, but we dont have an
    # implementation that is stable yet because if the signal handler
    # fires it will be caught in the main thread and all network operations
    # will cease until it's finished.
    #SignalHandler.registerHandler(signal.SIGUSR1, packHandler)
