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
$Id: ZCatalog.py 25050 2004-05-27 15:06:40Z chrisw $
"""

import time, sys
from zLOG import LOG, INFO

class StdoutHandler:
    """ A simple progress handler """

    def __init__(self, steps=100):
        self._steps = steps

    def init(self, ident, max):
        self._ident = ident
        self._max = max
        self._start = time.time()
        self.fp = sys.stdout
        self.output('started')

    def finish(self):
        self.output('terminated. Duration: %0.2f seconds' % \
                    (time.time() -self._start))

    def report(self, current, *args, **kw):
        if current % self._steps == 0: 
            self.output('%d/%d (%.2f%%)' % (current, self._max, (100.0 * current / self._max)))

    def output(self, text):
        print >>self.fp, '%s: %s' % (self._ident, text)


class ZLogHandler(StdoutHandler):
    """ Use zLOG """

    def output(self, text):
        LOG(self._ident, INFO, text)

