##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
DOM implementation in ZOPE : Read-Only methods

All standard Zope objects support DOM to a limited extent.
"""
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.Permissions import access_contents_information
from Acquisition import Explicit
from Acquisition import Implicit
from Acquisition import aq_base
from Acquisition import aq_parent
from App.class_init import InitializeClass


# Node type codes
# ---------------

ELEMENT_NODE       = 1
ATTRIBUTE_NODE     = 2
TEXT_NODE          = 3
CDATA_SECTION_NODE = 4
ENTITY_REFERENCE_NODE = 5
ENTITY_NODE        = 6
PROCESSING_INSTRUCTION_NODE = 7
COMMENT_NODE       = 8
DOCUMENT_NODE      = 9
DOCUMENT_TYPE_NODE = 10
DOCUMENT_FRAGMENT_NODE = 11
NOTATION_NODE      = 12

# Exception codes
# ---------------

INDEX_SIZE_ERR              = 1
DOMSTRING_SIZE_ERR          = 2
HIERARCHY_REQUEST_ERR       = 3
WRONG_DOCUMENT_ERR          = 4
INVALID_CHARACTER_ERR       = 5
NO_DATA_ALLOWED_ERR         = 6
NO_MODIFICATION_ALLOWED_ERR = 7
NOT_FOUND_ERR               = 8
NOT_SUPPORTED_ERR           = 9
INUSE_ATTRIBUTE_ERR         = 10

# Exceptions
# ----------

class DOMException(Exception):
    pass
class IndexSizeException(DOMException):
    code = INDEX_SIZE_ERR
class DOMStringSizeException(DOMException):
    code = DOMSTRING_SIZE_ERR
class HierarchyRequestException(DOMException):
    code = HIERARCHY_REQUEST_ERR
class WrongDocumentException(DOMException):
    code = WRONG_DOCUMENT_ERR
class InvalidCharacterException(DOMException):
    code = INVALID_CHARACTER_ERR
class NoDataAllowedException(DOMException):
    code = NO_DATA_ALLOWED_ERR
class NoModificationAllowedException(DOMException):
    code = NO_MODIFICATION_ALLOWED_ERR
class NotFoundException(DOMException):
    code = NOT_FOUND_ERR
class NotSupportedException(DOMException):
    code = NOT_SUPPORTED_ERR
class InUseAttributeException(DOMException):
    code = INUSE_ATTRIBUTE_ERR

# Node classes
# ------------

class Node:
    """
    Node Interface
    """

    security = ClassSecurityInfo()

    # DOM attributes
    # --------------

    security.declareProtected(access_contents_information, 'getNodeName')
    def getNodeName(self):
        """The name of this node, depending on its type"""
        return None

    security.declareProtected(access_contents_information, 'getNodeValue')
    def getNodeValue(self):
        """The value of this node, depending on its type"""
        return None

    security.declareProtected(access_contents_information, 'getParentNode')
    def getParentNode(self):
        """The parent of this node.  All nodes except Document
        DocumentFragment and Attr may have a parent"""
        return None

    security.declareProtected(access_contents_information, 'getChildNodes')
    def getChildNodes(self):
        """Returns a NodeList that contains all children of this node.
        If there are no children, this is a empty NodeList"""
        return NodeList()

    security.declareProtected(access_contents_information, 'getFirstChild')
    def getFirstChild(self):
        """The first child of this node. If there is no such node
        this returns None."""
        return None

    security.declareProtected(access_contents_information, 'getLastChild')
    def getLastChild(self):
        """The last child of this node. If there is no such node
        this returns None."""
        return None

    security.declareProtected(access_contents_information,
                              'getPreviousSibling')
    def getPreviousSibling(self):
        """The node immediately preceding this node.  If
        there is no such node, this returns None."""
        return None

    security.declareProtected(access_contents_information, 'getNextSibling')
    def getNextSibling(self):
        """The node immediately preceding this node.  If
        there is no such node, this returns None."""
        return None

    security.declareProtected(access_contents_information, 'getAttributes')
    def getAttributes(self):
        """Returns a NamedNodeMap containing the attributes
        of this node (if it is an element) or None otherwise."""
        return None

    security.declareProtected(access_contents_information, 'getOwnerDocument')
    def getOwnerDocument(self):
        """The Document object associated with this node.
        When this is a document this is None"""
        node = self
        if hasattr(node, 'aq_parent'):
            node = aq_parent(self)
            return node.getOwnerDocument()
        return node

    # DOM Methods
    # -----------

    security.declareProtected(access_contents_information, 'hasChildNodes')
    def hasChildNodes(self):
        """Returns true if the node has any children, false
        if it doesn't. """
        return len(self.objectIds())

