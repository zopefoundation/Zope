#! /usr/bin/env python1.5
##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""
Driver program to run METAL and TAL regression tests.
"""

import sys
import os
import string
from cStringIO import StringIO
import glob
import traceback

if __name__ == "__main__":
    import setpath                      # Local hack to tweak sys.path etc.

import driver

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
    while args and args[0][:1] == '-':
        opts.append(args[0])
        del args[0]
    if not args:
        prefix = os.path.join("tests", "input", "test*.")
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
        if string.find(arg, "metal") >= 0 and "-m" not in opts:
            locopts.append("-m")
        if not unittesting:
            print arg,
            sys.stdout.flush()
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
            string.replace(head, "input", "output"),
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
