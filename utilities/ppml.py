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
"""Provide conversion between Python pickles and XML

"""

__version__ = "1.9"                     # Code version

from pickle import *
from string import replace
import struct
import base64
import string
import xmllib, pickle

#  Create a list of all the characters
L = map(chr,range(256))

#  Create an empty dictionary
d = {}     

#  Create a dictionary d that maps each character to its
#  repr form

for c in L:
    d[c] = repr(c)[1:-1]
    
#  Modify values in the dictionary
d['<'] = "\\074"
d['>'] = "\\076"
d['&'] = "\\046"
d['\n'] = "\\n\n"
d['\t'] = "\\t"
d['\\'] = "\\"
d['\r'] = "\\r"
d["'"] = "\\'"


#  Function convert takes a string and converts it to either
#  repr or base64 format

def convert(S):
    new = ''
    encoding = 'repr'
    new = string.join(map(lambda s: d[s], S), '')
    if len(new) > (1.4*len(S)):
        encoding = 'base64'
        new = base64.encodestring(S)
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
    def value(self): return str(self._v)[:-1]
class Float(Scalar): pass
class String(Scalar):
    def __init__(self, v, encoding=''):
        encoding, v = convert(v)
        self.encoding=encoding
        self._v=v
    def value(self): return self._v
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
	    v=v.__str__(indent+2)
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
    def __init__(self): self._d={}
    def __len__(self): return len(self._d)
    def __setitem__(self, k, v): self._d[k]=v
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
		self._d.items()
		),
	    '')

class Sequence(Collection):

    def __init__(self, v=None): 
	if not v: v=[]
	self._subs=v

    def __len__(self): return len(self._subs)

    def append(self, v): self._subs.append(v)

    def value(self, indent):
	return string.join(map(
	    lambda v, indent=indent: v.__str__(indent),
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
	self.stack[-1].id=self.idprefix+`i`
    dispatch[BINPUT] = load_binput

    def load_long_binput(self):
        i = mloads('i' + self.read(4))
	self.stack[-1].id=self.idprefix+`i`
    dispatch[LONG_BINPUT] = load_long_binput




def ToXMLload(file):
    return ToXMLUnpickler(file).load()

def ToXMLloads(str):
    file = StringIO(str)
    return ToXMLUnpickler(file).load()


class XYap:
    start_handlers={}
    end_handlers={}

    def __init__(self):
        xmllib.XMLParser.__init__(self)
        top=[]
        self._stack=_stack=[top]
        self.push=_stack.append
        self.append=top.append

    def handle_data(self, data): self.append(data)

    def unknown_starttag(self, tag, attrs):
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
    
def name(self, tag, data, join=string.join, strip=string.strip):
    return strip(join(data[2:],''))


def start_pickle(self, tag, attr):
    self._pickleids={}
    return [tag,attr]

def end_string(self, tag, data):
    v=data[2]
    a=data[1]
    if a['encoding'] is not '':
        v=unconvert(a['encoding'],v)
    if a.has_key('id'): self._pickleids[a['id']]=v
    return v

def end_none(self,tag,data):
    return None

def end_reference(self, tag, data):
    return self._pickleids[data[1]['id']]

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

def end_item(self, tag, data):
    v=data[2:]
    return v

class xmlUnpickler(NoBlanks, XYap, xmllib.XMLParser):
    start_handlers={'pickle': start_pickle}
    end_handlers={
        'int':
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
        'none': end_none,
        'list': end_list,
        'tuple': end_tuple,
        'dictionary': end_dictionary,
        'key': lambda self, tag, data: data[2],
        'value': lambda self, tag, data: data[2],
        'item': end_item,
        'reference': end_reference,
        'state': lambda self, tag, data: data[2],
        'klass': lambda self, tag, data: data[2],
        }

def save_none(self, tag, data):
    return 'N'
    
def save_int(self, tag, data):
    v='I'+name(self, tag, data)+'\012'
    return v

def save_float(self, tag, data):
    v='F'+name(self, tag, data)+'\012'
    return v

def save_string(self, tag, data):
    v=data[2]
    a=data[1]
    encoding=a['encoding']
    if encoding is not '':
        v=base.unconvert(encoding,v)
    id=a['id']
    prefix=string.rfind(id,'.')
    if prefix>=0: id=id[prefix:]
    v="S'"+v+"'\012"+"p"+id+"\012"
    return v

def save_tuple(self, tag, data):
    T=data[2:]
    a=data[1]
    v=''
    for x in T:
        v=v+x
    id=a['id']
    prefix=string.rfind(id,'.')
    if prefix>=0: id=id[prefix:]
    if a.has_key('id'): v='('+v+'tp'+id+'\012'
    return v

def save_list(self, tag, data):
    L=data[2:]
    a=data[1]
    id=a['id']
    prefix=string.rfind(id,'.')
    if prefix>=0: id=id[prefix:]
    v='(lp'+id+'\012'
    x=0
    while x<len(L):
        v=v+L[x]+'a'
        x=x+1
    return v

def save_dict(self, tag, data):
    D=data[2:]
    a=data[1]
    id=a['id']
    prefix=string.rfind(id,'.')
    if prefix>=0: id=id[prefix:]
    v='(dp'+id+'\012'
    x=0
    while x<len(D):
        v=v+D[x]+'s'
        x=x+1
    if a.has_key('id'): self._pickleids[a['id']]=D
    return v

def save_item(self, tag, data):
    v=''
    for x in data[2:]:
        v=v+x
    return v        

def save_pickle(self, tag, data):
    v=data[2]+'.'
    return v

def save_reference(self, tag, data):
    a=data[1]
    id=a['id']
    prefix=string.rfind(id,'.')
    if prefix>=0: id=id[prefix:]
    v='g'+id+'\012'
    return v

def save_object(self, tag, data):
    a=data[1]
    v='(c'
    for x in data[2:]:
        v=v+x
    id=a['id']
    prefix=string.rfind(id,'.')
    if prefix>=0: id=id[prefix:]
    v=v+'p'+id+'\012'+'b'
    if a.has_key('id'): self._pickleids[a['id']]=v
    return v

def save_global(self, tag, data):
    a=data[1]
    if a.has_key('id'):
        id=a['id']
        prefix=string.rfind(id,'.')
        if prefix>=0: id=id[prefix:]
        v=a['module']+'\012'+a['name']+'\012op'+id+'\012'
        self._pickleids[a['id']]=v
    else: v=a['module']+'\012'+a['name']+'\012o'
    return v

def save_persis(self, tag, data):
    v=data[2]
    v=v+'Q'
    return v

class xmlPickler(xmlUnpickler):
    start_handlers={'pickle':start_pickle}
    end_handlers={
        'pickle': save_pickle,
        'none': save_none,
        'int': save_int,
        'float': save_float,
        'string': save_string,
        'reference': save_reference,
        'tuple': save_tuple,
        'list': save_list,
        'dictionary': save_dict,
        'item': save_item,
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
    c=C()
    c.foo=1
    c.bar=2
    x=[0,1,2,3]
    y=('abc','abc',c,c)
    x.append(y)
    x.append(y)
    x.append(5)
    print x, '\012'
    f=pickle.dumps(x)
    print f, '\012'
    p=ToXMLloads(f)
    print p, '\012'
    F=xmlPickler()
    data=string.split(str(p),'\n')
    for l in data:
        F.feed(l)
    F.close
    r=F._stack
    print r, '\012'
    print r[0][0], '\012'
    print pickle.loads(r[0][0]), '\012'


if __name__ == '__main__':
    test()
