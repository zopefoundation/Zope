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
Parse XML and compile to TALInterpreter intermediate code.
"""

import string
from XMLParser import XMLParser
from TALDefs import *
from TALGenerator import TALGenerator

class TALParser(XMLParser):

    ordered_attributes = 1

    def __init__(self, gen=None): # Override
        XMLParser.__init__(self)
        if gen is None:
            gen = TALGenerator()
        self.gen = gen
        self.nsStack = []
        self.nsDict = {XML_NS: 'xml'}
        self.nsNew = []

    def getCode(self):
        return self.gen.getCode()

    def getWarnings(self):
        return ()

    def StartNamespaceDeclHandler(self, prefix, uri):
        self.nsStack.append(self.nsDict.copy())
        self.nsDict[uri] = prefix
        self.nsNew.append((prefix, uri))

    def EndNamespaceDeclHandler(self, prefix):
        self.nsDict = self.nsStack.pop()

    def StartElementHandler(self, name, attrs):
        if self.ordered_attributes:
            # attrs is a list of alternating names and values
            attrlist = []
            for i in range(0, len(attrs), 2):
                key = attrs[i]
                value = attrs[i+1]
                attrlist.append((key, value))
        else:
            # attrs is a dict of {name: value}
            attrlist = attrs.items()
            attrlist.sort() # For definiteness
        name, attrlist, taldict, metaldict = self.process_ns(name, attrlist)
        attrlist = self.xmlnsattrs() + attrlist
        self.gen.emitStartElement(name, attrlist, taldict, metaldict)

    def process_ns(self, name, attrlist):
        taldict = {}
        metaldict = {}
        fixedattrlist = []
        name, namebase, namens = self.fixname(name)
        for key, value in attrlist:
            key, keybase, keyns = self.fixname(key)
            ns = keyns or namens # default to tag namespace
            item = key, value
            if ns == 'metal':
                metaldict[keybase] = value
                item = item + ("metal",)
            elif ns == 'tal':
                taldict[keybase] = value
                item = item + ("tal",)
            fixedattrlist.append(item)
        if namens in ('metal', 'tal'):
            taldict['tal tag'] = namens
        return name, fixedattrlist, taldict, metaldict

    def xmlnsattrs(self):
        newlist = []
        for prefix, uri in self.nsNew:
            if prefix:
                key = "xmlns:" + prefix
            else:
                key = "xmlns"
            if uri in (ZOPE_METAL_NS, ZOPE_TAL_NS):
                item = (key, uri, "xmlns")
            else:
                item = (key, uri)
            newlist.append(item)
        self.nsNew = []
        return newlist

    def fixname(self, name):
        if ' ' in name:
            uri, name = string.split(name, ' ')
            prefix = self.nsDict[uri]
            prefixed = name
            if prefix:
                prefixed = "%s:%s" % (prefix, name)
            ns = 'x'
            if uri == ZOPE_TAL_NS:
                ns = 'tal'
            elif uri == ZOPE_METAL_NS:
                ns = 'metal'
            return (prefixed, name, ns)
        return (name, name, None)

    def EndElementHandler(self, name):
        name = self.fixname(name)[0]
        self.gen.emitEndElement(name)

    def DefaultHandler(self, text):
        self.gen.emitRawText(text)

def test():
    import sys
    p = TALParser()
    file = "tests/input/test01.xml"
    if sys.argv[1:]:
        file = sys.argv[1]
    p.parseFile(file)
    program, macros = p.getCode()
    from TALInterpreter import TALInterpreter
    from DummyEngine import DummyEngine
    engine = DummyEngine(macros)
    TALInterpreter(program, macros, engine, sys.stdout, wrap=0)()

if __name__ == "__main__":
    test()
