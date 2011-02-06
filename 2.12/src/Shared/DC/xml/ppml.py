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
"""Provide conversion between Python pickles and XML

"""

__version__ = "1.9"                     # Code version

from pickle import *
import struct
import base64
import re
from marshal import loads as mloads
from xyap import NoBlanks
from xyap import xyap

binary = re.compile('[^\x1f-\x7f]').search


def escape(s, encoding='repr'):
    if binary(s) and isinstance(s, str):
        s = base64.encodestring(s)[:-1]
        encoding = 'base64'
    elif '>' in s or '<' in s or '&' in s:
        if not ']]>' in s:
            s = '<![CDATA[' + s + ']]>'
            encoding = 'cdata'
        else:
            s = s.replace('&', '&amp;')
            s = s.replace('>', '&gt;')
            s = s.replace('<', '&lt;')
    return encoding, s

def unescape(s, encoding):
    if encoding == 'base64':
        return base64.decodestring(s)
    else:
        s = s.replace('&lt;', '<')
        s = s.replace('&gt;', '>')
        return s.replace('&amp;', '&')

class Global:
    def __init__(self, module, name):
        self.module = module
        self.name = name

    def __str__(self, indent=0):
        if hasattr(self, 'id'):
            id = ' id="%s"' % self.id
        else:
            id = ''
        name = self.__class__.__name__.lower()
        return '%s<%s%s name="%s" module="%s"/>\n' % (
            ' ' * indent, name, id, self.name, self.module)

class Scalar:
    def __init__(self, v):
        self._v = v

    def value(self):
        return self._v

    def __str__(self, indent=0):
        if hasattr(self, 'id'):
            id = ' id="%s"' % self.id
        else:
            id = ''
        name = self.__class__.__name__.lower()
        return '%s<%s%s>%s</%s>\n' % (
            ' ' * indent, name, id, self.value(), name)

class Long(Scalar):
    def value(self):
        result = str(self._v)
        if result[-1:] == 'L':
            return result[:-1]
        return result

class String(Scalar):
    def __init__(self, v, encoding=''):
        encoding, v = escape(v, encoding)
        self.encoding = encoding
        self._v = v

    def __str__(self, indent=0):
        if hasattr(self,'id'):
            id = ' id="%s"' % self.id
        else:
            id = ''
        if hasattr(self, 'encoding'):
            encoding = ' encoding="%s"' % self.encoding
        else:
            encoding = ''
        name = self.__class__.__name__.lower()
        return '%s<%s%s%s>%s</%s>\n' % (
            ' ' * indent, name, id, encoding, self.value(), name)

class Unicode(String):
    def __init__(self, v, encoding):
        v = unicode(v, encoding)
        String.__init__(self, v)

    def value(self):
        return self._v.encode('utf-8')

class Wrapper:
    def __init__(self, v):
        self._v = v

    def value(self):
        return self._v

    def __str__(self, indent=0):
        if hasattr(self, 'id'):
            id = ' id="%s"' % self.id
        else:
            id = ''
        name = self.__class__.__name__.lower()
        v = self._v
        i = ' ' * indent
        if isinstance(v, Scalar):
            return '%s<%s%s>%s</%s>\n' % (i, name, id, str(v)[:-1], name)
        else:
            try:
                v = v.__str__(indent + 2)
            except TypeError:
                v = v.__str__()
            return '%s<%s%s>\n%s%s</%s>\n' % (i, name, id, v, i, name)

class Collection:
    def __str__(self, indent=0):
        if hasattr(self, 'id'):
            id = ' id="%s"' % self.id
        else:
            id = ''
        name = self.__class__.__name__.lower()
        i = ' ' * indent
        if self:
            return '%s<%s%s>\n%s%s</%s>\n' % (
                i, name, id, self.value(indent + 2), i, name)
        else:
            return '%s<%s%s/>\n' % (i, name, id)

class Dictionary(Collection):
    def __init__(self):
        self._d = []

    def __len__(self):
        return len(self._d)

    def __setitem__(self, k, v):
        self._d.append((k, v))

    def value(self, indent):
        return ''.join(
            map(lambda i, ind=' ' * indent, indent=indent + 4:
                '%s<item>\n'
                '%s'
                '%s'
                '%s</item>\n'
                %
                (ind,
                 Key(i[0]).__str__(indent),
                 Value(i[1]).__str__(indent),
                 ind),
                self._d
                ))

class Sequence(Collection):
    def __init__(self, v=None):
        if not v:
            v = []
        self._subs = v

    def __len__(self):
        return len(self._subs)

    def append(self, v):
        self._subs.append(v)

    def extend(self, v):
        self._subs.extend(v)

    def _stringify(self, v, indent):
        try:
            return v.__str__(indent + 2)
        except TypeError:
            return v.__str__()

    def value(self, indent):
        return ''.join(map(
            lambda v, indent=indent: self._stringify(v, indent),
            self._subs))

