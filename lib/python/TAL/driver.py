#! /usr/bin/env python1.5
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
Driver program to test METAL and TAL implementation.
"""

import os
import sys
import string

import getopt

if __name__ == "__main__":
    import setpath                      # Local hack to tweak sys.path etc.

# Import local classes
import TALDefs
import DummyEngine

FILE = "tests/input/test01.xml"

def main():
    versionTest = 1
    macros = 0
    mode = None
    showcode = 0
    showtal = -1
    strictinsert = 1
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hxlmnst")
    except getopt.error, msg:
        sys.stderr.write("\n%s\n" % str(msg))
        sys.stderr.write(
            "usage: driver.py [-h|-x] [-l] [-m] [-n] [-s] [-t] [file]\n")
        sys.stderr.write("-h/-x -- HTML/XML input (default auto)\n")
        sys.stderr.write("-l -- lenient structure insertion\n")
        sys.stderr.write("-m -- macro expansion only\n")
        sys.stderr.write("-n -- turn off the Python 1.5.2 test\n")
        sys.stderr.write("-s -- print intermediate code\n")
        sys.stderr.write("-t -- leave tal/metal attributes in output\n")
        sys.exit(2)
    for o, a in opts:
        if o == '-h':
            mode = "html"
        if o == '-l':
            strictinsert = 0
        if o == '-m':
            macros = 1
        if o == '-n':
            versionTest = 0
        if o == '-x':
            mode = "xml"
        if o == '-s':
            showcode = 1
        if o == '-t':
            showtal = 1
    if not versionTest:
        if sys.version[:5] != "1.5.2":
            sys.stderr.write(
                "Use Python 1.5.2 only; use -n to disable this test\n")
            sys.exit(2)
    if args:
        file = args[0]
    else:
        file = FILE
    it = compilefile(file, mode)
    if showcode: showit(it)
    else: interpretit(it, tal=(not macros), showtal=showtal,
                      strictinsert=strictinsert)

def interpretit(it, engine=None, stream=None, tal=1, showtal=-1,
                strictinsert=1):
    from TALInterpreter import TALInterpreter
    program, macros = it
    assert TALDefs.isCurrentVersion(program)
    if engine is None:
        engine = DummyEngine.DummyEngine(macros)
    TALInterpreter(program, macros, engine, stream, wrap=0,
                   tal=tal, showtal=showtal, strictinsert=strictinsert)()

def compilefile(file, mode=None):
    assert mode in ("html", "xml", None)
    if mode is None:
        ext = os.path.splitext(file)[1]
        if string.lower(ext) in (".html", ".htm"):
            mode = "html"
        else:
            mode = "xml"
    if mode == "html":
        from HTMLTALParser import HTMLTALParser
        p = HTMLTALParser()
    else:
        from TALParser import TALParser
        p = TALParser()
    p.parseFile(file)
    return p.getCode()

def showit(it):
    from pprint import pprint
    pprint(it)

if __name__ == "__main__":
    main()
