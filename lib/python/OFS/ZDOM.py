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

import string
import Acquisition


"""DOM implementation in ZOPE : Read-Only methods"""


# Supported Node type codes
# -------------------------
ELEMENT_NODE = 1
ATTRIBUTE_NODE = 2


""" -----------------------------------------------------------------------
Root - top level object, similar to Document also implements the DOM
DOMImplementation Interface"""

class Root:    

    def getParentNode(self):
        return None

    def getPreviousSibling(self):
        return None

    def getNextSibling(self):
        return None

    def getOwnerDocument(self):
        return self

    #DOM Method for INTERFACE DOMImplementation
    def hasFeature(self, feature, version = None):
        """ 
        hasFeature - Test if the DOM implementation implements a specific
        feature. Parameters: feature The package name of the feature to
        test. In Level 1, the legal values are "HTML" and "XML"
        (case-insensitive). version This is the version number of the
        package name to test. In Level 1, this is the string "1.0". If the
        version is not specified, supporting any version of the feature
        will cause the method to return true. Return Value true if the
        feature is implemented in the specified version, false otherwise.
        """
        feature=string.lower(feature)
        if feature == 'html': return 0
        if feature == 'xml':
            if version is None: return 1
            if version == '1.0': return 1
            return 0

""" ----------------------------------------------------------------------
INTERFACE Node """

class Node:

    # DOM attributes    
    def getNodeName(self):
        """The name of this node, depending on its type"""
        return None

    def getNodeValue(self):
        """The value of this node, depending on its type"""
        return None

    def getParentNode(self):
        """The parent of this node.  All nodes except Document
        DocumentFragment and Attr may have a parent"""
        return None

    def getChildNodes(self):
        """Returns a NodeList that contains all children of this node.
        If there are no children, this is a empty NodeList"""
        return NodeList()

    def getFirstChild(self):
        """The first child of this node.  If ther is no such node
        this returns None."""
        return None

    def getLastChild(self):
        """The last child of this node.  If ther is no such node
        this returns None."""
        return None

    def getPreviousSibling(self):
        """The node immediately preceding this node.  If
        there is no such node, this returns None."""
        return None

    def getNextSibling(self):
        """The node immediately following this node.
        If there is no such node, this returns None."""
        return None

    def getAttributes(self):
        """Returns a NamedNodeMap containing the attributes
        of this node (if it is an element) or None otherwise."""
        return None
    
    def getOwnerDocument(self):
        """The Document object associated with this node.
        When this is a document this is None"""
        node = self
        if hasattr(node, 'aq_parent'):
            node = self.aq_parent
            return node.getOwnerDocument()
        return node
        
    # DOM Method    
    def hasChildNodes(self):
        """Returns true if the node has any children, false
        if it doesn't. """
        return len(self.objectIds())
            
""" -----------------------------------------------------------------------
INTERFACE Element """

class Element(Node):

    # Element Attribute
    def getTagName(self):
        """The name of the element"""
        return self.__class__.__name__

    # Node Attributes
    def getNodeName(self):
        return self.getTagName()
      
    def getNodeType(self):
        return ELEMENT_NODE
    
    def getParentNode(self):
        return getattr(self, 'aq_parent', None)

    def getChildNodes(self):
        return  NodeList(self.objectValues())
   
    def getFirstChild(self):
        children = self.getChildNodes()
        if children:
            return children._data[0]
        return None

    def getLastChild(self):
        children = self.getChildNodes()
        if children:
            return children._data[-1]
        return None

    def getPreviousSibling(self):
        if hasattr(self, 'aq_parent'):
            parent = self.aq_parent
            ids=list(parent.objectIds())
            id=self.id
            if type(id) is not type(''): id=id()
            try: index=ids.index(id)
            except: return None
            if index < 1: return None
            return parent.objectValues()[index-1]
        return None

    def getNextSibling(self):
        if hasattr(self, 'aq_parent'):
            parent = self.aq_parent
            ids=list(parent.objectIds())
            id=self.id
            if type(id) is not type(''): id=id()
            try: index=ids.index(id)
            except: return None
            if index >= len(ids)-1: return None
            return parent.objectValues()[index+1]
        return None
      
    # Element Methods
    def getAttribute(self, name):
        """Retrieves an attribute value by name. """
        return None

    def getAttributeNode(self, name):
        """ Retrieves an Attr node by name or null if
        there is no such attribute. """
        return None

    def getElementsByTagName(self, tagname):
        """ Returns a NodeList of all the Elements with a given tag
        name in the order in which they would be encountered in a
        preorder traversal of the Document tree.  Parameter: tagname
        The name of the tag to match (* = all tags). Return Value: A new
        NodeList object containing all the matched Elements.
        """
        nodeList = []
        for child in self.objectValues():
            if (child.getNodeType()==ELEMENT_NODE and \
                    child.getTagName()==tagname or tagname== '*'):
                nodeList.append( child )
            n1 = child.getElementsByTagName(tagname)
            nodeList = nodeList + n1._data
        return NodeList(nodeList)
   
