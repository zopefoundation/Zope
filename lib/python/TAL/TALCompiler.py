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
Compile a DOM tree for efficient METAL and TAL expansion.
"""

import string
import re
from xml.dom import Node

from DOMVisitor import DOMVisitor

from TALDefs import ZOPE_TAL_NS, ZOPE_METAL_NS, NAME_RE
from TALDefs import macroIndexer, slotIndexer
from TALDefs import splitParts, parseAttributeReplacements
from TALDefs import parseSubstitution

class TALError(Exception):
    pass

class METALError(TALError):
    pass

KNOWN_METAL_ATTRIBUTES = [
    "define-macro",
    "use-macro",
    "define-slot",
    "fill-slot",
    ]

KNOWN_TAL_ATTRIBUTES = [
    "define",
    "condition",
    "insert",
    "replace",
    "repeat",
    "attributes",
    ]

class DummyCompiler:

    def compile(self, expr):
        return expr

class METALCompiler(DOMVisitor):

    def __init__(self, document, expressionCompiler=None):
        self.document = document
        DOMVisitor.__init__(self, document)
        if not expressionCompiler:
            expressionCompiler = DummyCompiler()
        self.expressionCompiler = expressionCompiler

    def __call__(self):
        self.macros = {}
        self.program = []
        self.stack = []
        self.namespaceDict = {}
        self.namespaceStack = [self.namespaceDict]
        DOMVisitor.__call__(self)
        assert not self.stack
        return self.program, self.macros

    def compileExpression(self, expr):
        return self.expressionCompiler.compile(expr)

    def pushProgram(self):
        self.stack.append(self.program)
        self.program = []

    def popProgram(self):
        program = self.program
        self.program = self.stack.pop()
        return program

    def pushNS(self):
        self.namespaceStack.append(self.namespaceDict)

    def popNS(self):
        self.namespaceDict = self.namespaceStack.pop()

    def newNS(self, prefix, namespaceURI):
        if self.namespaceDict.get(prefix) != namespaceURI:
            if self.namespaceDict is self.namespaceStack[-1]:
                self.namespaceDict = self.namespaceDict.copy()
            self.namespaceDict[prefix] = namespaceURI
            return 1
        else:
            return 0

    def getFullAttrList(self, node):
        # First, call newNS() for explicit xmlns attributes
        for attr in node.attributes.values():
            if attr.name == "xmlns":
                self.newNS(None, attr.value)
            elif attr.prefix == "xmlns":
                self.newNS(attr.localName, attr.value)
        list = []
        # Add namespace declarations for the node itself
        if node.namespaceURI:
            if self.newNS(node.prefix, node.namespaceURI):
                if node.prefix:
                    list.append(("xmlns:" + node.prefix, node.namespaceURI))
                else:
                    list.append(("xmlns", node.namespaceURI))
        # Add namespace declarations for each attribute
        for attr in node.attributes.values():
            if attr.namespaceURI:
                if not attr.prefix:
                    continue
                if self.newNS(attr.prefix, attr.namespaceURI):
                    if attr.prefix == "xmlns":
                        continue
                    if attr.prefix:
                        list.append(
                            ("xmlns:" + attr.prefix, attr.namespaceURI))
                    else:
                        list.append(("xmlns", node.namespaceURI))
        # Add the node's attributes
        list.extend(self.getAttributeList(node))
        return list

    def emit(self, *instruction):
        self.program.append(instruction)

    def emitStartTag(self, node):
        self.emit("startTag", node.nodeName, self.getFullAttrList(node))

    def emitStartEndTag(self, node):
        self.emit("startEndTag", node.nodeName, self.getFullAttrList(node))

    def emitEndTag(self, node):
        self.emit("endTag", node.nodeName)

    def visitElement(self, node):
        self.pushNS()
        if not node.hasAttributes():
            self.emitElement(node)
        else:
            self.checkSpuriousAttributes(node)
            self.expandElement(node)
        self.popNS()

    def checkSpuriousAttributes(self, node,
                                ns=ZOPE_METAL_NS,
                                known=KNOWN_METAL_ATTRIBUTES,
                                error=METALError,
                                what="METAL"):
        for attr in node.attributes.values():
            if attr.namespaceURI == ns:
                if attr.localName not in known:
                    raise error(
                        "bad %s attribute: %s;\nallowed are: %s" %
                        (what, repr(attr.name), string.join(known)))

    def expandElement(self, node):
        macroName = node.getAttributeNS(ZOPE_METAL_NS, "use-macro")
        if macroName:
            slotDict = slotIndexer(node)
            compiledSlots = {}
            if slotDict:
                # Compile the slots
                for slotName, slotNode in slotDict.items():
                    self.pushProgram()
                    self.visitElement(slotNode)
                    compiledSlots[slotName] = self.popProgram()
            cexpr = self.compileExpression(macroName)
            self.emit("useMacro", cexpr, compiledSlots)
            return
        macroName = node.getAttributeNS(ZOPE_METAL_NS, "define-macro")
        if macroName:
            # Save macro definitions
            if self.macros.has_key(macroName):
                raise METALError("duplicate macro definition: %s" % macroName)
            self.pushProgram()
            self.compileElement(node)
            macro = self.popProgram()
            self.macros[macroName] = macro
            self.emit("defineMacro", macroName, macro)
            return
        slotName = node.getAttributeNS(ZOPE_METAL_NS, "define-slot")
        if slotName:
            self.pushProgram()
            self.compileElement(node)
            block = self.popProgram()
            self.emit("defineSlot", slotName, block)
            return
        slotName = node.getAttributeNS(ZOPE_METAL_NS, "fill-slot")
        if slotName:
            self.pushProgram()
            self.compileElement(node)
            block = self.popProgram()
            self.emit("fillSlot", slotName, block)
            return
        self.compileElement(node)

    def compileElement(self, node):
        self.emitElement(node)

    def emitElement(self, node):
            if not node.hasChildNodes():
                self.emitStartEndTag(node)
            else:
                self.emitStartTag(node)
                self.visitAllChildren(node)
                self.emitEndTag(node)

    def visitText(self, node):
        self.emit("text", node.nodeValue)

    def visitComment(self, node):
        self.emit("comment", node.nodeValue)

    def getAttributeList(self, node):
        if not node.hasAttributes():
            return []
        attrList = []
        for attrNode in node.attributes.values():
            item = attrNode.nodeName, attrNode.nodeValue
            if (attrNode.namespaceURI == ZOPE_METAL_NS and
                attrNode.localName == "define-macro"):
                item = item + ("macroHack",)
            attrList.append(item)
        return attrList

class TALCompiler(METALCompiler):

    # Extending METAL method to add attribute replacements
    def getAttributeList(self, node):
        attrList = METALCompiler.getAttributeList(self, node)
        attrDict = self.getAttributeReplacements(node)
        if not attrDict:
            return attrList
        list = []
        for item in attrList:
            key, value = item[:2]
            if attrDict.has_key(key):
                item = (key, value, "replace", attrDict[key])
                del attrDict[key]
            list.append(item)
        return list

    # Overriding METAL method to compile TAL statements
    def compileElement(self, node):
        defines = node.getAttributeNS(ZOPE_TAL_NS, "define")
        repeat = node.getAttributeNS(ZOPE_TAL_NS, "repeat")
        if defines or repeat:
            self.emit("beginScope")
            if defines:
                self.emitDefines(defines)
            self.conditionalElement(node)
            self.emit("endScope")
        else:
            self.conditionalElement(node)

    # Extending METAL method to check for TAL statements
    def checkSpuriousAttributes(self, node):
        METALCompiler.checkSpuriousAttributes(self, node)
        METALCompiler.checkSpuriousAttributes(
            self, node, ZOPE_TAL_NS, KNOWN_TAL_ATTRIBUTES, TALError, "TAL")

    def emitDefines(self, defines):
        for part in splitParts(defines):
            m = re.match(
                r"\s*(?:(global|local)\s+)?(%s)\s+(.*)" % NAME_RE, part)
            if not m:
                raise TALError("invalid z:define syntax: " + `part`)
            scope, name, expr = m.group(1, 2, 3)
            scope = scope or "local"
            cexpr = self.compileExpression(expr)
            if scope == "local":
                self.emit("setLocal", name, cexpr)
            else:
                self.emit("setGlobal", name, cexpr)

    def conditionalElement(self, node):
        condition = node.getAttributeNS(ZOPE_TAL_NS, "condition")
        if condition:
            self.pushProgram()
            self.modifyingElement(node)
            block = self.popProgram()
            self.emit("condition", condition, block)
        else:
            self.modifyingElement(node)

    def modifyingElement(self, node):
        insert = node.getAttributeNS(ZOPE_TAL_NS, "insert")
        replace = node.getAttributeNS(ZOPE_TAL_NS, "replace")
        repeat = node.getAttributeNS(ZOPE_TAL_NS, "repeat")
        n = 0
        if insert: n = n+1
        if replace: n = n+1
        if repeat: n = n+1
        if n > 1:
            raise TALError("can't use z:insert, z:replace, z:repeat together")
        ok = 0
        if insert:
            ok = self.doInsert(node, insert)
        if not ok and replace:
            if node.isSameNode(self.document.documentElement):
                raise TALError("can't use replace on the document element")
            ok = self.doReplace(node, replace)
        if not ok and repeat:
            if node.isSameNode(self.document.documentElement):
                raise TALError("can't use repeat on the document element")
            ok = self.doRepeat(node, repeat)
        if not ok:
            self.emitElement(node)

    def doInsert(self, node, arg):
        key, expr = parseSubstitution(arg)
        if not key:
            return 0
        self.emitStartTag(node)
        self.doSubstitution(key, expr, {})
        self.emitEndTag(node)
        return 1

    def doReplace(self, node, arg):
        key, expr = parseSubstitution(arg)
        if not key:
            return 0
        attrDict = self.getAttributeReplacements(node)
        self.doSubstitution(key, expr, attrDict)
        return 1

    def doSubstitution(self, key, expr, attrDict):
        cexpr = self.compileExpression(expr)
        if key == "text":
            if attrDict:
                print "Warning: z:attributes unused for text replacement"
            self.emit("insertText", cexpr)
        else:
            assert key == "structure"
            self.emit("insertStructure", cexpr, attrDict)

    def doRepeat(self, node, arg):
        m = re.match("\s*(%s)\s+(.*)" % NAME_RE, arg)
        if not m:
            raise TALError("invalid z:repeat syntax: " + `arg`)
        name, expr = m.group(1, 2)
        cexpr = self.compileExpression(expr)
        self.pushProgram()
        self.emitElement(node)
        block = self.popProgram()
        self.emit("loop", name, cexpr, block)
        return 1

    def getAttributeReplacements(self, node):
        attrDict = {}
        value = node.getAttributeNS(ZOPE_TAL_NS, "attributes")
        if value:
            rawDict = parseAttributeReplacements(value)
            for key, expr in rawDict.items():
                attrDict[key] = self.compileExpression(expr)
        return attrDict

def test():
    from driver import FILE, parsefile
    doc = parsefile(FILE)
    compiler = TALCompiler(doc)
    program, macros = compiler()
    from pprint import pprint
    print "---program---"
    pprint(program)
    print "---macros---"
    pprint(macros)

if __name__ == "__main__":
    test()
