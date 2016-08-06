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
WebDAV XML request parsing tool using xml.minidom as xml parser.
Code contributed by Simon Eisenmann, struktur AG, Stuttgart, Germany
"""

"""
TODO:

 - Check the methods Node.addNode
   and find out if some code uses/requires this method.

   => If yes implement them, else forget them.

   NOTE: So far i didn't have any problems.
         If you have problems please report them.

 - We are using a hardcoded default of utf-8 for encoding unicode
   strings. While this is suboptimal, it does match the expected
   encoding from OFS.PropertySheet. We need to find a the encoding
   somehow, maybe use the same encoding as the ZMI is using?

"""

from StringIO import StringIO
from xml.dom import minidom
from xml.sax.expatreader import ExpatParser
from xml.sax.saxutils import escape as _escape
from xml.sax.saxutils import unescape as _unescape

escape_entities = {'"': '&quot;',
                   "'": '&apos;',
                   }

unescape_entities = {'&quot;': '"',
                     '&apos;': "'",
                     }

def escape(value, entities=None):
    _ent = escape_entities
    if entities is not None:
        _ent = _ent.copy()
        _ent.update(entities)
    return _escape(value, entities)

def unescape(value, entities=None):
    _ent = unescape_entities
    if entities is not None:
        _ent = _ent.copy()
        _ent.update(entities)
    return _unescape(value, entities)

# utf-8 is hardcoded on OFS.PropertySheets as the expected
# encoding properties will be stored in. Optimally, we should use the
# same encoding as the 'default_encoding' property that is used for
# the ZMI.
zope_encoding = 'utf-8'

class Node:
    """ Our nodes no matter what type
    """

    node = None

    def __init__(self, node):
        self.node = node

    def elements(self, name=None, ns=None):
        nodes = []
        for n in self.node.childNodes:
            if (n.nodeType == n.ELEMENT_NODE and
                ((name is None) or ((n.localName.lower())==name)) and
                ((ns is None) or (n.namespaceURI==ns))):
                nodes.append(Element(n))
        return nodes

    def qname(self):
        return '%s%s' % (self.namespace(), self.name())

    def addNode(self, node):
        # XXX: no support for adding nodes here
        raise NotImplementedError, 'addNode not implemented'

    def toxml(self):
        return self.node.toxml()

    def strval(self):
        return self.toxml().encode(zope_encoding)

    def name(self):  return self.node.localName
    def value(self): return self.node.nodeValue
    def nodes(self): return self.node.childNodes
    def nskey(self): return self.node.namespaceURI

    def namespace(self): return self.nskey()

    def attrs(self):
        return [Node(n) for n in self.node.attributes.values()]

    def remove_namespace_attrs(self):
        # remove all attributes which start with "xmlns:" or
        # are equal to "xmlns"
        if self.node.hasAttributes():
            toremove = []
            for name, value in self.node.attributes.items():
                if name.startswith('xmlns:'):
                    toremove.append(name)
                if name == 'xmlns':
                    toremove.append(name)
            for name in toremove:
                self.node.removeAttribute(name)

    def del_attr(self, name):
        # NOTE: zope calls this after remapping to remove namespace
        #       zope passes attributes like xmlns:n
        #       but the :n isnt part of the attribute name .. gash!

        attr = name.split(':')[0]
        if (self.node.hasAttributes() and
            self.node.attributes.has_key(attr)):
            # Only remove attributes if they exist
            return self.node.removeAttribute(attr)

    def remap(self, dict, n=0, top=1):
        # XXX:  this method is used to do some strange remapping of elements
        #       and namespaces .. someone wants to explain that code?

        # XXX:  i also dont understand why this method returns anything
        #       as the return value is never used

        # NOTE: zope calls this to change namespaces in PropPatch and Lock
        #       we dont need any fancy remapping here and simply remove
        #       the attributes in del_attr

        return {},0

    def __repr__(self):
        if self.namespace():
            return "<Node %s (from %s)>" % (self.name(), self.namespace())
        else: return "<Node %s>" % self.name()

class Element(Node):

    def toxml(self):
        # When dealing with Elements, we only want the Element's content.
        writer = StringIO(u'')
        for n in self.node.childNodes:
            if n.nodeType == n.CDATA_SECTION_NODE:
                # CDATA sections should not be unescaped.
                writer.write(n.data)
            elif n.nodeType == n.ELEMENT_NODE:
                writer.write(n.toxml())
            else:
                # TEXT_NODE and what else?
                value = n.toxml()
                # Unescape possibly escaped values.  We do this
                # because the value is *always* escaped in it's XML
                # representation, and if we store it escaped it will come
                # out *double escaped* when doing a PROPFIND.
                value = unescape(value, entities=unescape_entities)
                writer.write(value)
        return writer.getvalue()


class ProtectedExpatParser(ExpatParser):
    """ See https://bugs.launchpad.net/zope2/+bug/1114688
    """
    def __init__(self, forbid_dtd=True, forbid_entities=True,
                 *args, **kwargs):
        # Python 2.x old style class
        ExpatParser.__init__(self, *args, **kwargs)
        self.forbid_dtd = forbid_dtd
        self.forbid_entities = forbid_entities

    def start_doctype_decl(self, name, sysid, pubid, has_internal_subset):
        raise ValueError("Inline DTD forbidden")

    def entity_decl(self, entityName, is_parameter_entity, value, base, systemId, publicId, notationName):
        raise ValueError("<!ENTITY> forbidden")

    def unparsed_entity_decl(self, name, base, sysid, pubid, notation_name):
        # expat 1.2
        raise ValueError("<!ENTITY> forbidden")

    def reset(self):
        ExpatParser.reset(self)
        if self.forbid_dtd:
            self._parser.StartDoctypeDeclHandler = self.start_doctype_decl
        if self.forbid_entities:
            self._parser.EntityDeclHandler = self.entity_decl
            self._parser.UnparsedEntityDeclHandler = self.unparsed_entity_decl


class XmlParser:
    """ Simple wrapper around minidom to support the required
    interfaces for zope.webdav
    """

    dom = None

    def __init__(self):
        pass

    def parse(self, data):
        self.dom = minidom.parseString(data, parser=ProtectedExpatParser())
        return Node(self.dom)
