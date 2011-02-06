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
"""Python implementations of document template some features

XXX This module is no longer actively used, but is left as an
XXX implementation reference for cDocumentTemplate

$Id$"""
__version__='$Revision: 1.42 $'[11:-2]

import sys, types
from types import StringType, UnicodeType, TupleType
from DocumentTemplate.ustr import ustr

import warnings
warnings.warn('pDocumentTemplate is not longer in active use. '
              'It remains only as an implementation reference.',
              DeprecationWarning)
              
ClassTypes = [types.ClassType]

try:
    from ExtensionClass import Base
except ImportError:
    pass
else:
    class c(Base): pass
    ClassTypes.append(c.__class__)


def safe_callable(ob):
    # Works with ExtensionClasses and Acquisition.
    if hasattr(ob, '__class__'):
        if hasattr(ob, '__call__'):
            return 1
        else:
            return type(ob) in ClassTypes
    else:
        return callable(ob)

class InstanceDict:

    guarded_getattr=None

    def __init__(self,o,namespace,guarded_getattr=None):
        self.self=o
        self.cache={}
        self.namespace=namespace
        if guarded_getattr is None:
            self.guarded_getattr = namespace.guarded_getattr
        else: self.guarded_getattr = guarded_getattr

    def has_key(self,key):
        return hasattr(self.self,key)

    def keys(self):
        return self.self.__dict__.keys()

    def __repr__(self): return 'InstanceDict(%s)' % str(self.self)

    def __getitem__(self,key):

        cache=self.cache
        if cache.has_key(key): return cache[key]

        inst=self.self

        if key[:1]=='_':
            if key != '__str__':
                raise KeyError, key # Don't divuldge private data
            else:
                return str(inst)

        get = self.guarded_getattr
        if get is None:
            get = getattr

        try: r = get(inst, key)
        except AttributeError: raise KeyError, key

        self.cache[key]=r
        return r

    def __len__(self):
        return 1

class MultiMapping:

    def __init__(self): self.dicts=[]

    def __getitem__(self, key):
        for d in self.dicts:
            try:
                return d[key]
            except (KeyError, AttributeError):
                # XXX How do we get an AttributeError?
                pass
        raise KeyError, key

    def push(self,d): self.dicts.insert(0,d)

    def pop(self, n=1):
        r = self.dicts[-1]
        del self.dicts[:n]
        return r

    def keys(self):
        kz = []
        for d in self.dicts:
            kz = kz + d.keys()
        return kz

class DictInstance:

    def __init__(self, mapping):
        self.__d=mapping

    def __getattr__(self, name):
        try: return self.__d[name]
        except KeyError: raise AttributeError, name

class TemplateDict:

    level=0

    def _pop(self, n=1): return self.dicts.pop(n)
    def _push(self, d): return self.dicts.push(d)

    def __init__(self):
        m=self.dicts=MultiMapping()
        self._pop=m.pop
        self._push=m.push
        try: self.keys=m.keys
        except: pass

    def __getitem__(self,key,call=1):

        v = self.dicts[key]
        if call:
            if hasattr(v, '__render_with_namespace__'):
                return v.__render_with_namespace__(self)
            vbase = getattr(v, 'aq_base', v)
            if safe_callable(vbase):
                if getattr(vbase, 'isDocTemp', 0):
                    v = v(None, self)
                else:
                    v = v()
        return v

    def __len__(self):
        total = 0
        for d in self.dicts.dicts:
            total = total + len(d)
        return total

    def has_key(self,key):
        try:
            v=self.dicts[key]
        except KeyError:
            return 0
        return 1

    getitem=__getitem__

    def __call__(self, *args, **kw):
        if args:
            if len(args)==1 and not kw:
                m=args[0]
            else:
                m=self.__class__()
                for a in args: m._push(a)
                if kw: m._push(kw)
        else: m=kw
        return (DictInstance(m),)

def render_blocks(blocks, md):
    rendered = []
    append=rendered.append
    for section in blocks:
        if type(section) is TupleType:
            l=len(section)
            if l==1:
                # Simple var
                section=section[0]
                if type(section) is StringType: section=md[section]
                else: section=section(md)
                section=ustr(section)
            else:
                # if
                cache={}
                md._push(cache)
                try:
                    i=0
                    m=l-1
                    while i < m:
                        cond=section[i]
                        if type(cond) is StringType:
                            n=cond
                            try:
                                cond=md[cond]
                                cache[n]=cond
                            except KeyError, v:
                                v=str(v)
                                if n != v: raise KeyError, v, sys.exc_traceback
                                cond=None
                        else: cond=cond(md)
                        if cond:
                            section=section[i+1]
                            if section: section=render_blocks(section,md)
                            else: section=''
                            m=0
                            break
                        i=i+2
                    if m:
                        if i==m: section=render_blocks(section[i],md)
                        else: section=''

                finally: md._pop()

        elif type(section) is not StringType and type(section) is not UnicodeType:
            section=section(md)

        if section: rendered.append(section)

    l=len(rendered)
    if l==0: return ''
    elif l==1: return rendered[0]
    return join_unicode(rendered)

def join_unicode(rendered):
    """join a list of plain strings into a single plain string,
    a list of unicode strings into a single unicode strings,
    or a list containing a mix into a single unicode string with
    the plain strings converted from latin-1
    """
    try:
        return ''.join(rendered)
    except UnicodeError:
        # A mix of unicode string and non-ascii plain strings.
        # Fix up the list, treating normal strings as latin-1
        rendered = list(rendered)
        for i in range(len(rendered)):
            if type(rendered[i]) is StringType:
                rendered[i] = unicode(rendered[i],'latin-1')
        return u''.join(rendered)
