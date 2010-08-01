##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import sys
import time
from logging import getLogger

from DateTime.DateTime import DateTime
from zope.interface import implements

from .interfaces import IProgressHandler

LOG = getLogger('ProgressHandler')


class StdoutHandler(object):
    """ A simple progress handler """

    implements(IProgressHandler)

    def __init__(self, steps=100):
        self._steps = steps

    def init(self, ident, max):
        self._ident = ident
        self._max = max
        self._start = time.time()
        self.fp = sys.stdout
        self.output('Process started (%d objects to go)' % self._max)

    def info(self, text):
        self.output(text)

    def finish(self):
        self.output('Process terminated. Duration: %0.2f seconds' % \
                    (time.time() -self._start))

    def report(self, current, *args, **kw):
        if current > 0:
            if current % self._steps == 0:
                seconds_so_far = time.time() - self._start
                seconds_to_go = (seconds_so_far / current *
                                 (self._max - current))
                end = DateTime(time.time() + seconds_to_go)
                self.output('%d/%d (%.2f%%) Estimated termination: %s' % \
                            (current, self._max, (100.0 * current / self._max),
                            end.strftime('%Y/%m/%d %H:%M:%Sh')))

    def output(self, text):
        print >>self.fp, '%s: %s' % (self._ident, text)


class ZLogHandler(StdoutHandler):
    """ Use Zope logger"""

    def output(self, text):
        LOG.info(text)


class FilelogHandler(StdoutHandler):
    """ Use a custom file for logging """

    def __init__(self, filename, steps=100):
        StdoutHandler.__init__(self, steps)
        self.filename = filename

    def output(self, text):
        open(self.filename, 'a').write(text + '\n')
