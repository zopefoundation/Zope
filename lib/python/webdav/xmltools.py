##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################


""" 
WebDAV XML request parsing tool using xml.minidom as xml parser.
Code contributed by Simon Eisenmann, struktur AG, Stuttgart, Germany
"""

__version__='$Revision: 1.15.2.1 $'[11:-2]

"""
TODO:

 - Check the methods Node.addNode, Node.remap and Node del_attr
   and find out if some code uses/requires these methods.

   => If yes implement them, else forget them.
   
   NOTE: So far i didn't have any problems.
         If you have problems please report them.

"""

from xml.dom import minidom

class Node:
    """ our nodes no matter what type """
    
    node = None
    
    def __init__(self, node):
        self.node=node
        
    def elements(self, name=None, ns=None):
        nodes=[ Node(n) for n in self.node.childNodes if n.nodeType == n.ELEMENT_NODE and \
                                                   ((name is None) or ((n.localName.lower())==name)) and \
                                                   ((ns is None) or (n.namespaceURI==ns)) ]
        return nodes

    def qname(self):
        return '%s%s' % (self.namespace(), self.name()) 
        
    def addNode(self, node):
        # XXX: no support for adding nodes here
        raise NotImplementedError, 'addNode not implemented'

    def toxml(self):
        return self.node.toxml()
        
    def strval(self):
        return self.toxml()
        
    def name(self):  return self.node.localName
    def attrs(self): return self.node.attributes
    def value(self): return self.node.nodeValue
    def nodes(self): return self.node.childNodes
    def nskey(self): return self.node.namespaceURI
    
    def namespace(self): return self.nskey()
  
    def del_attr(self, name):
        # XXX: no support for removing attributes 
	#      zope can calls this after remapping to remove namespace
	#      haven't seen this happening though
        return None
  
    def remap(self, dict, n=0, top=1):
        # XXX: this method is used to do some strange remapping of elements
        #      and namespaces .. not sure how to do this with minidom
        #      and if this is even required for something
	#      zope calls this to change namespaces in PropPatch and Lock
        return {},0

    def __repr__(self):
        if self.namespace():
            return "<Node %s (from %s)>" % (self.name(), self.namespace())
        else: return "<Node %s>" % self.name()


class XmlParser:
    """ simple wrapper around minidom to support the required 
        interfaces for zope.webdav
    """

    dom = None
    
    def __init__(self):
        pass
        
    def parse(self, data):
        self.dom=minidom.parseString(data)
        return Node(self.dom)
        
