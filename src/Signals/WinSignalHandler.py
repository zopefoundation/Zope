##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""Signal handling dispatcher for Windows."""

# This code "simulates" Unix signals via Windows events.  When a signal is
# registered, we simply create a global named event for that signal.  The
# signal can be set by any user with the correct permission opening and
# setting the event.
#
# One event is used per signal, and the event name is based on both the
# Zope process ID and the signal number.  For example, assuming a process
# ID of 123, a SIGINT handler would create an event called "Zope-123-2"
# (as signal.SIGINT==2).  The logfile reopen handler uses an event named
# "Zope-123-12" (as the logfile handler uses SIGUSR2, which == 12)

# The following program will send such an event:
#   import sys, win32event
#   hev = win32event.OpenEvent(win32event.EVENT_MODIFY_STATE, 0, sys.argv[1])
#   win32event.SetEvent(hev)
# A good way to get the PID is to read the var/*.pid file for the app.

# This code is only the generic signal mechanism for Windows.
# The signal handlers are still external, just like for other platforms.

# NOTE: There is one huge semantic difference between these "signals"
# and signals on Unix.  On Windows, the signals are delivered asynchronously
# to a thread inside this module.  This thread calls the event handler
# directly - there is no magic to switch the call back to the main thread.
# If this is a problem (not currently, but likely later), one option may be
# to add yet another asyncore handler - the thread in this module could
# then "post" the request to the main thread via this asyncore handler.

import asyncore
import atexit
import logging
import os
import sys
import signal
import threading

# As at pywin32-204, we must ensure pywintypes is the first win32 module
# imported in our process, otherwise we can end up with 2 pywintypesxx.dll
# instances in our process resulting in:
# TypeError: The object is not a PySECURITY_ATTRIBUTES object
import pywintypes

# SetConsoleCtrlHandler not in early pywin32 versions - Signals.py will
# catch the import error.
from win32api import SetConsoleCtrlHandler
import win32con
import win32event
import ntsecuritycon

LIFETIME = True
try:
    from Lifetime import shutdown
except ImportError:
    LIFETIME = False

logger = logging.getLogger("WinSignalHandler")

# We simulate signals via win32 named events.  This is the event name
# prefix we use - the "signal number" is appended to this name.
event_name_prefix = "Zope-%d-" % os.getpid()

# For Windows 2000 and later, we prefix "Global\" to the name, so that
# it works correctly in a Terminal Services environment.
winver = sys.getwindowsversion()
# sys.getwindowsversion() -> major, minor, build, platform_id, ver_string
# for platform_id, 2==VER_PLATFORM_WIN32_NT
if winver[0] >= 5 and winver[3] == 2:
    event_name_prefix = "Global\\" + event_name_prefix


def createEventSecurityObject():
    # Create a security object giving World read/write access,
    # but only "Owner" modify access.
    sa = pywintypes.SECURITY_ATTRIBUTES()
    sidEveryone = pywintypes.SID()
    sidEveryone.Initialize(ntsecuritycon.SECURITY_WORLD_SID_AUTHORITY, 1)
    sidEveryone.SetSubAuthority(0, ntsecuritycon.SECURITY_WORLD_RID)
    sidCreator = pywintypes.SID()
    sidCreator.Initialize(ntsecuritycon.SECURITY_CREATOR_SID_AUTHORITY, 1)
    sidCreator.SetSubAuthority(0, ntsecuritycon.SECURITY_CREATOR_OWNER_RID)

    acl = pywintypes.ACL()
    acl.AddAccessAllowedAce(win32event.EVENT_MODIFY_STATE, sidEveryone)
    acl.AddAccessAllowedAce(ntsecuritycon.FILE_ALL_ACCESS, sidCreator)

    sa.SetSecurityDescriptorDacl(1, acl, 0)
    return sa


def wakeSelect():
    """Interrupt a sleeping asyncore 'select' call"""
    # What is the right thing to do here?
    # asyncore.close_all() works, but I fear that would
    # prevent the poll based graceful cleanup code from working.
    # This seems to work :)
    for fd, obj in asyncore.socket_map.items():
        if hasattr(obj, "pull_trigger"):
            obj.pull_trigger()


