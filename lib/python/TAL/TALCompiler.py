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
from xml.dom import Node

from DOMVisitor import DOMVisitor
from TALGenerator import TALGenerator
from TALDefs import *

class METALCompiler(DOMVisitor, TALGenerator):

    def __init__(self, document, expressionCompiler=None):
        self.document = document
        DOMVisitor.__init__(self, document)
        TALGenerator.__init__(self, expressionCompiler)

    def __call__(self):
        self.namespaceDict = {}
        self.namespaceStack = [self.namespaceDict]
        DOMVisitor.__call__(self)
        assert not self.stack
        return self.program, self.macros

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
        attr_nodes = node.attributes.values() # Cache this!
        self.checkSpuriousAttributes(attr_nodes)
        list = []
        # First, call newNS() for explicit xmlns and xmlns:prefix attributes
        for attr in attr_nodes:
            if attr.namespaceURI == XMLNS_NS:
                # This is a namespace declaration
                # XXX Should be able to use prefix and localName, but can't
                name = attr.name
                i = string.find(name, ':')
                if i < 0:
                    declPrefix = None
                else:
                    declPrefix = name[i+1:]
                self.newNS(declPrefix, attr.value)
        # Add namespace declarations for the node itself, if needed
        if node.namespaceURI:
            if self.newNS(node.prefix, node.namespaceURI):
                if node.prefix:
                    list.append(("xmlns:" + node.prefix, node.namespaceURI))
                else:
                    list.append(("xmlns", node.namespaceURI))
        # Add namespace declarations for each attribute, if needed
        for attr in attr_nodes:
            if attr.namespaceURI:
                if attr.namespaceURI == XMLNS_NS:
                    continue
                if self.newNS(attr.prefix, attr.namespaceURI):
                    if attr.prefix:
                        list.append(
                            ("xmlns:" + attr.prefix, attr.namespaceURI))
                    else:
                        list.append(("xmlns", node.namespaceURI))
        # Add the node's attributes
        list.extend(self.getAttributeList(node, attr_nodes))
        return list

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
            self.expandElement(node)
        self.popNS()

    def checkSpuriousAttributes(self, attr_nodes,
                                ns=ZOPE_METAL_NS,
                                known=KNOWN_METAL_ATTRIBUTES,
                                error=METALError,
                                what="METAL"):
        for attr in attr_nodes:
            if attr.namespaceURI == ns:
                if attr.localName not in known:
                    raise error(
                        "bad %s attribute: %s;\nallowed are: %s" %
                        (what, repr(attr.name), string.join(known)))

    def expandElement(self, node):
        macroName = node.getAttributeNS(ZOPE_METAL_NS, "use-macro")
        if macroName:
            self.pushProgram()
            self.pushSlots()
            self.compileElement(node)
            self.emitUseMacro(macroName)
            return
        macroName = node.getAttributeNS(ZOPE_METAL_NS, "define-macro")
        if macroName:
            self.pushProgram()
            self.compileElement(node)
            self.emitDefineMacro(macroName)
            return
        slotName = node.getAttributeNS(ZOPE_METAL_NS, "define-slot")
        if slotName:
            self.pushProgram()
            self.compileElement(node)
            self.emitDefineSlot(slotName)
            return
        slotName = node.getAttributeNS(ZOPE_METAL_NS, "fill-slot")
        if slotName:
            self.pushProgram()
            self.compileElement(node)
            self.emitFillSlot(slotName)
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
        self.emitText(node.nodeValue)

    def visitComment(self, node):
        self.emit("comment", node.nodeValue)

    def getAttributeList(self, node, attr_nodes):
        if not attr_nodes:
            return []
        attrList = []
        for attrNode in attr_nodes:
            item = attrNode.nodeName, attrNode.nodeValue
            if (attrNode.namespaceURI == ZOPE_METAL_NS and
                attrNode.localName == "define-macro"):
                item = item + ("macroHack",)
            attrList.append(item)
        return attrList

class TALCompiler(METALCompiler):

    # Extending METAL method to add attribute replacements
    def getAttributeList(self, node, attr_nodes):
        attrList = METALCompiler.getAttributeList(self, node, attr_nodes)
        attrDict = self.getAttributeReplacements(node)
        if not attrDict:
            return attrList
        list = []
        for item in attrList:
            key, value = item[:2]
            if attrDict.has_key(key):
                item = (key, value, "replace", attrDict[key])
                del attrDict[key] # XXX Why?
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
    def checkSpuriousAttributes(self, attr_nodes):
        METALCompiler.checkSpuriousAttributes(self, attr_nodes)
        METALCompiler.checkSpuriousAttributes(
            self, attr_nodes,
            ZOPE_TAL_NS, KNOWN_TAL_ATTRIBUTES, TALError, "TAL")

    def conditionalElement(self, node):
        condition = node.getAttributeNS(ZOPE_TAL_NS, "condition")
        if condition:
            self.pushProgram()
            self.modifyingElement(node)
            self.emitCondition(condition)
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
        self.emitStartTag(node)
        self.pushProgram()
        self.visitAllChildren(node)
        self.emitSubstitution(arg)
        self.emitEndTag(node)
        return 1

    def doReplace(self, node, arg):
        attrDict = self.getAttributeReplacements(node)
        self.pushProgram()
        self.emitElement(node)
        self.emitSubstitution(arg, attrDict)
        return 1

    def doRepeat(self, node, arg):
        self.pushProgram()
        self.emitElement(node)
        self.emitRepeat(arg)
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
