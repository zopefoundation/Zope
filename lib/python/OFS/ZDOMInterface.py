from Zope.Interfaces.Interface import Interface

class Node:
    """
    A node.
    """

NodeInterface=Interface(Node) # create the interface object


class Document:
    """A document.
    """
    __extends__ = (NodeInterface,)


DocumentInterface=Interface(Document) # create the interface object


class Element:
    """An element.
    """
    __extends__ = (NodeInterface,)


ElementInterface=Interface(Element) # create the interface object