class SignalHandler(object):

    def __init__(self):
        self.registry = {}
        self.event_handles = {}
        self.admin_event_handle = win32event.CreateEvent(None, 0, 0, None)
        self.shutdown_requested = False
        # Register a "console control handler" for Ctrl+C/Break notification.
        SetConsoleCtrlHandler(consoleCtrlHandler)

        # Start the thread that is watching for events.
        thread = threading.Thread(target=self.signalCheckerThread)
        # If something goes terribly wrong, don't wait for this thread!
        thread.setDaemon(True)
        thread.start()
        self.signal_thread = thread

    def shutdown(self):
        # Shutdown our signal watcher thread.
        logger.debug("signal handler shutdown starting.")
        self.shutdown_requested = 1
        win32event.SetEvent(self.admin_event_handle)
        self.signal_thread.join(5)  # should never block for long!

        self.registry = None
        self.event_handles = None
        self.admin_event_handle = None
        logger.debug("signal handler shutdown complete.")

    def consoleCtrlHandler(self, ctrlType):
        """Called by Windows on a new thread whenever a console control
           event is raised."""
        logger.debug("Windows control event %d" % ctrlType)
        sig = None
        if ctrlType == win32con.CTRL_C_EVENT:
            # user pressed Ctrl+C or someone did GenerateConsoleCtrlEvent
            sig = signal.SIGINT
        elif ctrlType == win32con.CTRL_BREAK_EVENT:
            sig = signal.SIGTERM
        elif ctrlType == win32con.CTRL_CLOSE_EVENT:
            # Console is about to die.
            # CTRL_CLOSE_EVENT gives us 5 seconds before displaying
            # the "End process" dialog - so treat as 'fast'
            sig = signal.SIGTERM
        elif ctrlType in (win32con.CTRL_LOGOFF_EVENT,
                          win32con.CTRL_SHUTDOWN_EVENT):
            # MSDN says:
            # "Note that this signal is received only by services.
            # Interactive applications are terminated at logoff, so
            # they are not present when the system sends this signal."
            # We can therefore ignore it (our service framework
            # manages shutdown in this case)
            pass
        else:
            logger.info("Unexpected windows control event %d" % ctrlType)
        # Call the signal handler - we could also do it asynchronously
        # by setting the relevant event, but we need it synchronous so
        # that we don't wake the select loop until after the shutdown
        # flags have been set.
        result = 0
        if sig is not None and sig in self.registry:
            self.signalHandler(sig, None)
            result = 1  # don't call other handlers.
        return result

    def signalCheckerThread(self):
        while not self.shutdown_requested:
            handles = [self.admin_event_handle]
            signums = [None]
            for signum, handle in self.event_handles.items():
                signums.append(signum)
                handles.append(handle)
            rc = win32event.WaitForMultipleObjects(handles, False,
                                                   win32event.INFINITE)
            logger.debug("signalCheckerThread awake with %s" % rc)
            signum = signums[rc - win32event.WAIT_OBJECT_0]
            if signum is None:
                # Admin event - either shutdown, or new event object created.
                pass
            else:
                logger.debug("signalCheckerThread calling %s" % signum)
                self.signalHandler(signum, None)
                logger.debug("signalCheckerThread back")
        logger.debug("signalCheckerThread stopped")

    def registerHandler(self, signum, handler):
        """Register a handler function that will be called when the process
           recieves the signal signum. The signum argument must be a signal
           constant such as SIGTERM. The handler argument must be a function
           or method that takes no arguments."""
        items = self.registry.get(signum)
        if items is None:
            items = self.registry[signum] = []
            # Create an event for this signal.
            event_name = event_name_prefix + str(signum)
            sa = createEventSecurityObject()
            hevent = win32event.CreateEvent(sa, 0, 0, event_name)
            self.event_handles[signum] = hevent
            # Let the worker thread know there is a new handle.
            win32event.SetEvent(self.admin_event_handle)
            signame = get_signal_name(signum)
            logger.debug(
                "Installed sighandler for %s (%s)" % (signame, event_name))
        items.insert(0, handler)

    def getRegisteredSignals(self):
        """Return a list of the signals that have handlers registered. This
           is used to pass the signals through to the ZDaemon code."""
        return self.registry.keys()

    def signalHandler(self, signum, frame):
        """Meta signal handler that dispatches to registered handlers."""
        signame = get_signal_name(signum)
        logger.info("Caught signal %s" % signame)

        for handler in self.registry.get(signum, []):
            # Never let a bad handler prevent the standard signal
            # handlers from running.
            try:
                handler()
            except SystemExit as rc:
                # On Unix, signals are delivered to the main thread, so a
                # SystemExit does the right thing.  On Windows, we are on
                # our own thread, so throwing SystemExit there isn't a great
                # idea.  Just shutdown the main loop.
                if LIFETIME:
                    logger.debug("Trapped SystemExit(%s) - "
                                 "doing Lifetime shutdown" % rc)
                    shutdown(rc)
                else:
                    raise
            except:
                logger.exception("A handler for %s failed!'" % signame)
            wakeSelect()  # trigger a walk around the Lifetime loop.

_signals = None


def get_signal_name(n):
    """Return the symbolic name for signal n.

    Returns 'signal n' if there is no SIG name bound to n in the signal
    module.
    """
    global _signals
    if _signals is None:
        _signals = {}
        for k, v in signal.__dict__.items():
            startswith = getattr(k, 'startswith', None)
            if startswith is None:
                continue
            if startswith('SIG') and not startswith('SIG_'):
                _signals[v] = k
        # extra ones that aren't (weren't?) in Windows.
        for name, val in ("SIGHUP", 1), ("SIGUSR1", 10), ("SIGUSR2", 12):
            if name not in _signals:
                _signals[val] = name

    return _signals.get(n, 'signal %d' % n)


def consoleCtrlHandler(ctrlType):
    # The win32 ConsoleCtrlHandler
    return SignalHandler.consoleCtrlHandler(ctrlType)

# The SignalHandler is actually a singleton.
SignalHandler = SignalHandler()

# Need to be careful at shutdown - the 'signal watcher' thread which triggers
# the shutdown may still be running when the main thread terminates and
# Python starts cleaning up.
atexit.register(SignalHandler.shutdown)
