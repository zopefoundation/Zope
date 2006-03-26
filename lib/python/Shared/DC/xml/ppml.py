##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
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
from string import replace
import struct
import base64
import string
import pickle
import tempfile
import marshal
import xyap

mdumps = marshal.dumps
mloads = marshal.loads

xyap=xyap.xyap

ListType=type([])

# Create repr mappong
reprs = {}
for c in map(chr,range(256)): reprs[c] = repr(c)[1:-1]
reprs['\n'] = "\\n\n"
reprs['\t'] = "\\t"
reprs['\\'] = "\\\\"
reprs['\r'] = "\\r"
reprs["'"] = "\\'"
reprs2={}
reprs2['<'] = "\\074"
reprs2['>'] = "\\076"
reprs2['&'] = "\\046"


#  Function convert takes a string and converts it to either
#  repr or base64 format

def convert(S, find=string.find):
    new = ''
    encoding = 'repr'
    new = string.join(map(reprs.get, S), '')
    if len(new) > (1.4*len(S)):
        encoding = 'base64'
        new = base64.encodestring(S)[:-1]
    elif find(new,'>') >= 0 or find(new,'<') >= 0 or find(new,'&') >= 0:
        if find(new, ']]>') <0 :
            new='<![CDATA[\n\n'+new+'\n\n]]>'
            encoding='cdata'
        else:
            new=string.join(map(lambda s: reprs2.get(s,s), new), '')
    return encoding, new

#  Function unconvert takes a encoding and a string and
#  returns the original string

def unconvert(encoding,S):
    original = ''
    if encoding == 'base64':
        original = base64.decodestring(S)
    else:
        x = string.replace(S, '\n', '')
        original = eval("'"+x+"'")
    return original

t32 = 1L << 32

def p64(v, pack=struct.pack):
    if v < t32: h=0
    else:
        h=v/t32
        v=v%t32
    return pack(">II", h, v)

def u64(v, unpack=struct.unpack):
    h, v = unpack(">ii", v)
    if v < 0: v=t32+v
    if h:
        if h < 0: h=t32+h
        v=h*t32+v
    return v

class Global:

    def __init__(self, module, name):
        self.module=module
        self.name=name

    def __str__(self, indent=0):
        if hasattr(self, 'id'): id=' id="%s"' % self.id
        else: id=''
        name=string.lower(self.__class__.__name__)
        return '%s<%s%s name="%s" module="%s"/>\n' % (
            ' '*indent, name, id, self.name, self.module)

class Scalar:

    def __init__(self, v):
        self._v=v

    def value(self): return self._v

    def __str__(self, indent=0):
        if hasattr(self, 'id'): id=' id="%s"' % self.id
        else: id=''
        name=string.lower(self.__class__.__name__)
        return '%s<%s%s>%s</%s>\n' % (
            ' '*indent, name, id, self.value(), name)

def xmlstr(v):
    v=`v`
    if v[:1]=='\'':
        v=string.replace(v,'"','\\"')
    v=replace(v,'%','\\045')
    v=replace(v,'&','\\046')
    return v[1:-1]

class Int(Scalar): pass
class Long(Scalar):
    def value(self):
        result = str(self._v)
        if result[-1:] == 'L':
            return result[:-1]
        return result

class Float(Scalar): pass
class String(Scalar):
    def __init__(self, v, encoding=''):
        encoding, v = convert(v)
        self.encoding=encoding
        self._v=v
    def __str__(self,indent=0):
        if hasattr(self,'id'):id=' id="%s"' % self.id
        else: id=''
        if hasattr(self, 'encoding'):encoding=' encoding="%s"' % self.encoding
        else: encoding=''
        name=string.lower(self.__class__.__name__)
        return '%s<%s%s%s>%s</%s>\n' % (
            ' '*indent, name, id, encoding, self.value(), name)

class Wrapper:

    def __init__(self, v): self._v=v

    def value(self): return self._v

    def __str__(self, indent=0):
        if hasattr(self, 'id'): id=' id="%s"' % self.id
        else: id=''
        name=string.lower(self.__class__.__name__)
        v=self._v
        i=' '*indent
        if isinstance(v,Scalar):
            return '%s<%s%s> %s </%s>\n' % (i, name, id, str(v)[:-1], name)
        else:
            try:
                v=v.__str__(indent+2)
            except TypeError:
                v=v.__str__()
            return '%s<%s%s>\n%s%s</%s>\n' % (i, name, id, v, i, name)

