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
Make an exact copy of a DOM document (sub)tree.
"""

from xml.dom import Node
from DOMVisitor import DOMVisitor

class CopyingDOMVisitor(DOMVisitor):

    def __init__(self, rootNode, documentFactory):
        DOMVisitor.__init__(self, rootNode)
        self.documentFactory = documentFactory

    def __call__(self):
        self.newDocument = None
        self.curNode = None
        DOMVisitor.__call__(self)
        return self.newDocument

    def visitElement(self, node):
        self.copyElement(node)
        self.copyAllAttributes(node)
        DOMVisitor.visitElement(self, node)
        self.backUp()

    def backUp(self):
        self.curNode = self.curNode.parentNode

    def copyElement(self, node):
        namespaceURI = node.namespaceURI
        if self.newDocument is None:
            # This must be the documentElement node.  Create the
            # document now; this also creates the documentElement node
            self.newDocument = self.documentFactory.createDocument(
                namespaceURI, node.nodeName, None)
            newNode = self.newDocument.documentElement
        else:
            newNode = self.newDocument.createElementNS(namespaceURI,
                                                       node.nodeName)
            self.curNode.appendChild(newNode)
        self.curNode = newNode

    def copyAllAttributes(self, node):
        for attr in node.attributes.values():
            self.copyAttribute(attr)

    def copyAttribute(self, attr):
        if attr.namespaceURI:
            self.curNode.setAttributeNS(
                attr.namespaceURI, attr.nodeName, attr.nodeValue)
        else:
            self.curNode.setAttribute(attr.nodeName, attr.nodeValue)

    def visitText(self, node):
        newNode = self.newDocument.createTextNode(node.nodeValue)
        self.curNode.appendChild(newNode)

    def visitComment(self, node):
        if self.newDocument:
            newNode = self.newDocument.createComment(node.nodeValue)
            self.curNode.appendChild(newNode)
        # XXX Else, this is a comment before the documentElement; lose it.
        