class none:
    def __str__(self, indent=0):
        return ' ' * indent + '<none/>\n'
none = none()

class Reference(Scalar):
    def __init__(self, v):
        self._v = v

    def __str__(self, indent=0):
        v = self._v
        name = self.__class__.__name__.lower()
        return '%s<%s id="%s"/>\n' % (' ' * indent, name, v)

Get = Reference

class Object(Sequence):
    def __init__(self, klass, args):
        self._subs = [Klass(klass), args]

    def __setstate__(self, v):
        self.append(State(v))

class Int(Scalar): pass
class Float(Scalar): pass
class List(Sequence): pass
class Tuple(Sequence): pass
class Key(Wrapper): pass
class Value(Wrapper): pass
class Klass(Wrapper): pass
class State(Wrapper): pass
class Pickle(Wrapper): pass
class Persistent(Wrapper): pass


class ToXMLUnpickler(Unpickler):
    def load(self):
        return Pickle(Unpickler.load(self))

    dispatch = {}
    dispatch.update(Unpickler.dispatch)

    def persistent_load(self, v):
        return Persistent(v)

    def load_persid(self):
        pid = self.readline()[:-1]
        self.append(self.persistent_load(String(pid)))
    dispatch[PERSID] = load_persid

    def load_none(self):
        self.append(none)
    dispatch[NONE] = load_none

    def load_int(self):
        self.append(Int(int(self.readline()[:-1])))
    dispatch[INT] = load_int

    def load_binint(self):
        self.append(Int(mloads('i' + self.read(4))))
    dispatch[BININT] = load_binint

    def load_binint1(self):
        self.append(Int(ord(self.read(1))))
    dispatch[BININT1] = load_binint1

    def load_binint2(self):
        self.append(Int(mloads('i' + self.read(2) + '\000\000')))
    dispatch[BININT2] = load_binint2

    def load_long(self):
        self.append(Long(long(self.readline()[:-1], 0)))
    dispatch[LONG] = load_long

    def load_float(self):
        self.append(Float(float(self.readline()[:-1])))
    dispatch[FLOAT] = load_float

    def load_binfloat(self, unpack=struct.unpack):
        self.append(Float(unpack('>d', self.read(8))[0]))
    dispatch[BINFLOAT] = load_binfloat

    def load_string(self):
        rep = self.readline()[:-1]
        for q in "\"'":
            if rep.startswith(q):
                if not rep.endswith(q):
                    raise ValueError, 'insecure string pickle'
                rep = rep[len(q):-len(q)]
                break
        else:
            raise ValueError, 'insecure string pickle'
        self.append(String(rep.decode('string-escape')))
    dispatch[STRING] = load_string

    def load_binstring(self):
        len = mloads('i' + self.read(4))
        self.append(String(self.read(len)))
    dispatch[BINSTRING] = load_binstring

    def load_unicode(self):
        self.append(Unicode(self.readline()[:-1],'raw-unicode-escape'))
    dispatch[UNICODE] = load_unicode

    def load_binunicode(self):
        len = mloads('i' + self.read(4))
        self.append(Unicode(self.read(len),'utf-8'))
    dispatch[BINUNICODE] = load_binunicode

    def load_short_binstring(self):
        len = ord(self.read(1))
        self.append(String(self.read(len)))
    dispatch[SHORT_BINSTRING] = load_short_binstring

    def load_tuple(self):
        k = self.marker()
        self.stack[k:] = [Tuple(self.stack[k + 1:])]
    dispatch[TUPLE] = load_tuple

    def load_empty_tuple(self):
        self.stack.append(Tuple())
    dispatch[EMPTY_TUPLE] = load_empty_tuple

    def load_empty_list(self):
        self.stack.append(List())
    dispatch[EMPTY_LIST] = load_empty_list

    def load_empty_dictionary(self):
        self.stack.append(Dictionary())
    dispatch[EMPTY_DICT] = load_empty_dictionary

    def load_list(self):
        k = self.marker()
        self.stack[k:] = [List(self.stack[k + 1:])]
    dispatch[LIST] = load_list

    def load_dict(self):
        k = self.marker()
        d = Dictionary()
        items = self.stack[k + 1:]
        for i in range(0, len(items), 2):
            key = items[i]
            value = items[i + 1]
            d[key] = value
        self.stack[k:] = [d]
    dispatch[DICT] = load_dict

    def load_inst(self):
        k = self.marker()
        args = Tuple(self.stack[k + 1:])
        del self.stack[k:]
        module = self.readline()[:-1]
        name = self.readline()[:-1]
        value = Object(Global(module, name), args)
        self.append(value)
    dispatch[INST] = load_inst

    def load_obj(self):
        stack = self.stack
        k = self.marker()
        klass = stack[k + 1]
        del stack[k + 1]
        args = Tuple(stack[k + 1:])
        del stack[k:]
        value = Object(klass, args)
        self.append(value)
    dispatch[OBJ] = load_obj

    def load_global(self):
        module = self.readline()[:-1]
        name = self.readline()[:-1]
        self.append(Global(module, name))
    dispatch[GLOBAL] = load_global

    def load_reduce(self):
        stack = self.stack

        callable = stack[-2]
        arg_tup = stack[-1]
        del stack[-2:]

        value = Object(callable, arg_tup)
        self.append(value)
    dispatch[REDUCE] = load_reduce

    idprefix=''

    def load_get(self):
        self.append(Get(self.idprefix + self.readline()[:-1]))
    dispatch[GET] = load_get

    def load_binget(self):
        i = ord(self.read(1))
        self.append(Get(self.idprefix + repr(i)))
    dispatch[BINGET] = load_binget

    def load_long_binget(self):
        i = mloads('i' + self.read(4))
        self.append(Get(self.idprefix + repr(i)))
    dispatch[LONG_BINGET] = load_long_binget

    def load_put(self):
        self.stack[-1].id = self.idprefix + self.readline()[:-1]
    dispatch[PUT] = load_put

    def load_binput(self):
        i = ord(self.read(1))
        last = self.stack[-1]
        if getattr(last, 'id', last) is last:
            last.id = self.idprefix + repr(i)
    dispatch[BINPUT] = load_binput

    def load_long_binput(self):
        i = mloads('i' + self.read(4))
        last = self.stack[-1]
        if getattr(last, 'id', last) is last:
            last.id = self.idprefix + repr(i)
    dispatch[LONG_BINPUT] = load_long_binput