class Collection:

    def __str__(self, indent=0):
        if hasattr(self, 'id'): id=' id="%s"' % self.id
        else: id=''
        name=string.lower(self.__class__.__name__)
        i=' '*indent
        if self:
            return '%s<%s%s>\n%s%s</%s>\n' % (
                i, name, id, self.value(indent+2), i, name)
        else:
            return '%s<%s%s/>\n' % (i, name, id)

class Key(Wrapper): pass
class Value(Wrapper): pass

class Dictionary(Collection):
    def __init__(self): self._d=[]
    def __len__(self): return len(self._d)
    def __setitem__(self, k, v): self._d.append((k,v))
    def value(self, indent):
        return string.join(
            map(lambda i, ind=' '*indent, indent=indent+4:
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
                ),
            '')

class Sequence(Collection):

    def __init__(self, v=None):
        if not v: v=[]
        self._subs=v

    def __len__(self): return len(self._subs)

    def append(self, v): self._subs.append(v)
    def extend(self, v): self._subs.extend(v)

    def _stringify(self, v, indent):
        try:
            return v.__str__(indent+2)
        except TypeError:
            return v.__str__()

    def value(self, indent):
        return string.join(map(
            lambda v, indent=indent: self._stringify(v, indent),
            self._subs),'')

class List(Sequence): pass
class Tuple(Sequence): pass

class Klass(Wrapper): pass
class State(Wrapper): pass
class Pickle(Wrapper): pass
class Persistent(Wrapper): pass

class none:
    def __str__(self, indent=0): return ' '*indent+'<none/>\n'
none=none()

class Reference(Scalar):
    def __init__(self, v): self._v=v
    def __str__(self, indent=0):
        v=self._v
        name=string.lower(self.__class__.__name__)
        return '%s<%s id="%s"/>\n' % (' '*indent,name,v)

Get=Reference

class Object(Sequence):
    def __init__(self, klass, args):
        self._subs=[Klass(klass), args]

    def __setstate__(self, v): self.append(State(v))

