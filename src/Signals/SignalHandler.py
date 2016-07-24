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
"""Signal handling dispatcher."""

import os
import sys
import signal
from logging import getLogger

LOG = getLogger('SignalHandler')


class SignalHandler(object):

    def __init__(self):
        self.registry = {}

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
            signame = get_signal_name(signum)
            LOG.debug("Installed sighandler for %s" % signame)
        items.insert(0, handler)

    def getRegisteredSignals(self):
        """Return a list of the signals that have handlers registered. This
           is used to pass the signals through to the ZDaemon code."""
        return self.registry.keys()

    def signalHandler(self, signum, frame):
        """Meta signal handler that dispatches to registered handlers."""
        signame = get_signal_name(signum)
        LOG.info("Caught signal %s" % signame)

        for handler in self.registry.get(signum, []):
            # Never let a bad handler prevent the standard signal
            # handlers from running.
            try:
                handler()
            except SystemExit:
                # if we trap SystemExit, we can't restart
                raise
            except:
                LOG.warn('A handler for %s failed!' % signame,
                         exc_info=sys.exc_info())

_signals = None


def get_signal_name(n):
    """Return the symbolic name for signal n.

    Returns 'unknown' if there is no SIG name bound to n in the signal
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
    return _signals.get(n, 'signal %d' % n)

# The SignalHandler is actually a singleton.
SignalHandler = SignalHandler()
