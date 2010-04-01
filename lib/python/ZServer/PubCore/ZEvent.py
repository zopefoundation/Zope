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

"""Simple Event Manager Based on Pipes
"""

from ZServer.medusa.thread.select_trigger import trigger
from asyncore import socket_map

class simple_trigger(trigger):
    def handle_close(self):
        pass

the_trigger=simple_trigger()

def Wakeup(thunk=None):
    global the_trigger
    try:
        the_trigger.pull_trigger(thunk)
    except OSError, why:
        # this broken pipe as a result of perhaps a signal
        # we want to handle this gracefully so we get rid of the old
        # trigger and install a new one.
        if why[0] == 32:
            del socket_map[the_trigger._fileno]
            the_trigger = simple_trigger() # adds itself back into socket_map
            the_trigger.pull_trigger(thunk)