InitializeClass(Node)


class Document(Explicit, Node):
    """
    Document Interface
    """

    security = ClassSecurityInfo()

    # Document Methods
    # ----------------

    security.declareProtected(access_contents_information, 'getImplementation')
    def getImplementation(self):
        """
        The DOMImplementation object that handles this document.
        """
        return DOMImplementation()

    security.declareProtected(access_contents_information, 'getDoctype')
    def getDoctype(self):
        """
        The Document Type Declaration associated with this document.
        For HTML documents as well as XML documents without
        a document type declaration this returns null.
        """
        return None

    security.declareProtected(access_contents_information,
                              'getDocumentElement')
    def getDocumentElement(self):
        """
        This is a convenience attribute that allows direct access to
        the child node that is the root element of the document.
        """
        return aq_parent(self)

    # Node Methods
    # ------------

    def getNodeName(self):
        """The name of this node, depending on its type"""
        return '#document'

    def getNodeType(self):
        """A code representing the type of the node."""
        return DOCUMENT_NODE

    def getOwnerDocument(self):
        """The Document object associated with this node.
        When this is a document this is None"""
        return self

    def getChildNodes(self):
        """Returns a NodeList that contains all children of this node.
        If there are no children, this is a empty NodeList"""
        return NodeList([aq_parent(self)])

    def getFirstChild(self):
        """The first child of this node. If there is no such node
        this returns None."""
        return aq_parent(self)

    def getLastChild(self):
        """The last child of this node. If there is no such node
        this returns None."""
        return aq_parent(self)

    def hasChildNodes(self):
        """Returns true if the node has any children, false
        if it doesn't. """
        return 1

InitializeClass(Document)


class DOMImplementation:
    """
    DOMImplementation Interface
    """

    security = ClassSecurityInfo()

    security.declareProtected(access_contents_information, 'hasFeature')
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
        feature=feature.lower()
        if feature == 'html': return 0
        if feature == 'xml':
            if version is None: return 1
            if version == '1.0': return 1
            return 0

InitializeClass(DOMImplementation)


class Element(Node):
    """
    Element interface
    """

    security = ClassSecurityInfo()

    # Element Attributes
    # ------------------

    security.declareProtected(access_contents_information, 'getTagName')
    def getTagName(self):
        """The name of the element"""
        return self.__class__.__name__

    # Node Attributes
    # ---------------

    def getNodeName(self):
        """The name of this node, depending on its type"""
        return self.getTagName()

    def getNodeType(self):
        """A code representing the type of the node."""
        return ELEMENT_NODE

    def getParentNode(self):
        """The parent of this node.  All nodes except Document
        DocumentFragment and Attr may have a parent"""
        return getattr(self, 'aq_parent', None)

    def getChildNodes(self):
        """Returns a NodeList that contains all children of this node.
        If there are no children, this is a empty NodeList"""
        return  NodeList(self.objectValues())

    def getFirstChild(self):
        """The first child of this node. If there is no such node
        this returns None"""
        children = self.getChildNodes()
        if children:
            return children._data[0]
        return None

    def getLastChild(self):
        """The last child of this node.  If there is no such node
        this returns None."""
        children = self.getChildNodes()
        if children:
            return children._data[-1]
        return None

    def getPreviousSibling(self):
        """The node immediately preceding this node.  If
        there is no such node, this returns None."""
        if hasattr(self, 'aq_parent'):
            parent = aq_parent(self)
            ids=list(parent.objectIds())
            id=self.id
            if type(id) is not type(''): id=id()
            try: index=ids.index(id)
            except: return None
            if index < 1: return None
            return parent.objectValues()[index-1]
        return None

    def getNextSibling(self):
        """The node immediately preceding this node.  If
        there is no such node, this returns None."""
        if hasattr(self, 'aq_parent'):
            parent = aq_parent(self)
            ids=list(parent.objectIds())
            id=self.id
            if type(id) is not type(''): id=id()
            try: index=ids.index(id)
            except: return None
            if index >= len(ids)-1: return None
            return parent.objectValues()[index+1]
        return None

    # Element Methods
    # ---------------

    security.declareProtected(access_contents_information, 'getAttribute')
    def getAttribute(self, name):
        """Retrieves an attribute value by name."""
        return None

    security.declareProtected(access_contents_information, 'getAttributeNode')
    def getAttributeNode(self, name):
        """ Retrieves an Attr node by name or None if
        there is no such attribute. """
        return None

    security.declareProtected(access_contents_information,
                              'getElementsByTagName')
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
                nodeList.append(child)
            if hasattr(child, 'getElementsByTagName'):
                n1 = child.getElementsByTagName(tagname)
                nodeList = nodeList + n1._data
        return NodeList(nodeList)

