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
Copy a DOM tree, applying TAL (Template Attribute Language) transformations.
"""

import string
import re
from xml.dom import Node
from CopyingDOMVisitor import CopyingDOMVisitor

ZOPE_TAL_NS = "http://xml.zope.org/namespaces/tal"
ZOPE_METAL_NS = "http://xml.zope.org/namespaces/metal"

NAME_RE = "[a-zA-Z_][a-zA-Z0-9_]*"

class TALVisitor(CopyingDOMVisitor):

    """
    Copy a DOM tree while applying TAL transformations.

    The DOM tree must have been created with XML namespace information
    included (i.e. I'm not going to interpret your xmlns* attributes
    for you), otherwise we will make an unmodified copy.
    """

    def __init__(self, document, documentFactory, engine):
        CopyingDOMVisitor.__init__(self, document, documentFactory)
        self.document = document
        self.engine = engine
        self.currentMacro = None
        self.originalNode = None
        self.slotIndex = None

    def visitElement(self, node):
        if not node.attributes:
            CopyingDOMVisitor.visitElement(self, node)
            return
        macroName = node.getAttributeNS(ZOPE_METAL_NS, "use-macro")
        if macroName:
            macroNode = self.findMacro(macroName)
            if macroNode:
                self.expandMacro(macroNode, node)
            return
        if self.currentMacro and self.slotIndex and self.originalNode:
            slotName = node.getAttributeNS(ZOPE_METAL_NS, "define-slot")
            if slotName:
                slotNode = self.slotIndex.get(slotName)
                if slotNode:
                    self.visitElement(slotNode)
                    return
        if node.getAttributeNS(ZOPE_TAL_NS, "omit"):
            # XXX Problem: this DOM implementation doesn't
            # differentiate between argument empty and argument
            # absent.
            # XXX Question: should 'omit' be done before or after
            # 'define'?
            return
        defines = node.getAttributeNS(ZOPE_TAL_NS, "define")
        if defines:
            self.engine.beginScope()
            self.doDefine(defines)
            self.finishElement(node)
            self.engine.endScope()
        else:
            self.finishElement(node)

    def finishElement(self, node):
        condition = node.getAttributeNS(ZOPE_TAL_NS, "condition")
        if condition and not self.engine.evaluateBoolean(condition):
            return
        attrDict = {}
        attributes = node.getAttributeNS(ZOPE_TAL_NS, "attributes")
        if attributes:
            attrDict = self.parseAttributeReplacements(attributes)
        insert = node.getAttributeNS(ZOPE_TAL_NS, "insert")
        replace = node.getAttributeNS(ZOPE_TAL_NS, "replace")
        if not (insert or replace):
            done = 0
        else:
            if insert and replace:
                print "Warning: z:insert overrides z:replace on the same node"
            done = self.doModify(node, insert, insert or replace, attrDict)
        if not done:
            self.copyElement(node)
            self.copyAttributes(node, attrDict)
            self.visitAllChildren(node)
            self.backUp()

    def findMacro(self, macroName):
        # XXX This is not written for speed :-)
        doc, localName = self.engine.findMacroDocument(macroName)
        if not doc:
            doc = self.document
        macroDict = macroIndexer(doc)
        if macroDict.has_key(localName):
            return macroDict[localName]
        else:
            print "No macro found:", macroName
            return None

    def expandMacro(self, macroNode, originalNode):
        save = self.currentMacro, self.slotIndex, self.originalNode
        self.currentMacro = macroNode
        self.slotIndex = slotIndexer(originalNode)
        self.originalNode = originalNode
        self.visitElement(macroNode)
        self.currentMacro, self.slotIndex, self.originalNode = save

    def doDefine(self, arg):
        for part in self.splitParts(arg):
            m = re.match(
                r"\s*(?:(global|local)\s+)?(%s)\s+as\s+(.*)" % NAME_RE, part)
            if not m:
                print "Bad syntax in z:define argument:", `part`
            else:
                scope, name, expr = m.group(1, 2, 3)
                scope = scope or "local"
                value = self.engine.evaluateValue(expr)
                if scope == "local":
                    self.engine.setLocal(name, value)
                else:
                    self.engine.setGlobal(name, value)

    def doModify(self, node, inserting, arg, attrDict):
        m = re.match(
            r"(?:\s*(text|structure|for\s+(%s)\s+in)\s+)?(.*)" % NAME_RE, arg)
        if not m:
            print "Bad syntax in z:insert/replace:", `arg`
            return 0
        key, name, expr = m.group(1, 2, 3)
        if not key:
            key = "text"
        saveNode = self.curNode
        if key[:3] == "for":
            if inserting:
                rv = self.doInsertLoop(node, key, name, expr, attrDict)
            else:
                rv = self.doReplaceLoop(node, key, name, expr, attrDict)
        else:
            rv = self.doNonLoop(node, inserting, key, expr, attrDict)
        self.curNode = saveNode
        return rv

    def doInsertLoop(self, node, key, name, expr, attrDict):
        sequence = self.engine.evaluateSequence(expr)
        self.copyElement(node)
        self.copyAttributes(node, attrDict)
        for item in sequence:
            self.engine.setLocal(name, item)
            self.visitAllChildren(node)
        self.backUp()
        return 1

    def doReplaceLoop(self, node, key, name, expr, attrDict):
        if not self.newDocument:
            print "Can't have a z:replace for loop on the documentElement"
            return 0
        sequence = self.engine.evaluateSequence(expr)
        for item in sequence:
            self.engine.setLocal(name, item)
            self.copyElement(node)
            self.copyAttributes(node, attrDict)
            self.visitAllChildren(node)
            self.backUp()
        return 1

    def doNonLoop(self, node, inserting, key, expr, attrDict):
        if inserting:
            self.copyElement(node)
            self.copyAttributes(node, attrDict)
        if key == "text":
            if attrDict:
                print "Warning: z:attributes unused for text replacement"
            data = self.engine.evaluateText(expr)
            newChild = self.newDocument.createTextNode(str(data))
            self.curNode.appendChild(newChild)
        if key == "structure":
            data = self.engine.evaluateStructure(expr)
            attrDone = inserting or not attrDict
            for newChild in data:
                self.curNode.appendChild(newChild)
                if not attrDone and newChild.nodeType == Node.ELEMENT_NODE:
                    self.changeAttributes(newChild, attrDict)
                    attrDone = 1
            if not attrDone:
                # Apparently no element nodes were inserted
                print "Warning: z:attributes unused for struct replacement"
        return 1

    def copyAttributes(self, node, attrDict):
        for attr in node.attributes.values():
            namespaceURI = attr.namespaceURI
            attrName = attr.nodeName
            attrValue = attr.nodeValue
            if attrDict.has_key(attrName):
                expr = attrDict[attrName]
                if expr == "nothing":
                    continue
                attrValue = self.engine.evaluateText(expr)
                if attrValue is None:
                    continue
            if namespaceURI:
                # When expanding a macro, change its define-macro to use-macro
                if (self.currentMacro and
                    namespaceURI == ZOPE_METAL_NS and
                    attr.localName == "define-macro"):
                    attrName = attr.prefix + ":use-macro"
                self.curNode.setAttributeNS(namespaceURI, attrName, attrValue)
            else:
                self.curNode.setAttribute(attrName, attrValue)

    def parseAttributeReplacements(self, arg):
        dict = {}
        for part in self.splitParts(arg):
            m = re.match(r"\s*([^\s=]+)\s*=\s*(.*)", part)
            if not m:
                print "Bad syntax in z:attributes:", `part`
                continue
            name, expr = m.group(1, 2)
            if dict.has_key(name):
                print "Duplicate attribute name in z:attributes:", `part`
                continue
            dict[name] = expr
        return dict

    def splitParts(self, arg):
        # Break in pieces at undoubled semicolons and
        # change double semicolons to singles:
        arg = string.replace(arg, ";;", "\0")
        parts = string.split(arg, ';')
        parts = map(lambda s: string.replace(s, "\0", ";;"), parts)
        return parts


def macroIndexer(document):
    """
    Return a dictionary containing all define-macro nodes in a document.

    The dictionary will have the form {macroName: node, ...}.
    """
    macroIndex = {}
    _macroVisitor(document.documentElement, macroIndex)
    return macroIndex

def _macroVisitor(node, macroIndex, __elementNodeType=Node.ELEMENT_NODE):
    # Internal routine to efficiently recurse down the tree of elements
    macroName = node.getAttributeNS(ZOPE_METAL_NS, "define-macro")
    if macroName:
        if macroIndex.has_key(macroName):
            print ("Duplicate macro definition: %s in <%s>" %
                   (macroName, node.nodeName))
        else:
            macroIndex[macroName] = node
    for child in node.childNodes:
        if child.nodeType == __elementNodeType:
            _macroVisitor(child, macroIndex)


def slotIndexer(rootNode):
    """
    Return a dictionary containing all use-slot nodes in a subtree.

    The dictionary will have the form {slotName: node, ...}.
    """
    slotIndex = {}
    _slotVisitor(rootNode, slotIndex)
    return slotIndex

def _slotVisitor(node, slotIndex, __elementNodeType=Node.ELEMENT_NODE):
    # Internal routine to efficiently recurse down the tree of elements
    slotName = node.getAttributeNS(ZOPE_METAL_NS, "use-slot")
    if slotName:
        if slotIndex.has_key(slotName):
            print ("Duplicate slot definition: %s in <%s>" %
                   (slotName, node.nodeName))
        else:
            slotIndex[slotName] = node
    for child in node.childNodes:
        if child.nodeType == __elementNodeType:
            _slotVisitor(child, slotIndex)
