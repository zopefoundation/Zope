##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################

"""WebDAV XML parsing tools."""
__version__='$Revision: 1.1 $'[11:-2]

import sys, os, string, xmllib
from Acquisition import Implicit
from cStringIO import StringIO


type_document=0
type_element=1
type_attribute=2
type_text=3
type_cdata=4
type_entityref=5
type_entity=6
type_procinst=7
type_comment=8
type_notation=9


class Node(Implicit):
    """Common base class for Node objects."""
    __name__=''
    __value__=''
    __attrs__=[]
    __nodes__=[]
    __nskey__=''

    def name(self):  return self.__name__
    def attrs(self): return self.__attrs__
    def value(self): return self.__value__
    def nodes(self): return self.__nodes__
    def nskey(self): return self.__nskey__
    
    def addNode(self, node):
        self.__nodes__.append(node.__of__(self))

    def namespace(self):
        nskey=self.__nskey__
        while 1:
            if hasattr(self, '__nsdef__'):
                val=self.__nsdef__.get(nskey, None)
                if val is not None: return val
            if not hasattr(self, 'aq_parent'):
                return ''
            self=self.aq_parent

    def elements(self, name=None, ns=None, lower=string.lower):
        nodes=[]
        name=name and lower(name)
        for node in self.__nodes__:
            if node.__type__==type_element and \
               ((name is None) or (lower(node.__name__)==name)) and \
               ((ns is None) or (node.namespace()==ns)):
                nodes.append(node)
        return nodes
    
    def __getitem__(self, n):
        return self.__nodes__[n]

    def qname(self):
        ns=self.__nskey__
        if ns: ns='%s:' % ns
        return '%s%s' % (ns, self.__name__)

    def toxml(self):
        return self.__value__

    def strval(self):
        return self.toxml()


class Document(Node):
    def __init__(self, encoding='utf-8', stdalone=''):
        self.__name__ ='document'
        self.__nodes__=[]
        self.encoding=encoding
        self.stdalone=stdalone
        self.document=self
        
    def toxml(self):
        result=['<?xml version="1.0" encoding="%s"?>' % self.encoding]
        for node in self.__nodes__:
            result.append(node.toxml())
        return string.join(result, '')

    def __del__(self):
        self.document=None
        print 'bye!'
        
class Element(Node):
    __type__=type_element
    
    def __init__(self, name, attrs={}):
        self.__name__ =name
        self.__attrs__=[]
        self.__nodes__=[]
        self.__nsdef__={}
        self.__nskey__=''
        for name, val in attrs.items():
            attr=Attribute(name, val)
            self.__attrs__.append(attr)
        self.ns_parse()
        parts=string.split(self.__name__, ':')
        if len(parts) > 1:
            self.__nskey__=parts[0]
            self.__name__=string.join(parts[1:], ':')
            
    def ns_parse(self):
        nsdef=self.__nsdef__={}
        for attr in self.attrs():
            name, val=attr.name(), attr.value()
            key=string.lower(name)
            if key[:6]=='xmlns:':
                nsdef[name[6:]]=val
            elif key=='xmlns':
                nsdef['']=val

    def fixup(self):
        self.__attrs__=map(lambda n, s=self: n.__of__(s), self.__attrs__)
        
    def get_attr(self, name, ns=None, default=None):
        for attr in self.__attrs__:
            if attr.name()==name and (ns is None) or (ns==attr.namespace()):
                return attr
        return default

    def remap(self, dict, n=0, top=1):
        # The remap method effectively rewrites an element and all of its
        # children, consolidating namespace declarations into the element
        # on which the remap function is called and fixing up namespace
        # lookup structures.
        nsval=self.namespace()
        if not nsval: nsid=''
        elif not dict.has_key(nsval):
            nsid='ns%d' % n
            dict[nsval]=nsid
            n=n+1
        else: nsid=dict[nsval]
        for attr in self.__attrs__:
            dict, n=attr.remap(dict, n, 0)
        for node in self.elements():
            dict, n=node.remap(dict, n, 0)
        attrs=[]
        for attr in self.__attrs__:
            name=attr.__name__
            if not (((len(name) >= 6) and (name[:6]=='xmlns:')) or \
                    name=='xmlns'):
                attrs.append(attr)
        self.__attrs__=attrs
        self.__nsdef__={}
        self.__nskey__=nsid
        if top:
            attrs=self.__attrs__
            keys=dict.keys()
            keys.sort()
            for key in keys:
                attr=Attribute('xmlns:%s' % dict[key], key)
                attrs.append(attr.__of__(self))
            self.__attrs__=attrs
            self.ns_parse()
        return dict, n

    def toxml(self):
        qname=self.qname()
        result=['<%s' % qname]
        for attr in self.__attrs__:
            result.append(attr.toxml())
        if not self.__value__ and not self.__nodes__:
            result.append('/>')
        else:
            result.append('>')
            for node in self.__nodes__:
                result.append(node.toxml())
            result.append('</%s>' % qname)
        return string.join(result, '')

    def strval(self, top=1):
        if not self.__value__ and not self.__nodes__:
            return ''
        result=map(lambda n: n.toxml(), self.__nodes__)
        return string.join(result, '')