InitializeClass(Element)


class ElementWithAttributes(Element):
    """
    Elements that allow DOM access to Zope properties of type 'string'.

    Note: This sub-class should only be used by PropertyManagers
    """

    def getAttributes(self):
        """Returns a NamedNodeMap containing the attributes
        of this node (if it is an element) or None otherwise."""
        attribs={}
        for p in self._properties:
            if p['type'] == 'string':
                name=p['id']
                attrib=Attr(name, self.getProperty(name,'')).__of__(self)
                attribs[name]=attrib
        return NamedNodeMap(attribs)

    def getAttribute(self, name):
        """Retrieves an attribute value by name."""
        if self.getPropertyType(name) == 'string':
            return self.getProperty(name,'')

    def getAttributeNode(self, name):
        """Retrieves an Attr node by name or None if
        there is no such attribute. """
        if self.getPropertyType(name) == 'string':
            return Attr(name, self.getProperty(name,'')).__of__(self)
        return None


class ElementWithTitle(Element):
    """
    Elements that allow DOM access to Zope 'title' property.

    Note: Don't use this sub-class for PropertyManagers
    """

    def getAttributes(self):
        """Returns a NamedNodeMap containing the attributes
        of this node (if it is an element) or None otherwise."""
        title = self.getAttributeNode('title')
        if title is not None:
            return NamedNodeMap({'title':title})
        return NamedNodeMap()

    def getAttribute(self, name):
        """Retrieves an attribute value by name."""
        if name=='title' and hasattr(aq_base(self), 'title'):
            return self.title
        return ''

    def getAttributeNode(self, name):
        """Retrieves an Attr node by name or None if
        there is no such attribute. """
        value=self.getAttribute(name)
        if value:
            return Attr(name, value).__of__(self)
        return None


class Root(ElementWithAttributes):
    """
    The top-level Zope object.
    """

    def getOwnerDocument(self):
        """
        """
        return Document().__of__(self)


class NodeList:
    """NodeList interface - Provides the abstraction of an ordered
    collection of nodes.

    Python extensions: can use sequence-style 'len', 'getitem', and
    'for..in' constructs.
    """

    # The security machinery is not willing to treat this like a
    # list just because we act like one. We need to assert that
    # its ok to allow access to items in the nodelist.
    __allow_access_to_unprotected_subobjects__=1

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


class NamedNodeMap:
    """
    NamedNodeMap interface - Is used to represent collections
    of nodes that can be accessed by name.  NamedNodeMaps are not
    maintained in any particular order.

    Python extensions: can use sequence-style 'len', 'getitem', and
    'for..in' constructs, and mapping-style 'getitem'.
    """

    # Tell the security machinery to allow access to items.
    __allow_access_to_unprotected_subobjects__=1

    def __init__(self, data=None):
        if data is None : data = {}
        self._data = data

    def item(self, index):
        """Returns the index-th item in the map"""
        try: return self._data.values()[index]
        except IndexError: return None

    def __getitem__(self, key):
        if type(key)==type(1):
            return self._data.values()[key]
        else:
            return self._data[key]

    def getLength(self):
        """The length of the NodeList"""
        return len(self._data)

    __len__ = getLength

    def getNamedItem(self, name):
        """Retrieves a node specified by name. Parameters:
        name Name of a node to retrieve. Return Value A Node (of any
        type) with the specified name, or None if the specified name
        did not identify any node in the map.
        """
        if self._data.has_key(name):
            return self._data[name]
        return None


class Attr(Implicit, Node):
    """
    Attr interface - The Attr interface represents an attriubte in an
    Element object. Attr objects inherit the Node Interface
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.specified = 1

    def getNodeName(self):
        """The name of this node, depending on its type"""
        return self.name

    def getName(self):
        """Returns the name of this attribute."""
        return self.name

    def getNodeValue(self):
        """The value of this node, depending on its type"""
        return self.value

    def getNodeType(self):
        """A code representing the type of the node."""
        return ATTRIBUTE_NODE

    def getSpecified(self):
        """If this attribute was explicitly given a value in the
        original document, this is true; otherwise, it is false."""
        return self.specified
