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
import regex
import pickle
import tempfile
import marshal
       
ListType=type([])
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

t32 = 1L << 32

def p64(v, pack=struct.pack):
    if v < t32: h=0
    else:
        h=v/t32
        v=v%t32
    return pack(">II", h, v)

def u64(v, unpack=struct.unpack):
    h, v = unpack(">ii", v)
    if v < 0: v=t32-v
    if h:
        if h < 0: h=t32-h
        v=h*t32+v
    return v

def cp(f1, f2, l):
    read=f1.read
    write=f2.write
    n=8192
    
    while l > 0:
        if n > l: n=l
        d=read(n)
        write(d)
        l = l - len(d)

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

class ZopeData:
    def __init__(self, parser, tag, attrs):
        self._pos=0
        self.file=parser.file
        self.tempfile=parser.tempfile

    def append(self, transaction, f=None):
        file=self.file
        write=file.write
        tfile=self.tempfile
        dlen=tfile.tell()
        tfile.seek(0)
        id=transaction.serial
        user, desc, ext = transaction._ude
        transaction._ude=None

        tlen=transaction._thl
        pos=self._pos
        file.seek(pos)
        tl=tlen+dlen
        stl=p64(tl)
        write(struct.pack(
            ">8s" "8s" "c"  "H"         "H"         "H"
            , id, stl, ' ', len(user), len(desc), len(ext),
            ))
        if user: write(user)
        if desc: write(desc)
        if ext: write(ext)

        cp(tfile,file,dlen)

        write(stl)
        self._pos=pos+tl+8


class Transaction:
    def __init__(self, parser, tag, attrs):
        self.file=parser.file
        self.tempfile=parser.tempfile

        self.tempfile.seek(0)
       
        tyme=attrs['time']
        start=0
        stop=string.find(tyme[start:],'-')+start
        year=string.atoi(tyme[start:stop])
        start=stop+1
        stop=string.find(tyme[start:],'-')+start
        month=string.atoi(tyme[start:stop])
        start=stop+1
        stop=string.find(tyme[start:],' ')+start
        day=string.atoi(tyme[start:stop])
        start=stop+1
        stop=string.find(tyme[start:],':')+start
        hour=string.atoi(tyme[start:stop])
        start=stop+1
        stop=string.find(tyme[start:],':')+start
        minute=string.atoi(tyme[start:stop])
        start=stop+1
        second=string.atof(tyme[start:])
        t=(((((year-1900)*12+month-1)*31+day-1)*24+hour)*60+minute)
        t=struct.pack(">If",t,second*(1L<<32)/60)
        self.serial=t
        self._user=user=''
        self._descr=desc=''
        self._ext=ext=''
        self._thl= 23+len(user)+len(desc)+len(ext)
        self._ude= user, desc, ext
        self._index={}
        self._tindex=[]
        self._pos=0
        self._oid='\0\0\0\0\0\0\0\0'

    def append(self, data):
        version=''
        old=self._index.get(self._oid,0)
        pnv=None
        if old:
            file=self.file
            file.seek(old)
            read=file.read
            h=read(42)
            doid,oserial,sprev,stloc,vlen,splen = unpack(">8s8s8s8sH8s", h)
            if doid != self.serial: raise CorruptedDataError, h
#            if vlen:
#                pnv=read(8)
#                if (len(version) != vlen or
#                    (read(8)
#                     and version !=read(vlen))):
#                     raise POSException.VersionLockError, oid
#            if self.serial !=oserial: raise POSException.ConflictError
        tfile=self.tempfile
        write=tfile.write
        pos=self._pos
        serial=self.serial
        oid=self._oid
        here=tfile.tell()+pos+self._thl
        self._tindex.append(self._oid, here)
        serial=self.serial
        write(struct.pack(">8s8s8s8sH8s", oid, serial, p64(old), p64(pos),
                   len(version), p64(len(data))))

#        if version:            
#            if pnv: write(pnv)
#            else: write(p64(old))
#            tvindex=self._tvindex
#            pv=tvindex.get(version, 0) or self._vindexpos(version,0)
#            write(p64(pv))
#            tvindex[version]=here
#            write(version)

        for x in data[2:]:
            write(x)

        return serial

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

