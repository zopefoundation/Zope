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
        self.engine = engine

    def visitElement(self, node):
        if not self.checkTAL(node):
            CopyingDOMVisitor.visitElement(self, node)

    def checkTAL(self, node):
        # Do TAL expansion.  Return value is 1 if node expansion
        # complete, 0 if original node should be copied.
        attrs = node.attributes
        if not attrs:
            return 0
        # Collect TAL attributes
        setOps = []
        ifOps = []
        modOps = []
        attrOps = []
        omit = 0
        for attr in attrs.values():
            if attr.namespaceURI == ZOPE_TAL_NS:
                name = attr.localName
                if name == "define":
                    setOps.append(attr)
                elif name == "condition":
                    ifOps.append(attr)
                elif name in ("insert", "replace"):
                    modOps.append(attr)
                elif name == "attributes":
                    attrOps.append(attr)
                elif name == "omit":
                    omit = 1
                else:
                    print "Unrecognized ZOPE/TAL attribute:",
                    print "%s=%s" % (attr.nodeName, `attr.nodeValue`)
                    # This doesn't stop us from doing the rest!
        # If any of these assertions fail, the DOM is broken
        assert len(setOps) <= 1
        assert len(ifOps) <= 1
        assert len(attrOps) <= 1
        # Execute TAL attributes in proper order:
        # 0. omit, 1. define, 2. condition, 3. insert/replace, 4. attributes
        if omit:
            if setOps or ifOps or modOps or attrOps:
                print "Note: z:omit conflicts with all other z:... attributes"
            return 1
        if setOps:
            [attr] = setOps
            self.doDefine(node, attr.nodeValue)
        if ifOps:
            [attr] = ifOps
            if not self.doCondition(node, attr.nodeValue):
                return 1
        attrDict = {}
        if attrOps:
            [attr] = attrOps
            attrDict = self.prepAttr(node, attr.nodeValue)
        if len(modOps) > 1:
            names = map(lambda a: a.nodeName, modOps)
            print "Mutually exclusive ZOPE/TAL attributes:", [names]
        elif modOps:
            [attr] = modOps
            return self.doModify(
                node, attr.localName, attr.nodeValue, attrDict)
        if attrDict:
            ##saveNode = self.curNode
            self.copyElement(node)
            self.copyAttributes(node, attrDict)
            self.visitAllChildren(node)
            self.endVisitElement(node)
            ##self.curNode = saveNode
            return 1
        return 0

    def doDefine(self, node, arg):
        for part in self.splitParts(arg):
            m = re.match(
                r"\s*(global\s+|local\s+)?(%s)\s+as\s+(.*)" % NAME_RE, part)
            if not m:
                print "Bad syntax in z:define argument:", `part`
            else:
                scope, name, expr = m.group(1, 2, 3)
                scope = string.strip(scope or "local")
                value = self.engine.evaluateValue(expr)
                if scope == "local":
                    self.engine.setLocal(name, value)
                else:
                    self.engine.setGlobal(name, value)

    def doCondition(self, node, arg):
        return self.engine.evaluateBoolean(arg)

    def doModify(self, node, cmdName, arg, attrDict):
        assert cmdName in ("insert", "replace")
        inserting = (cmdName == "insert")
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
        self.endVisitElement(node)
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
            self.endVisitElement(node)
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
                if not attrDone and newChild.nodeType == ELEMENT_NODE:
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
                if string.strip(expr) == "nothing":
                    continue
                attrValue = self.engine.evaluateText(expr)
                if attrValue is None:
                    continue
            if namespaceURI:
                self.curNode.setAttributeNS(namespaceURI, attrName, attrValue)
            else:
                self.curNode.setAttribute(attrName, attrValue)

    def prepAttr(self, node, arg):
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
        parts = string.split(arg, ';')
        while "" in parts:
            i = parts.index("")
            if i+1 >= len(parts):
                break
            parts[i-1:i+2] = ["%s;%s" % (parts[i-1], parts[i+1])]
        return parts
