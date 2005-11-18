#! /usr/bin/env python
##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
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
Helper program to time compilation and interpretation
"""

import sys
import time
import getopt
from cPickle import dumps, loads
from cStringIO import StringIO

from driver import FILE, compilefile, interpretit

def main():
    count = 10
    try:
        opts, args = getopt.getopt(sys.argv[1:], "n:")
    except getopt.error, msg:
        print msg
        sys.exit(2)
    for o, a in opts:
        if o == "-n":
            count = int(a)
    if not args:
        args = [FILE]
    for file in args:
        print file
        dummyfile = StringIO()
        it = timefunc(count, compilefile, file)
        timefunc(count, interpretit, it, None, dummyfile)

def timefunc(count, func, *args):
    sys.stderr.write("%-14s: " % func.__name__)
    sys.stderr.flush()
    t0 = time.clock()
    for i in range(count):
        result = func(*args)
    t1 = time.clock()
    sys.stderr.write("%6.3f secs for %d calls, i.e. %4.0f msecs per call\n"
                     % ((t1-t0), count, 1000*(t1-t0)/count))
    return result

if __name__ == "__main__":
    main()
