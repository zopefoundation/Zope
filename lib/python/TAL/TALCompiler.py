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
Compile a DOM tree for efficient TAL expansion.

XXX TO DO:
- xmlns attributes
- get macro use/define substitution right
"""

import string
import re
from xml.dom import Node

from DOMVisitor import DOMVisitor

from TALVisitor import  ZOPE_TAL_NS, ZOPE_METAL_NS, NAME_RE
from TALVisitor import macroIndexer, slotIndexer
from TALVisitor import splitParts, parseAttributeReplacements

class TALCompiler(DOMVisitor):

    def __init__(self, document):
        DOMVisitor.__init__(self, document)

    def __call__(self):
        self.macros = {}
        self.program = []
        self.stack = []
        DOMVisitor.__call__(self)
        assert not self.stack
        return self.program, self.macros

    def pushProgram(self):
        self.stack.append(self.program)
        self.program = []

    def popProgram(self):
        program = self.program
        self.program = self.stack.pop()
        return program

    def emit(self, *instruction):
        self.program.append(instruction)

    def emitStartTag(self, node):
        self.emit("startTag", node.nodeName, getAttributeList(node))

    def emitStartEndTag(self, node):
        self.emit("startEndTag", node.nodeName, getAttributeList(node))

    def emitEndTag(self, node):
        self.emit("endTag", node.nodeName)

    def visitElement(self, node):
        if not node.hasAttributes():
            self.emitElement(node)
            return
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
            self.emit("useMacro", macroName, compiledSlots)
            return
        macroName = node.getAttributeNS(ZOPE_METAL_NS, "define-macro")
        if macroName:
            # Save macro definitions
            if self.macros.has_key(macroName):
                print "Warning: duplicate macro definition for", macroName
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
        slotName = node.getAttributeNS(ZOPE_METAL_NS, "use-slot")
        if slotName:
            self.pushProgram()
            self.compileElement(node)
            block = self.popProgram()
            self.emit("useSlot", slotName, block)
            return
        self.compileElement(node)

    def compileElement(self, node):
        if node.getAttributeNodeNS(ZOPE_TAL_NS, "omit"):
            # XXX Question: should 'omit' be done before or after
            # 'define'?  (I.e., is it a shortcut for
            # z:condition:"false" or is it stronger?)
            return
        defines = node.getAttributeNS(ZOPE_TAL_NS, "define")
        if defines:
            self.emit("beginScope")
            self.emitDefines(defines)
            self.conditionalElement(node)
            self.emit("endScope")
        else:
            self.conditionalElement(node)

    def emitDefines(self, defines):
        for part in splitParts(defines):
            m = re.match(
                r"\s*(?:(global|local)\s+)?(%s)\s+as\s+(.*)" % NAME_RE, part)
            if not m:
                print "Bad syntax in z:define argument:", `part`
            else:
                scope, name, expr = m.group(1, 2, 3)
                scope = scope or "local"
                if scope == "local":
                    self.emit("setLocal", name, expr)
                else:
                    self.emit("setGlobal", name, expr)

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
        if not (insert or replace):
            done = 0
        else:
            if insert and replace:
                print "Warning: z:insert overrides z:replace on the same node"
            # XXX Check for z:replace in documentElement
            done = self.doModify(node, insert, insert or replace)
        if not done:
            self.emitElement(node)

    def doModify(self, node, inserting, arg):
        m = re.match(
            r"(?:\s*(text|structure|for\s+(%s)\s+in)\s+)?(.*)" % NAME_RE, arg)
        if not m:
            print "Bad syntax in z:insert/replace:", `arg`
            return 0
        key, name, expr = m.group(1, 2, 3)
        if not key:
            key = "text"
        if key[:3] == "for":
            if inserting:
                self.doInsertLoop(node, name, expr)
            else:
                self.doReplaceLoop(node, name, expr)
        else:
            self.doNonLoop(node, inserting, key, expr)
        return 1

    def doInsertLoop(self, node, name, expr):
        self.emitStartTag(node)
        self.pushProgram()
        self.visitAllChildren(node)
        block = self.popProgram()
        self.emit("loop", name, expr, block)
        self.emitEndTag(node)

    def doReplaceLoop(self, node, name, expr):
        self.pushProgram()
        self.emitElement(node)
        block = self.popProgram()
        self.emit("loop", name, expr, block)

    def doNonLoop(self, node, inserting, key, expr):
        if inserting:
            self.emitStartTag(node)
            self.doInsert(node, key, expr)
            self.emitEndTag(node)
        else:
            self.doInsert(node, key, expr)

    def doInsert(self, node, key, expr):
        attrDict = getAttributeReplacements(node)
        if key == "text":
            if attrDict and not inserting:
                print "Warning: z:attributes unused for text replacement"
            self.emit("insertText", expr)
        else:
            assert key == "structure"
            self.emit("insertStructure", expr, attrDict)

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

def getAttributeList(node):
    if not node.hasAttributes():
        return []
    attrList = []
    for attrNode in node.attributes.values():
        attrList.append((attrNode.nodeName, attrNode.nodeValue))
    attrDict = getAttributeReplacements(node)
    if not attrDict:
        return attrList
    list = []
    for key, value in attrList:
        if attrDict.has_key(key):
            list.append((key, value, attrDict[key]))
            del attrDict[key]
        else:
            list.append((key, value))
    return list

def getAttributeReplacements(node):
    attributes = node.getAttributeNS(ZOPE_TAL_NS, "attributes")
    if not attributes:
        return {}
    else:
        return parseAttributeReplacements(attributes)

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
