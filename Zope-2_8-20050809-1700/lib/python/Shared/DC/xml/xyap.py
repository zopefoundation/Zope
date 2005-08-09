"""Yet another XML parser

This is meant to be very simple:

  - stack based

  - The parser has a table of start handlers and end handlers.

  - start tag handlers are called with the parser instance, tag names
    and attributes.  The result is placed on the stack.  The default
    handler places a special object on the stack (uh, a list, with the
    tag name and attributes as the first two elements. ;)

  - end tag handlers are called with the object on the parser, the tag
    name, and top of the stack right after it has been removed.  The
    result is appended to the object on the top of the stack.

Note that namespace attributes should recieve some special handling.
Oh well.
"""

import string
import xmllib

from pickle import *
from types import ListType


class xyap:
    start_handlers={}
    end_handlers={}

    def __init__(self):
        top=[]
        self._stack=_stack=[top]
        self.push=_stack.append
        self.append=top.append

    def handle_data(self, data): self.append(data)

    def unknown_starttag(self, tag, attrs):
        if type(attrs) is ListType:
            x=0
            temp={}
            while x<len(attrs):
                temp[attrs[x]]=attrs[x+1]
                x=x+2
            attrs=temp
        start=self.start_handlers
        if start.has_key(tag): tag = start[tag](self, tag, attrs)
        else:                  tag = [tag, attrs]
        self.push(tag)
        self.append=tag.append

    def unknown_endtag(self, tag):
        _stack=self._stack
        top=_stack[-1]
        del _stack[-1]
        append=self.append=_stack[-1].append
        end=self.end_handlers
        if end.has_key(tag): top=end[tag](self, tag, top)
        append(top)

class NoBlanks:

    def handle_data(self, data):
        if string.strip(data): self.append(data)


def struct(self, tag, data):
    r={}
    for k, v in data[2:]: r[k]=v
    return r

def name(self, tag, data, join=string.join, strip=string.strip):
    return strip(join(data[2:],''))

def tuplef(self, tag, data): return tuple(data[2:])

class XYap(xyap, xmllib.XMLParser):
    def __init__(self):
        xmllib.XMLParser.__init__(self)
        top=[]
        self._stack=_stack=[top]
        self.push=_stack.append
        self.append=top.append

class xmlrpc(NoBlanks, XYap, xmllib.XMLParser):
    end_handlers={
        'methodCall': tuplef,
        'methodName': name,
        'params': tuplef,
        'param': lambda self, tag, data: data[2],
        'value': lambda self, tag, data: data[2],
        'i4':
        lambda self, tag, data, atoi=string.atoi, name=name:
        atoi(name(self, tag, data)),
        'int':
        lambda self, tag, data, atoi=string.atoi, name=name:
            atoi(name(self, tag, data)),
        'boolean':
        lambda self, tag, data, atoi=string.atoi, name=name:
            atoi(name(self, tag, data)),
        'string': lambda self, tag, data, join=string.join:
            join(data[2:], ''),
        'double':
        lambda self, tag, data, atof=string.atof, name=name:
            atof(name(self, tag, data)),
        'float':
        lambda self, tag, data, atof=string.atof, name=name:
            atof(name(self, tag, data)),
        'struct': struct,
        'member': tuplef,
        'name': name,
        'array': lambda self, tag, data: data[2],
        'data': lambda self, tag, data: data[2:],
        }

def test():

    data="""<?xml version="1.0"?>
    <methodCall>
             <methodName>examples.getStateName
             </methodName>
             <params>
                <param>
                   <value><i4>41</i4></value>
                   </param>

                <param><value>
                <struct>
             <member>
                <name>lowerBound</name>
                <value><i4>18</i4></value>
                </member>
             <member>
                <name>upperBound</name>
                <value><i4>139</i4></value>
                </member>
             </struct></value>
                   </param>

                <param><value>
             <array>
             <data>
                <value><i4>12</i4></value>
                <value><string>Egypt</string></value>
                <value><boolean>0</boolean></value>
                <value><i4>-31</i4></value>
                </data>
             </array></value>
                   </param>

                </params>
             </methodCall>
             """

    data=string.split(data,'\n')
    r=[]
    for C in XYap, xmlrpc:
        p=C()
        for l in data:
            p.feed(l)
        p.close()
        r.append(p._stack)

    return r


if __name__=='__main__': print test()