class ToXMLUnpickler(Unpickler):

    def load(self): return Pickle(Unpickler.load(self))

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
        self.append(Int(string.atoi(self.readline()[:-1])))
    dispatch[INT] = load_int

    def load_binint(self):
        self.append(Int(mloads('i' + self.read(4))))
    dispatch[BININT] = load_binint

    def load_binint1(self):
        self.append(Int(mloads('i' + self.read(1) + '\000\000\000')))
    dispatch[BININT1] = load_binint1

    def load_binint2(self):
        self.append(Int(mloads('i' + self.read(2) + '\000\000')))
    dispatch[BININT2] = load_binint2

    def load_long(self):
        self.append(Long(string.atol(self.readline()[:-1], 0)))
    dispatch[LONG] = load_long

    def load_float(self):
        self.append(Float(string.atof(self.readline()[:-1])))
    dispatch[FLOAT] = load_float

    def load_binfloat(self, unpack=struct.unpack):
        self.append(Float(unpack('>d', self.read(8))[0]))
    dispatch[BINFLOAT] = load_binfloat

    def load_string(self):
        self.append(String(eval(self.readline()[:-1],
                                {'__builtins__': {}}))) # Let's be careful
    dispatch[STRING] = load_string

    def load_binstring(self):
        len = mloads('i' + self.read(4))
        self.append(String(self.read(len)))
    dispatch[BINSTRING] = load_binstring

    def load_short_binstring(self):
        len = mloads('i' + self.read(1) + '\000\000\000')
        self.append(String(self.read(len)))
    dispatch[SHORT_BINSTRING] = load_short_binstring

    def load_tuple(self):
        k = self.marker()
        self.stack[k:] = [Tuple(self.stack[k+1:])]
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
        self.stack[k:] = [List(self.stack[k+1:])]
    dispatch[LIST] = load_list

    def load_dict(self):
        k = self.marker()
        d = Dictionary()
        items = self.stack[k+1:]
        for i in range(0, len(items), 2):
            key = items[i]
            value = items[i+1]
            d[key] = value
        self.stack[k:] = [d]
    dispatch[DICT] = load_dict

    def load_inst(self):
        k = self.marker()
        args = Tuple(self.stack[k+1:])
        del self.stack[k:]
        module = self.readline()[:-1]
        name = self.readline()[:-1]
        value=Object(Global(module, name), args)
        self.append(value)
    dispatch[INST] = load_inst

    def load_obj(self):
        stack = self.stack
        k = self.marker()
        klass = stack[k + 1]
        del stack[k + 1]
        args = Tuple(stack[k + 1:])
        del stack[k:]
        value=Object(klass,args)
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
        arg_tup  = stack[-1]
        del stack[-2:]

        value=Object(callable, arg_tup)
        self.append(value)
    dispatch[REDUCE] = load_reduce

    idprefix=''

    def load_get(self):
        self.append(Get(self.idprefix+self.readline()[:-1]))
    dispatch[GET] = load_get

    def load_binget(self):
        i = mloads('i' + self.read(1) + '\000\000\000')
        self.append(Get(self.idprefix+`i`))
    dispatch[BINGET] = load_binget

    def load_long_binget(self):
        i = mloads('i' + self.read(4))
        self.append(Get(self.idprefix+`i`))
    dispatch[LONG_BINGET] = load_long_binget

    def load_put(self):
        self.stack[-1].id=self.idprefix+self.readline()[:-1]
    dispatch[PUT] = load_put

    def load_binput(self):
        i = mloads('i' + self.read(1) + '\000\000\000')
        last = self.stack[-1]
        if getattr(last, 'id', last) is last:
            last.id = self.idprefix + `i`
    dispatch[BINPUT] = load_binput

    def load_long_binput(self):
        i = mloads('i' + self.read(4))
        last = self.stack[-1]
        if getattr(last, 'id', last) is last:
            last.id = self.idprefix + `i`
    dispatch[LONG_BINPUT] = load_long_binput


def ToXMLload(file):
    return ToXMLUnpickler(file).load()

def ToXMLloads(str):
    file = StringIO(str)
    return ToXMLUnpickler(file).load()



class NoBlanks:

    def handle_data(self, data):
        if string.strip(data): self.append(data)

def name(self, tag, data, join=string.join, strip=string.strip):
    return strip(join(data[2:],''))

def start_pickle(self, tag, attrs):
    self._pickleids={}
    return [tag,attrs]

def end_string(self, tag, data):
    v=data[2]
    a=data[1]
    if a['encoding'] is not '':
        v=unconvert(a['encoding'],v)
    if a.has_key('id'): self._pickleids[a['id']]=v
    return v

def end_list(self, tag, data):
    v=data[2:]
    a=data[1]
    if a.has_key('id'): self._pickleids[data[1]['id']]=v
    return v

def end_tuple(self, tag, data):
    v=tuple(data[2:])
    a=data[1]
    if a.has_key('id'): self._pickleids[data[1]['id']]=v
    return v

def end_dictionary(self, tag, data):
    D={}
    a=data[1]
    for k, v in data[2:]: D[k]=v
    if a.has_key('id'): self._pickleids[a['id']]=D
    return D

class xmlUnpickler(NoBlanks, xyap):
    start_handlers={'pickle': start_pickle}
    end_handlers={
        'int':
        lambda self,tag,data,atoi=string.atoi,name=name:
            atoi(name(self, tag, data)),
        'long':
        lambda self,tag,data,atoi=string.atoi,name=name:
            atoi(name(self, tag, data)),
        'boolean':
        lambda self,tag,data,atoi=string.atoi,name=name:
            atoi(name(self, tag, data)),
        'string': end_string ,
        'double':
        lambda self,tag,data,atof=string.atof,name=name:
            atof(name(self, tag, data)),
        'float':
        lambda self,tag,data,atof=string.atof,name=name:
            atof(name(self, tag, data)),
        'none': lambda self, tag, data: None,
        'list': end_list,
        'tuple': end_tuple,
        'dictionary': end_dictionary,
        'key': lambda self, tag, data: data[2],
        'value': lambda self, tag, data: data[2],
        'item': lambda self, tag, data: data[2:],
        'reference': lambda self, tag, data: self._pickleids[data[1]['id']],
        'state': lambda self, tag, data: data[2],
        'klass': lambda self, tag, data: data[2],
        }

