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

_metal = ZOPE_METAL_NS + " "
METAL_DEFINE_MACRO = _metal + "define-macro"
METAL_USE_MACRO = _metal + "use-macro"
METAL_DEFINE_SLOT = _metal + "define-slot"
METAL_FILL_SLOT = _metal + "fill-slot"

_tal = ZOPE_TAL_NS + " "
TAL_DEFINE = _tal + "define"
TAL_CONDITION = _tal + "condition"
TAL_INSERT = _tal + "insert"
TAL_REPLACE = _tal + "replace"
TAL_REPEAT = _tal + "repeat"
TAL_ATTRIBUTES = _tal + "attributes"

from TALGenerator import TALGenerator

class TALParser(XMLParser):

    ordered_attributes = 1

    def __init__(self, gen=None): # Override
        XMLParser.__init__(self)
        if gen is None:
            gen = TALGenerator()
        self.gen = gen
        self.todoStack = []
        self.nsStack = []
        self.nsDict = {}
        self.nsNew = []

    def getCode(self):
        return self.gen.program, self.gen.macros

    def todoPush(self, todo):
        self.todoStack.append(todo)

    def todoPop(self):
        return self.todoStack.pop()

    def StartNamespaceDeclHandler(self, prefix, uri):
        self.nsStack.append(self.nsDict.copy())
        self.nsDict[uri] = prefix
        self.nsNew.append((prefix, uri))

    def EndNamespaceDeclHandler(self, prefix):
        self.nsDict = self.nsStack.pop()

    def StartElementHandler(self, name, attrs):
        if self.ordered_attributes:
            # attrs is a list of alternating names and values
            attrdict = {}
            attrlist = []
            for i in range(0, len(attrs), 2):
                key = attrs[i]
                value = attrs[i+1]
                attrdict[key] = value
                attrlist.append((key, value))
        else:
            # attrs is a dict of {name: value}
            attrdict = attrs
            attrlist = attrs.items()
            attrlist.sort() # For definiteness
        self.checkattrs(attrlist)
        todo = {}
        defineMacro = attrdict.get(METAL_DEFINE_MACRO)
        useMacro = attrdict.get(METAL_USE_MACRO)
        defineSlot = attrdict.get(METAL_DEFINE_SLOT)
        fillSlot = attrdict.get(METAL_FILL_SLOT)
        defines = attrdict.get(TAL_DEFINE)
        condition = attrdict.get(TAL_CONDITION)
        insert = attrdict.get(TAL_INSERT)
        replace = attrdict.get(TAL_REPLACE)
        repeat = attrdict.get(TAL_REPEAT)
        attrsubst = attrdict.get(TAL_ATTRIBUTES)
        n = 0
        if defineMacro: n = n+1
        if useMacro: n = n+1
        if fillSlot: n = n+1
        if defineSlot: n = n+1
        if n > 1:
            raise METALError("only one METAL attribute per element")
        n = 0
        if insert: n = n+1
        if replace: n + n+1
        if repeat: n = n+1
        if n > 1:
            raise TALError("can't use insert, replace, repeat together")
        if defineMacro:
            self.gen.pushProgram()
            todo["defineMacro"] = defineMacro
        if useMacro:
            self.gen.pushSlots()
            self.gen.pushProgram()
            todo["useMacro"] = useMacro
        if defineSlot:
            self.gen.pushProgram()
            todo["defineSlot"] = defineSlot
        if fillSlot:
            self.gen.pushProgram()
            todo["fillSlot"] = fillSlot
        if defines:
            self.gen.emit("beginScope")
            self.gen.emitDefines(defines)
            todo["define"] = defines
        if condition:
            self.gen.pushProgram()
            todo["condition"] = condition
        if insert:
            todo["insert"] = insert
        elif replace:
            todo["replace"] = replace
            self.gen.pushProgram()
        elif repeat:
            todo["repeat"] = repeat
            self.gen.emit("beginScope")
            self.gen.pushProgram()
        if attrsubst:
            repldict = parseAttributeReplacements(attrsubst)
        else:
            repldict = {}
        self.gen.emitStartTag(self.fixname(name),
                                  self.fixattrs(attrlist, repldict))
        if insert:
            self.gen.pushProgram()
        self.todoPush(todo)

    def checkattrs(self, attrlist):
        talprefix = _tal
        ntal = len(talprefix)
        metalprefix = _metal
        nmetal = len(metalprefix)
        for key, value in attrlist:
            if key[:nmetal] == metalprefix:
                if key[nmetal:] not in KNOWN_METAL_ATTRIBUTES:
                    raise METALError(
                        "bad METAL attribute: %s;\nallowed are: %s" %
                        (repr(key[nmetal:]),
                         string.join(KNOWN_METAL_ATTRIBUTES)))
            elif key[:ntal] == talprefix:
                if key[ntal:] not in KNOWN_TAL_ATTRIBUTES:
                    raise TALError(
                        "bad TAL attribute: %s;\nallowed are: %s" %
                        (repr(key[ntal:]),
                         string.join(KNOWN_TAL_ATTRIBUTES)))

    def fixattrs(self, attrlist, repldict):
        newlist = []
        for prefix, uri in self.nsNew:
            if prefix:
                newlist.append(("xmlns:" + prefix, uri))
            else:
                newlist.append(("xmlns", uri))
        self.nsNew = []
        for fullkey, value in attrlist:
            key = self.fixname(fullkey)
            if repldict.has_key(key):
                item = (key, value, "replace", repldict[key])
            elif fullkey == METAL_DEFINE_MACRO:
                item = (key, value, "macroHack")
            else:
                item = (key, value)
            newlist.append(item)
        return newlist

    def fixname(self, name):
        if ' ' in name:
            uri, name = string.split(name, ' ')
            prefix = self.nsDict[uri]
            if prefix:
                name = "%s:%s" % (prefix, name)
        return name

    def EndElementHandler(self, name):
        name = self.fixname(name)
        todo = self.todoPop()
        if not todo:
            # Shortcut
            self.gen.emitEndTag(name)
            return
        insert = todo.get("insert")
        if insert:
            self.gen.emitSubstitution(insert)
        self.gen.emitEndTag(name)
        repeat = todo.get("repeat")
        if repeat:
            self.gen.emitRepeat(repeat)
            self.gen.emit("endScope")
        replace = todo.get("replace")
        if replace:
            self.gen.emitSubstitution(replace)
        condition = todo.get("condition")
        if condition:
            self.gen.emitCondition(condition)
        if todo.get("define"):
            self.gen.emit("endScope")
        defineMacro = todo.get("defineMacro")
        useMacro = todo.get("useMacro")
        defineSlot = todo.get("defineSlot")
        fillSlot = todo.get("fillSlot")
        if defineMacro:
            self.gen.emitDefineMacro(defineMacro)
        if useMacro:
            self.gen.emitUseMacro(useMacro)
        if defineSlot:
            self.gen.emitDefineSlot(defineSlot)
        if fillSlot:
            self.gen.emitFillSlot(fillSlot)

    def CommentHandler(self, text):
        self.gen.emit("comment", text)

    def CharacterDataHandler(self, text):
        self.gen.emitText(text)

def test():
    import sys
    p = TALParser()
    file = "test/test1.xml"
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