def ToXMLload(file):
    return ToXMLUnpickler(file).load()

def ToXMLloads(str):
    from StringIO import StringIO
    file = StringIO(str)
    return ToXMLUnpickler(file).load()

def name(self, tag, data):
    return ''.join(data[2:]).strip()

def start_pickle(self, tag, attrs):
    self._pickleids = {}
    return [tag, attrs]

def save_int(self, tag, data):
    if self.binary:
        v = int(name(self, tag, data))
        if v >= 0:
            if v <= 0xff:
                return BININT1 + chr(v)
            if v <= 0xffff:
                return '%c%c%c' % (BININT2, v & 0xff, v >> 8)
        hb = v >> 31
        if hb == 0 or hb == -1:
            return BININT + struct.pack('<i', v)
    return INT + name(self, tag, data) + '\n'

def save_float(self, tag, data):
    if self.binary:
        return BINFLOAT + struct.pack('>d', float(name(self, tag, data)))
    else:
        return FLOAT + name(self, tag, data) + '\n'

def save_put(self, v, attrs):
    id = attrs.get('id', '')
    if id:
        prefix = id.rfind('.')
        if prefix >= 0:
            id = id[prefix + 1:]
        elif id[0] == 'i':
            id = id[1:]
        if self.binary:
            id = int(id)
            if id < 256:
                id = BINPUT + chr(id)
            else:
                id = LONG_BINPUT + struct.pack('<i', id)
        else:
            id = PUT + repr(id) + '\n'
        return v + id
    return v

def save_string(self, tag, data):
    a = data[1]
    v = ''.join(data[2:])
    encoding = a['encoding']
    if encoding is not '':
        v = unescape(v, encoding)
    if self.binary:
        l = len(v)
        if l < 256:
            v = SHORT_BINSTRING + chr(l) + v
        else:
            v = BINSTRING + struct.pack('<i', l) + v
    else:
        v = STRING + repr(v) + '\n'
    return save_put(self, v, a)

def save_unicode(self, tag, data):
    a = data[1]
    v = ''.join(data[2:])
    encoding = a['encoding']
    if encoding is not '':
        v = unescape(v, encoding)
    if self.binary:
        v = v.encode('utf-8')
        v = BINUNICODE + struct.pack("<i", len(v)) + v
    else:
        v = v.replace("\\", "\\u005c")
        v = v.replace("\n", "\\u000a")
        v.encode('raw-unicode-escape')
        v = UNICODE + v + '\n'
    return save_put(self, v, a)

def save_tuple(self, tag, data):
    T = data[2:]
    if not T:
        return EMPTY_TUPLE
    return save_put(self, MARK + ''.join(T) + TUPLE, data[1])

def save_list(self, tag, data):
    L = data[2:]
    if self.binary:
        v = save_put(self, EMPTY_LIST, data[1])
        if L:
            v = v + MARK + ''.join(L) + APPENDS
    else:
        v = save_put(self, MARK + LIST, data[1])
        if L:
            v = APPEND.join(L) + APPEND
    return v