class xyap:
    start_handlers={}
    end_handlers={}

    def __init__(self, file, binary=0):
        top=[]
        self.file=file
        self.tempfile=tempfile.TemporaryFile()
        self._stack=_stack=[top]
        self.push=_stack.append
        self.append=top.append
        self.binary=binary

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

class xmlUnpickler(NoBlanks, xyap):
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

def save_string(self, tag, data):
    binary=self.binary
    if len(data)>2: v=data[2]
    else: v=''
    a=data[1]
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
    if a.has_key('id'):
        id=a['id']
        prefix=string.rfind(id,'.')
        if prefix>=0: id=id[prefix+1:]
        if binary:
            id=string.atoi(id)
            s=mdumps(id)[1:]
            if (id < 256):
                id=s[0]
                put='q'
            else:
                id=s
                put='r'
            v=v+put+id
        else: v=v+put+id+"\012"
    return v

def save_tuple(self, tag, data):
    binary=self.binary
    T=data[2:]
    a=data[1]
    v=''
    put='p'
    for x in T:
        v=v+x
    if v is '': return ')'
    v='('+v+'t'
    if a.has_key('id'):
        id=a['id']
        prefix=string.rfind(id,'.')
        if prefix>=0: id=id[prefix+1:]
        if binary:
            id=string.atoi(id)
            s=mdumps(id)[1:]
            if (id < 256):
                id=s[0]
                put='q'
            else:
                id=s
                put='r'
            v=v+put+id
        else:
            v=v+put+id+'\012'
    return v

def save_list(self, tag, data):
    binary=self.binary
    L=data[2:]
    a=data[1]
    v=''
    x=0
    if a.has_key('id'):
        id=a['id']
        prefix=string.rfind(id,'.')
        if prefix>=0: id=id[prefix+1:]
    if binary:
        while x<len(L):
            v=v+L[x]
            x=x+1
        if id:
            id=string.atoi(id)
            s=mdumps(id)[1:]
            if (id < 256):
                id=s[0]
                put='q'
            else:
                id=s
                put='r'
            if v is not '':
                v=']'+put+id+'('+v+'e'
            else: v=']'+put+id
    else:
        while x<len(L):
            v=v+L[x]+'a'
            x=x+1
        if id:
            v='(lp'+id+'\012'+v
    if v=='': v=']'
    
    return v

def save_dict(self, tag, data):
    binary=self.binary
    D=data[2:]
    a=data[1]
    id=a['id']
    prefix=string.rfind(id,'.')
    if prefix>=0: id=id[prefix+1:]
    if binary:
        id=string.atoi(id)
        s=mdumps(id)[1:]
        if (id < 256):
            id=s[0]
            put='q'
        else:
            id=s
            put='r'
        v='}'+put+id
        if len(D)>0: v=v+'('
        x=0
        while x < len(D):
            v=v+D[x]
            x=x+1
        v=v+'u'
    else:
        v='(dp'+id+'\012'
        x=0
        while x<len(D):
            v=v+D[x]+'s'
            x=x+1
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
    binary=self.binary
    a=data[1]
    v='(c'
    j=0
    id=a['id']
    prefix=string.rfind(id,'.')
    if prefix>=0: id=id[prefix+1:]
    put='p'
    if binary:
        id=string.atoi(id)
        s=mdumps(id)[1:]
        if (id < 256):
            id=s[0]
            put='q'
        else:
            id=s
            put='r'
        for x in data[2:]:
            if j==0: v=v + x
            elif j==1:
                x=x[1:]
                stop=string.rfind(x,'t')
                if stop>=0: x=x[:stop]
                v=v+x+'o'+put+id
            elif j==2: v=v+x
            j=j+1
    else:
        for x in data[2:]:
            if j==0: v=v+x
            elif j==1:
                x=x[1:]
                stop=string.rfind(x,'t')
                if stop>=0: x=x[:stop]
                v=v+x+'o'+put+id+'\012'
            elif j==2: v=v+x
            j=j+1
    v=v+'b'
    if a.has_key('id'): self._pickleids[a['id']]=v
    return v