def save_int(self, tag, data):
    binary=self.binary
    if binary:
        v=string.atoi(name(self, tag, data))
        i=mdumps(v)[1:]
        if (i[-2:] == '\000\000'):
            if (i[-3] == '\000'):
                v='K'+i[:-3]
                return v
            v='M'+i[:-2]
            return v
        v='J'+i
        return v
    v='I'+name(self, tag, data)+'\012'
    return v

def save_float(self, tag, data):
    binary=self.binary
    if binary: v='G'+struct.pack('>d',string.atof(name(self, tag, data)))
    else: v='F'+name(self, tag, data)+'\012'
    return v

def save_put(self, v, attrs):
    id=attrs.get('id','')
    if id:
        prefix=string.rfind(id,'.')
        if prefix >= 0: id=id[prefix+1:]
        elif id[0]=='i': id=id[1:]
        if self.binary:
            id=string.atoi(id)
            s=mdumps(id)[1:]
            if (id < 256):
                id=s[0]
                put='q'
            else:
                id=s
                put='r'
            id=put+id
        else:
            id="p"+id+"\012"
        return v+id
    return v

def save_string(self, tag, data):
    binary=self.binary
    v=''
    a=data[1]
    if len(data)>2:
        for x in data[2:]:
            v=v+x
    encoding=a['encoding']
    if encoding is not '':
        v=unconvert(encoding,v)
    put='p'
    if binary:
        l=len(v)
        s=mdumps(l)[1:]
        if (l<256):
            v='U'+s[0]+v
        else:
            v='T'+s+v
        put='q'
    else: v="S'"+v+"'\012"
    return save_put(self, v, a)

def save_tuple(self, tag, data):
    T=data[2:]
    if not T: return ')'
    return save_put(self, '('+string.join(T,'')+'t', data[1])

def save_list(self, tag, data):
    L=data[2:]
    a=data[1]
    if self.binary:
        v=save_put(self, ']', a)
        if L: v=v+'('+string.join(L,'')+'e'
    else:
        v=save_put(self, '(l', a)
        if L: v=string.join(L,'a')+'a'
    return v

def save_dict(self, tag, data):
    D=data[2:]
    if self.binary:
        v=save_put(self, '}', data[1])
        if D: v=v+'('+string.join(D,'')+'u'
    else:
        v=save_put(self, '(d', data[1])
        if D: v=v+string.join(D,'s')+'s'
    return v

def save_reference(self, tag, data):
    binary=self.binary
    a=data[1]
    id=a['id']
    prefix=string.rfind(id,'.')
    if prefix>=0: id=id[prefix+1:]
    get='g'
    if binary:
        id=string.atoi(id)
        s=mdumps(id)[1:]
        if (id < 256):
            id=s[0]
            get='h'
        else:
            id=s
            get='j'
        v=get+id
    else: v=get+id+'\012'

    return v

def save_object(self, tag, data):
    v='('+data[2]
    x=data[3][1:]
    stop=string.rfind(x,'t')  # This seems
    if stop>=0: x=x[:stop]    # wrong!
    v=save_put(self, v+x+'o', data[1])
    v=v+data[4]+'b' # state
    return v

def save_global(self, tag, data):
    a=data[1]
    return save_put(self, 'c'+a['module']+'\012'+a['name']+'\012', a)

def save_persis(self, tag, data):
    v=data[2]
    if  self.binary:
        v=v+'Q'
    else:
        v='P'+v
    return v

