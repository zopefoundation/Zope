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
import xml.parsers.expat

from pickle import *


class xyap:
    start_handlers = {}
    end_handlers = {}

    def __init__(self):
        top = []
        self._stack = _stack = [top]
        self.push = _stack.append
        self.append = top.append

    def handle_data(self, data):
        self.append(data)

    def unknown_starttag(self, tag, attrs):
        if isinstance(attrs, list):
            attrs = dict(attrs)
        start = self.start_handlers
        if tag in start:
            tag = start[tag](self, tag, attrs)
        else:
            tag = [tag, attrs]
        self.push(tag)
        self.append = tag.append

    def unknown_endtag(self, tag):
        _stack = self._stack
        top = _stack.pop()
        append = self.append = _stack[-1].append
        end = self.end_handlers
        if tag in end:
            top = end[tag](self, tag, top)
        append(top)

class NoBlanks:

    def handle_data(self, data):
        if data.strip():
            self.append(data)


def struct(self, tag, data):
    r = {}
    for k, v in data[2:]:
        r[k] = v
    return r

_nulljoin = "".join

def name(self, tag, data):
    return _nulljoin(data[2:]).strip()

def tuplef(self, tag, data):
    return tuple(data[2:])

class XYap(xyap):
    def __init__(self):
        self._parser = xml.parsers.expat.ParserCreate()
        self._parser.StartElementHandler = self.unknown_starttag
        self._parser.EndElementHandler = self.unknown_endtag
        self._parser.CharacterDataHandler = self.handle_data
        xyap.__init__(self)

class xmlrpc(NoBlanks, XYap):
    end_handlers = {
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

    data = """<?xml version="1.0"?>
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

    data = data.split('\n')
    r = []
    for C in XYap, xmlrpc:
        p = C()
        for l in data:
            p.feed(l)
        p.close()
        r.append(p._stack)

    return r


if __name__=='__main__':
    print test()
