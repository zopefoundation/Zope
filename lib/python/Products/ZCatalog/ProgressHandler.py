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

class DefaultProgressHandler:
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


class ProgressMixin:
    """ A simple machinery to provide progres informations for long running
        ZCatalog operations like reindexing.
    """

    def pg_register(self, handler=None):
        self._v_pg_handler = handler

    def pg_init(self, ident, max):
        handler = getattr(self, '_v_pg_handler', None)
        if not handler: return
        handler.init(ident, max)

    def pg_finish(self):
        handler = getattr(self, '_v_pg_handler', None)
        if not handler: return
        handler.finish()

    def pg_report(self, current, *args, **kw):
        handler = getattr(self, '_v_pg_handler', None)
        if not handler: return
        handler.report(current, *args, **kw)
