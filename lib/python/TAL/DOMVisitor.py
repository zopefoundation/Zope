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
Visitor class for DOM trees.

XXX Assumptions: only Document and Element nodes have children worth
visiting.  This is probably wrong, but good enough for now.  Please
let me know which node types I should also deal with!

XXX This may not be as general as the Visitor class in product
ParsedXML.Printer.py, but that uses ParsedXML.DOM.Traversal, and I
don't want this class to depend on the DOM implementation there.

"""

from xml.dom import Node

class DOMVisitor:

    """
    Visitor class for DOM trees.

    Subclass this class, overriding methods for visiting the various
    node types.  Instantiate your subclass with a particular DOM node
    to create a visitor instance for the DOM subtree rooted at that
    node.  Call your instance to visit each node in that subtree once,
    in document order.

    There's a visit<NodeType>() method for each node type.  There's
    also a visitUnknown() which is called for unrecognized node types
    (which shouldn't happen if you are using a standard DOM
    implementation).

    You can influence which nodes are visited in which order by
    overriding visitAllChildren(), and/or by overriding
    visitDocument() and visitElement().  If you override the latter
    two, be careful to either call the base class method or call
    visitAllChildren() as shown in their base class implementations,
    otherwise the tree traversal will break.
    """

    def __init__(self, rootNode):
        """
        Construct a visitor instance.

        Arguments:

        rootNode: the root of the subtree to be traversed.  This is
        typically a document node or an element node.
        """
        self.rootNode = rootNode

    def __call__(self):
        """
        Traverse the subtree given to the constructor.
        """
        self.visitNode(self.rootNode)

    def visitNode(self, node):
        """
        Visit any type of node.

        This switches out to one of the node-specific visitor methods.
        The recursing down into children is handled by calling
        visitAllChildren() in the node-specific visitor methods.
        """
        methodName = self.visitSwitch.get(node.nodeType, "visitUnknown")
        method = getattr(self, methodName)
        method(node)

    # Dictionary mapping node types to method names, used in visitNode
    visitSwitch = {
        Node.ELEMENT_NODE: "visitElement",
        Node.ATTRIBUTE_NODE: "visitAttribute",
        Node.TEXT_NODE: "visitText",
        Node.CDATA_SECTION_NODE: "visitCDATASection",
        Node.ENTITY_REFERENCE_NODE: "visitEntityReference",
        Node.ENTITY_NODE: "visitEntity",
        Node.PROCESSING_INSTRUCTION_NODE: "visitProcessingInstruction",
        Node.COMMENT_NODE: "visitComment",
        Node.DOCUMENT_NODE: "visitDocument",
        Node.DOCUMENT_TYPE_NODE: "visitDocumentType",
        Node.DOCUMENT_FRAGMENT_NODE: "visitDocumentFragment",
        Node.NOTATION_NODE: "visitNotation",
    }

    def visitUnknown(self, node):
        """
        Visit a node of an unknown type.
        """
        pass

    def visitDocument(self, node):
        """
        Visit a document node.

        This calls visitAllChildren() to recurse into the document tree.
        """
        self.visitAllChildren(node)

    def visitElement(self, node):
        """
        Visit an element node.

        This calls visitAllChildren() to recurse into the document
        tree.
        """
        self.visitAllChildren(node)

    def visitAllChildren(self, node):
        """
        Call visitNode() for each child of the given node.
        """
        # XXX eventually use firstChild/nextSibling, for speed
        for child in node.childNodes:
            self.visitNode(child)

    def visitAttribute(self, node):
        """
        Override this empty method to visit an attribute node.
        """
        pass

    def visitText(self, node):
        """
        Override this empty method to visit a text node.
        """
        pass

    def visitCDATASection(self, node):
        """
        Override this empty method to visit a CDATA section node.
        """
        pass

    def visitEntityReference(self, node):
        """
        Override this empty method to visit an entity reference node.
        """
        pass

    def visitEntity(self, node):
        """
        Override this empty method to visit an entity node.
        """
        self.visitAllChildren(node)

    def visitProcessingInstruction(self, node):
        """
        Override this empty method to visit a processing instruction node.
        """
        pass

    def visitComment(self, node):
        """
        Override this empty method to visit a comment node.
        """
        pass

    def visitDocumentType(self, node):
        """
        Override this empty method to visit a document type node.
        """
        pass

    def visitDocumentFragment(self, node):
        """
        Override this empty method to visit a document fragment node.
        """
        pass

    def visitNotation(self, node):
        """
        Override this empty method to visit a notation node.
        """
        pass