class xmlPickler(NoBlanks, xyap):
    start_handlers={
        'pickle': lambda self, tag, attrs: [tag, attrs],
        }
    end_handlers={
        'pickle': lambda self, tag, data: str(data[2])+'.',
        'none': lambda self, tag, data: 'N',
        'int': save_int,
        'long': lambda self, tag, data: 'L'+str(data[2])+'L\012',
        'float': save_float,
        'string': save_string,
        'reference': save_reference,
        'tuple': save_tuple,
        'list': save_list,
        'dictionary': save_dict,
        'item': lambda self, tag, data, j=string.join: j(data[2:],''),
        'value': lambda self, tag, data: data[2],
        'key' : lambda self, tag, data: data[2],
        'object': save_object,
        'klass': lambda self, tag, data: data[2],
        'state': lambda self, tag, data: data[2],
        'global': save_global,
        'persistent': save_persis,
        }


# The rest is used for testing only

class C:
    def __cmp__(self, other):
        return cmp(self.__dict__, other.__dict__)

def test():
    import xmllib
    c=C()
    c.foo=1
    c.bar=2
    x=[0,1,2,3]
    y=('abc','abc',c,c)
    x.append(y)
    x.append(y)
    t=()
    l=[]
    s=''
    L = long('999999999999')
    x.append(t)
    x.append(l)
    x.append(s)
    x.append(L)
    x.append(55555)
    x.append(13)
    r=[x]
    print x
    f=pickle.dumps(x)
    print f
    r.append(f)
    q=ToXMLloads(f)
    q=str(q)
    q='<?xml version="1.0"?>\n'+q
    print q
    r.append(q)
    file=''
    F=xmlPickler(file)
    p=xmllib.XMLParser()
    p.start_handlers=F.start_handlers
    p.end_handlers=F.end_handlers
    p.handle_data=F.handle_data
    p.unknown_starttag=F.unknown_starttag
    p.unknown_endtag=F.unknown_endtag
    p._stack=F._stack
    p.push=F.push
    p.append=F.append
    p.file=F.file
    p.tempfile=F.tempfile
    p.binary=1
    data=string.split(q,'\n')
    for l in data:
        p.feed(l)
    p.close()
    z=p._stack
    z=z[0][0]
    print z, '\012'
    r.append(z)
    l=pickle.loads(z)
    print l, '\012'
    r.append(l)

def test1():
    import xmllib
    q=open('Data.xml').read()
    file=open('out','w'+'b')
    F=xmlPickler(file,1)
    p=xmllib.XMLParser()
    p.start_handlers=F.start_handlers
    p.end_handlers=F.end_handlers
    p.handle_data=F.handle_data
    p.unknown_starttag=F.unknown_starttag
    p.unknown_endtag=F.unknown_endtag
    p._stack=F._stack
    p.push=F.push
    p.append=F.append
    p.file=F.file
    p.tempfile=F.tempfile
    data=string.split(q,'\n')
    for l in data:
        p.feed(l)
    p.close()
    z=p._stack
    z=z[0][0]
    print z, '\012'

def test2():
    import xml.parsers.expat
    c=C()
    c.foo=1
    c.bar=2
    x=[0,1,2,3]
    y=('abc','abc',c,c)
    x.append(y)
    x.append(y)
    t=()
    l=[]
    s=''
    L = long('999999999999')
    x.append(t)
    x.append(l)
    x.append(s)
    x.append(L)
    x.append(5)
    x.append(13)
    print x, '\012'
    f=pickle.dumps(x)
    print f, '\012'
    q=ToXMLloads(f)
    q=str(q)
    q='<?xml version="1.0"?>\n'+q
    print q, '\012'
    file=''
    F=xmlPickler()
    F.binary=0
    p=xml.parsers.expat.ParserCreate()
    p.CharacterDataHandler=F.handle_data
    p.StartElementHandler=F.unknown_starttag
    p.EndElementHandler=F.unknown_endtag
    r=p.Parse(q)
    print r, '\012'

def test3():
    import xml.parsers.expat
    data=open('Data.xml').read()
    file=open('out','w'+'b')
    F=xmlPickler()
    F.file=file
    F.binary=1
    p=xml.parsers.expat.ParserCreate()
    p.CharacterDataHandler=F.handle_data
    p.StartElementHandler=F.unknown_starttag
    p.EndElementHandler=F.unknown_endtag
    r=p.Parse(data)
    print r, '\012'

if __name__ == '__main__':
    test()