"""-------------------------------------------------------------------"""
class ElementWithAttributes(Element):
    """
    Elements that allow DOM access to Zope properties of type 'string'.
    
    Note: This sub-class should only be used by PropertyManagers
    """
    
    def getAttributes(self):
        attribs={}
        for p in self._properties:
            if p['type'] == 'string':
                name=p['id']
                attrib=Attr(name, self.getProperty(name,'')).__of__(self)
                attribs[name]=attrib
        return NamedNodeMap(attribs)
   
    def getAttribute(self, name):
        if self.getPropertyType(name) == 'string':
            return self.getProperty(name,'')
 
    def getAttributeNode(self, name):
        if self.getPropertyType(name) == 'string':
            return Attr(name, self.getProperty(name,'')).__of__(self)
        return None


class ElementWithTitle(Element):
    """
    Elements that allow DOM access to Zope title property.
    
    Note: Don't use this sub-class for PropertyManagers
    """
    
    def getAttributes(self):
        if self.getAttribute('title'):
            return NamedNodeMap({'title' : self.title})
        return NamedNodeMap()
        
    def getAttribute(self, name):
        if name=='title' and hasattr(self.aq_base, 'title'):
            return self.title
        return ''
    
    def getAttributeNode(self, name):
        value=self.getAttribute(name)
        if value:
            return Attr(name, value).__of__(self)
        return None
            
""" -------------------------------------------------------------------
INTERFACE NodeList - provides the abstraction of an ordered collection
of nodes. """
   
class NodeList:

    def __init__(self,list=None):
        self._data = list or []
    
    def __getitem__(self, index):
        return self._data[index]
        
    def item(self, index):
        """Returns the index-th item in the collection"""
        try: return self._data[index]    
        except IndexError: return None
         
    def getLength(self):
        """The length of the NodeList"""
        return len(self._data)
    
    __len__=getLength
 
""" -----------------------------------------------------------------
INTERFACE NamedNodeMap - Interface is used to represent collections
of nodes that can be accessed by name.  NamedNodeMaps are not
maintained in any particular order.  """

class NamedNodeMap:

    def __init__(self, data=None):
        if data is None : data = {}
        self._data = data

    def __getitem__(self, index):
        """Returns the index-th item in the map"""
        try: return self._data.values()[index]
        except IndexError: return None
        
    item = __getitem__

    def getLength(self):
        """The length of the NodeList"""
        return len(self._data)

    __len__ = getLength
    
    def getNamedItem(self, name):
        """Retrieves a node specified by name. Parameters:
        name Name of a node to retrieve. Return Value  A Node (of any
        type) with the specified name, or null if the specified name
        did not identify any node in the map.
        """
        if self._data.has_key(name): 
            return self._data[name]
        return None

""" ------------------------------------------------------------------
INTERFACE Attr - The Attr interface represents an attriubte in an
Element object.  Attr objects inherit the Node Interface"""

class Attr(Acquisition.Implicit, Node):

    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.specified = 1
        
    def getNodeName(self):
        return self.name

    def getName(self):
        return self.name
    
    def getNodeValue(self):
        return self.value

    def getNodeType(self):
        return ATTRIBUTE_NODE

    def getSpecified(self):
        return self.specified
        
   





















