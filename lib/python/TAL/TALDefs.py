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
Common definitions used by TAL and METAL compilation an transformation.
"""

XMLNS_NS = "http://www.w3.org/2000/xmlns/" # URI for XML NS declarations

ZOPE_TAL_NS = "http://xml.zope.org/namespaces/tal"
ZOPE_METAL_NS = "http://xml.zope.org/namespaces/metal"

NAME_RE = "[a-zA-Z_][a-zA-Z0-9_]*"

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

class TALError(Exception):
    pass

class METALError(TALError):
    pass

import re
_attr_re = re.compile(r"\s*([^\s]+)\s*(.*)")
_subst_re = re.compile(r"\s*(?:(text|structure)\s+)?(.*)")
del re

def parseAttributeReplacements(arg):
    dict = {}
    for part in splitParts(arg):
        m = _attr_re.match(part)
        if not m:
            print "Bad syntax in attributes:", `part`
            continue
        name, expr = m.group(1, 2)
        if dict.has_key(name):
            print "Duplicate attribute name in attributes:", `part`
            continue
        dict[name] = expr
    return dict

def parseSubstitution(arg):
    m = _subst_re.match(arg)
    if not m:
        print "Bad syntax in insert/replace:", `arg`
        return None, None
    key, expr = m.group(1, 2)
    if not key:
        key = "text"
    return key, expr

def splitParts(arg):
    # Break in pieces at undoubled semicolons and
    # change double semicolons to singles:
    import string
    arg = string.replace(arg, ";;", "\0")
    parts = string.split(arg, ';')
    parts = map(lambda s, repl=string.replace: repl(s, "\0", ";;"), parts)
    if len(parts) > 1 and not string.strip(parts[-1]):
        del parts[-1] # It ended in a semicolon
    return parts


def macroIndexer(document):
    """
    Return a dictionary containing all define-macro nodes in a document.

    The dictionary will have the form {macroName: node, ...}.
    """
    macroIndex = {}
    _macroVisitor(document.documentElement, macroIndex)
    return macroIndex

from xml.dom import Node

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
    Return a dictionary containing all fill-slot nodes in a subtree.

    The dictionary will have the form {slotName: node, ...}.
    """
    slotIndex = {}
    _slotVisitor(rootNode, slotIndex)
    return slotIndex

def _slotVisitor(node, slotIndex, __elementNodeType=Node.ELEMENT_NODE):
    # Internal routine to efficiently recurse down the tree of elements
    slotName = node.getAttributeNS(ZOPE_METAL_NS, "fill-slot")
    if slotName:
        if slotIndex.has_key(slotName):
            print ("Duplicate slot definition: %s in <%s>" %
                   (slotName, node.nodeName))
        else:
            slotIndex[slotName] = node
    for child in node.childNodes:
        if child.nodeType == __elementNodeType:
            _slotVisitor(child, slotIndex)

del Node
