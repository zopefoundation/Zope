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
Driver program to test TALVisitor and its base class CopyingDOMVisitor.
"""

import sys

import getopt

import setpath                          # Local hack to tweak sys.path etc.

# Use the ParsedXML product and its DOM implementation
from Products.ParsedXML import Printer
from Products.ParsedXML.DOM import Core, ExpatBuilder

# Import local classes
from CopyingDOMVisitor import CopyingDOMVisitor
from DummyEngine import DummyEngine

FILE = "test/test1.xml"

def main():
    noVersionTest = 0
    macros = 0
    compile = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:], "cmn")
    except getopt.error, msg:
        sys.stderr.write("%s\n" % str(msg))
        sys.stderr.write("usage: driver.py [-c] [-m] [-n] [file]\n")
        sys.stderr.write("-c -- compiled mode (faster)\n")
        sys.stderr.write("-m -- macro expansion only\n")
        sys.stderr.write("-n -- turn of the Python 1.5.2 test\n")
        sys.exit(2)
    for o, a in opts:
        if o == '-c':
            compile = 1
        if o == '-m':
            macros = 1
        if o == '-n':
            noVersionTest = 1
    if not noVersionTest:
        if sys.version[:5] != "1.5.2":
            sys.stderr.write(
                "Use Python 1.5.2 only; use -n to disable this test\n")
            sys.exit(2)
    if args:
        file = args[0]
    else:
        file = FILE
    doc = parsefile(file)
    if macros or compile:
        if macros:
            it = precompiletree(doc)
        else:
            it = compiletree(doc)
        interpretit(it)
    else:
        doc = talizetree(doc)
        printtree(doc)

def parsefile(file):
    return ExpatBuilder.parse(file, 1)

def printtree(node, stream=None, encoding=None):
    if stream is None:
        stream = sys.stdout
    Printer.PrintVisitor(node, stream, encoding)()

def copytree(root, dom=None):
    if dom is None:
        dom = Core.theDOMImplementation
    return CopyingDOMVisitor(root, dom)()

def talizetree(root, dom=None, engine=None):
    from TALVisitor import TALVisitor
    if dom is None:
        dom = Core.theDOMImplementation
    if engine is None:
        engine = DummyEngine()
    return TALVisitor(root, dom, engine)()

def precompiletree(root):
    from TALCompiler import METALCompiler
    return METALCompiler(root)()

def compiletree(root):
    from TALCompiler import TALCompiler
    return TALCompiler(root)()

def interpretit(it, engine=None, stream=None):
    from TALInterpreter import TALInterpreter
    program, macros = it
    if engine is None:
        engine = DummyEngine(macros)
    TALInterpreter(program, macros, engine, stream)()

if __name__ == "__main__":
    main()