class Attribute(Node):
    __type__=type_attribute
    def __init__(self, name, val):
        self.__name__=name
        self.__value__=val
        self.__nskey__=''
        parts=string.split(name, ':')
        if len(parts) > 1:
            pre=string.lower(parts[0])
            if not (pre in ('xml', 'xmlns')):
                self.__nskey__=parts[0]
                self.__name__=string.join(parts[1:], ':')

    def remap(self, dict, n=0, top=1):
        nsval=self.namespace()
        if not nsval: nsid=''
        elif not dict.has_key(nsval):
            nsid='ns%d' % n
            dict[nsval]=nsid
            n=n+1
        else: nsid=dict[nsval]
        self.__nskey__=nsid
        return dict, n

    def toxml(self):
        ns=self.__nskey__
        if ns: ns='%s:' % ns
        return ' %s%s="%s"' % (ns, self.__name__, self.__value__)
        
class Text(Node):
    __name__='#text'
    __type__=type_text
    def __init__(self, val):
        self.__value__=val
    def toxml(self):
        return escape(self.__value__)


class CData(Node):
    __type__=type_cdata
    __name__='#cdata'
    def __init__(self, val):
        self.__value__=val
    def toxml(self):
        return '<![CDATA[%s]]>' % self.__value__



class EntityRef(Node):
    __name__='#entityref'
    __type__=type_entityref

    def __init__(self, val):
        self.__value__=val
        
    def toxml(self):
        return '&%s;' % self.__value__


class Entity(Node):
    __name__='#entity'
    __type__=type_entity

    def __init__(self, name, pubid, sysid, nname):
        
        self.__value__=val
        
    def toxml(self):
        return ''

class ProcInst(Node):
    __type__=type_procinst
    def __init__(self, name, val):
        self.__name__=name
        self.__value__=val
        
    def toxml(self):
        return '<?%s %s?>' % (self.__name__, self.__value__)


class Comment(Node):
    __name__='#comment'
    __type__=type_comment
    
    def __init__(self, val):
        self.__value__=val

    def toxml(self):
        return '<!--%s-->' % self.__value__





class XmlParser(xmllib.XMLParser):
    def __init__(self):
        xmllib.XMLParser.__init__(self)
        self.root=None
        self.node=None
        
    def parse(self, data):
        self.feed(data)
        self.close()
        return self.root
    
    def add(self, node):
        self.node.addNode(node)

    def push(self, node):
        self.node.addNode(node)
        self.node=self.node.__nodes__[-1]

    def pop(self):
        self.node=self.node.aq_parent

    def unknown_starttag(self, name, attrs):
        node=Element(name, attrs)
        self.push(node)
        # Fixup aq chain!
        self.node.fixup()

    def unknown_endtag(self, name):
        self.pop()

    def handle_xml(self, encoding, stdalone):
        self.root=Document(encoding, stdalone)
        self.node=self.root

    def handle_doctype(self, tag, pubid, syslit, data):
        pass

    def handle_entity(self, name, strval, pubid, syslit, ndata):
        self.add(Entity(name, strval, pubid, syslit, ndata))

    def handle_cdata(self, data):
        self.add(CData(data))

    def handle_proc(self, name, data):
        self.add(ProcInst(name, data))

    def handle_comment(self, data):
        self.add(Comment(data))

    def handle_data(self, data):
        self.add(Text(data))

    def unknown_entityref(self, data):
        self.add(EntityRef(data))



def escape(data, entities={}):
    # snarfed from xml.util...
    data = string.replace(data, "&", "&amp;")
    data = string.replace(data, "<", "&lt;")
    data = string.replace(data, ">", "&gt;")
    for chars, entity in entities.items():
        data = string.replace(data, chars, entity)        
    return data

def remap(data):
    root=XmlParser().parse(data)
    dict={'DAV:':'d', 'http://www.zope.org/propsets/default':'z'}
    root.elements()[0].remap(dict, 0)
    return root.toxml()

def remap_test():
    file=open('big.xml','r')
    data=file.read()
    file.close()
    data=remap(data)
    file=open('new.xml','w')
    file.write(data)
    file.close()