def save_dict(self, tag, data):
    D = data[2:]
    if self.binary:
        v = save_put(self, EMPTY_DICT, data[1])
        if D:
            v = v + MARK + ''.join(D) + SETITEMS
    else:
        v = save_put(self, MARK + DICT, data[1])
        if D:
            v = v + SETITEM.join(D) + SETITEM
    return v

def save_reference(self, tag, data):
    a = data[1]
    id = a['id']
    prefix = id.rfind('.')
    if prefix >= 0:
        id = id[prefix + 1:]
    if self.binary:
        id = int(id)
        if id < 256:
            return BINGET + chr(id)
        else:
            return LONG_BINGET + struct.pack('<i', i)
    else:
        return GET + repr(id) + '\n'

def save_object(self, tag, data):
    v = MARK + data[2]
    x = data[3][1:]
    stop = x.rfind('t')  # This seems
    if stop >= 0:        # wrong!
        x = x[:stop]
    v = save_put(self, v + x + OBJ, data[1])
    v = v + data[4] + BUILD # state
    return v

def save_global(self, tag, data):
    a = data[1]
    return save_put(self, GLOBAL + a['module'] + '\n' + a['name'] + '\n', a)

def save_persis(self, tag, data):
    v = data[2]
    if self.binary:
        return v + BINPERSID
    else:
        return PERSID + v

class xmlPickler(NoBlanks, xyap):
    start_handlers = {
        'pickle': lambda self, tag, attrs: [tag, attrs],
        }
    end_handlers = {
        'pickle': lambda self, tag, data: str(data[2]) + STOP,
        'none': lambda self, tag, data: NONE,
        'int': save_int,
        'long': lambda self, tag, data: LONG + str(data[2]) + LONG + '\n',
        'float': save_float,
        'string': save_string,
        'reference': save_reference,
        'tuple': save_tuple,
        'list': save_list,
        'dictionary': save_dict,
        'item': lambda self, tag, data: ''.join(map(str, data[2:])),
        'value': lambda self, tag, data: data[2],
        'key' : lambda self, tag, data: data[2],
        'object': save_object,
        'klass': lambda self, tag, data: data[2],
        'state': lambda self, tag, data: data[2],
        'global': save_global,
        'persistent': save_persis,
        'unicode': save_unicode,
        }


# The rest is used for testing only

class C:
    def __cmp__(self, other):
        return cmp(self.__dict__, other.__dict__)

def test():
    import xmllib
    import pickle
    c = C()
    c.foo = 1
    c.bar = 2
    x = [0, 1, 2, 3]
    y = ('abc', 'abc', c, c)
    x.append(y)
    x.append(y)
    t = ()
    l = []
    s = ''
    L = long('999999999999')
    x.append(t)
    x.append(l)
    x.append(s)
    x.append(L)
    x.append(55555)
    x.append(13)
    r = [x]
    print x
    f = pickle.dumps(x)
    print f
    r.append(f)
    q = ToXMLloads(f)
    q = str(q)
    q = '<?xml version="1.0"?>\n' + q
    print q
    r.append(q)
    F = xmlPickler()
    F.binary = 1
    p = xmllib.XMLParser()
    p.start_handlers = F.start_handlers
    p.end_handlers = F.end_handlers
    p.handle_data = F.handle_data
    p.unknown_starttag = F.unknown_starttag
    p.unknown_endtag = F.unknown_endtag
    p._stack = F._stack
    p.push = F.push
    p.append = F.append
    data = q.split('\n')
    for l in data:
        p.feed(l)
    p.close()
    z = p._stack
    z = z[0][0]
    print z, '\n'
    r.append(z)
    l = pickle.loads(z)
    print l, '\n'
    r.append(l)

def test1():
    import xml.parsers.expat
    import pickle
    c = C()
    c.foo = 1
    c.bar = 2
    x = [0, 1, 2, 3]
    y = ('abc', 'abc', c, c)
    x.append(y)
    x.append(y)
    t = ()
    l = []
    s = ''
    L = long('999999999999')
    x.append(t)
    x.append(l)
    x.append(s)
    x.append(L)
    x.append(5)
    x.append(13)
    print x, '\n'
    f = pickle.dumps(x)
    print f, '\n'
    q = ToXMLloads(f)
    q = str(q)
    q = '<?xml version="1.0"?>\n' + q
    print q, '\n'
    F = xmlPickler()
    F.binary = 0
    p = xml.parsers.expat.ParserCreate()
    p.CharacterDataHandler = F.handle_data
    p.StartElementHandler = F.unknown_starttag
    p.EndElementHandler = F.unknown_endtag
    r = p.Parse(q)
    print r, '\n'

if __name__ == '__main__':
    test()
