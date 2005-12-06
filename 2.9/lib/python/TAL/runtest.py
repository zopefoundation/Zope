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
Driver program to run METAL and TAL regression tests.
"""

import sys
import os
from cStringIO import StringIO
import glob
import traceback

if __name__ == "__main__":
    import setpath                      # Local hack to tweak sys.path etc.

import driver
import tests.utils

def showdiff(a, b):
    import ndiff
    cruncher = ndiff.SequenceMatcher(ndiff.IS_LINE_JUNK, a, b)
    for tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
        if tag == "equal":
            continue
        print nicerange(alo, ahi) + tag[0] + nicerange(blo, bhi)
        ndiff.dump('<', a, alo, ahi)
        if a and b:
            print '---'
        ndiff.dump('>', b, blo, bhi)

def nicerange(lo, hi):
    if hi <= lo+1:
        return str(lo+1)
    else:
        return "%d,%d" % (lo+1, hi)

def main():
    opts = []
    args = sys.argv[1:]
    quiet = 0
    unittesting = 0
    if args and args[0] == "-q":
        quiet = 1
        del args[0]
    if args and args[0] == "-Q":
        unittesting = 1
        del args[0]
    while args and args[0].startswith('-'):
        opts.append(args[0])
        del args[0]
    if not args:
        prefix = os.path.join("tests", "input", "test*.")
        if tests.utils.skipxml:
            xmlargs = []
        else:
            xmlargs = glob.glob(prefix + "xml")
            xmlargs.sort()
        htmlargs = glob.glob(prefix + "html")
        htmlargs.sort()
        args = xmlargs + htmlargs
        if not args:
             sys.stderr.write("No tests found -- please supply filenames\n")
             sys.exit(1)
    errors = 0
    for arg in args:
        locopts = []
        if arg.find("metal") >= 0 and "-m" not in opts:
            locopts.append("-m")
        if not unittesting:
            print arg,
            sys.stdout.flush()
        if tests.utils.skipxml and arg.endswith(".xml"):
            print "SKIPPED (XML parser not available)"
            continue
        save = sys.stdout, sys.argv
        try:
            try:
                sys.stdout = stdout = StringIO()
                sys.argv = [""] + opts + locopts + [arg]
                driver.main()
            finally:
                sys.stdout, sys.argv = save
        except SystemExit:
            raise
        except:
            errors = 1
            if quiet:
                print sys.exc_type
                sys.stdout.flush()
            else:
                if unittesting:
                    print
                else:
                    print "Failed:"
                    sys.stdout.flush()
                traceback.print_exc()
            continue
        head, tail = os.path.split(arg)
        outfile = os.path.join(
            head.replace("input", "output"),
            tail)
        try:
            f = open(outfile)
        except IOError:
            expected = None
            print "(missing file %s)" % outfile,
        else:
            expected = f.readlines()
            f.close()
        stdout.seek(0)
        if hasattr(stdout, "readlines"):
            actual = stdout.readlines()
        else:
            actual = readlines(stdout)
        if actual == expected:
            if not unittesting:
                print "OK"
        else:
            if unittesting:
                print
            else:
                print "not OK"
            errors = 1
            if not quiet and expected is not None:
                showdiff(expected, actual)
    if errors:
        sys.exit(1)

def readlines(f):
    L = []
    while 1:
        line = f.readline()
        if not line:
            break
        L.append(line)
    return L

if __name__ == "__main__":
    main()