def save_global(self, tag, data):
    binary=self.binary
    a=data[1]
    if a.has_key('id'):
        id=a['id']
        prefix=string.rfind(id,'.')
        if prefix>=0: id=id[prefix+1:]
        put='p'
        if binary:
            id=string.atoi(id)
            s=mdumps(id)[1:]
            if (id < 256):
                id=s[0]
                put='q'
            else:
                id=s
                put='r'
            v=a['module']+'\012'+a['name']+'\012'+put+id
        else:
            v=a['module']+'\012'+a['name']+'\012'+put+id+'\012'
        self._pickleids[a['id']]=v
    else: v=a['module']+'\012'+a['name']+'\012'
    return v

def save_persis(self, tag, data):
    v=data[2]
    if v[0]=='(' and v[1]=='I':
        f=regex.search('\012',v)
        change=v[2:f]
        change=p64(string.atoi(change))
        v=v[:1]+"S'"+change+"'"+v[f:]
    if v[0]=='I':
        f=regex.search('\012',v)
        change=v[1:f]
        change=p64(string.atoi(change)+1)
        v="S'"+change+"'"+v[f:]
    v=v+'Q'
    return v

def save_user(self, tag, data):
    transaction=self._transaction
    if len(data)>2: v=data[2]
    else: v=''
    self._user=v
    transaction._thl=self._transaction._thl+len(v)
    transaction._ude=v,transaction._ude[1],transaction._ude[2]
    return v

def save_description(self, tag, data):
    transaction=self._transaction
    if len(data)>2: v=data[2]
    else: v=''
    a=data[1]
    if a.has_key('encoding'): encoding=a['encoding']
    else: encoding=''
    if encoding:
        v=unconvert(encoding,v)
    transaction._descr=v
    transaction._thl=transaction._thl+len(v)
    transaction._ude=transaction._ude[0],v,transaction._ude[2]
    return v

def save_rec(self, tag, data):
    a=data[1]
    if a.has_key('id'):
        a['id']=p64(string.atoi(a['id'])+1)
    if a.has_key('time'):
        start=0
        stop=string.find(a['time'][start:],'-')+start
        year=string.atoi(a['time'][start:stop])
        start=stop+1
        stop=string.find(a['time'][start:],'-')+start
        month=string.atoi(a['time'][start:stop])
        start=stop+1
        stop=string.find(a['time'][start:],' ')+start
        day=string.atoi(a['time'][start:stop])
        start=stop+1
        stop=string.find(a['time'][start:],':')+start
        hour=string.atoi(a['time'][start:stop])
        start=stop+1
        stop=string.find(a['time'][start:],':')+start
        minute=string.atoi(a['time'][start:stop])
        start=stop+1
        second=string.atof(a['time'][start:])
        a['time']=struct.pack(">If",(((((year-1900)*12)+month-1)*31+day-1)*24+
                                   hour)*60 +minute, second*(1L<<32)/60)
        data[1]=a
        
    return data

def start_transaction(self, tag, attrs):
    self._transaction=Transaction(self, tag, attrs)
    return self._transaction

def start_ZopeData(self, tag, attrs):
    self._ZopeData=ZopeData(self, tag, attrs)
    return self._ZopeData


class xmlPickler(xmlUnpickler):
    start_handlers={'pickle': start_pickle,
                    'transaction': start_transaction,
                    'ZopeData': start_ZopeData,
                    }
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
        'user': save_user,
        'description': save_description,
        'rec': save_rec,
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
    x.append(t)
    x.append(l)
    x.append(s)
    x.append(55555)
    x.append(13)
    r=[x]
    print x
    f=pickle.dumps(x)
    print f
    r.append(f)
    q=ToXMLloads(f)
    q=str(q)
#    q='<?xml version="1.0">\n'+q
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
    p.file=file
    p.tempfile=tempfile.TemporaryFile()
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
    import xml.parsers.pyexpat
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
    x.append(t)
    x.append(l)
    x.append(s)
    x.append(5)
    x.append(13)
    print x, '\012'
    f=pickle.dumps(x)
    print f, '\012'
    q=ToXMLloads(f)
    q=str(q)
    q='<?xml version="1.0">\n'+q
    print q, '\012'
    file=''
    F=xmlPickler(file)
    p=xml.parsers.pyexpat.ParserCreate()
    p.CharacterDataHandler=F.handle_data
    p.StartElementHandler=F.unknown_starttag
    p.EndElementHandler=F.unknown_endtag
    r=p.Parse(q)
    print r, '\012'

if __name__ == '__main__':
    test()


