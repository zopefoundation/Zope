#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software, contact:
#
#   Digital Creations, L.C.
#   910 Princess Ann Street
#   Fredericksburge, Virginia  22401
#
#   info@digicool.com
#
#   (540) 371-6909
#
############################################################################## 
__doc__='''Python implementations of document template some features


$Id: pDocumentTemplate.py,v 1.12 1998/05/13 20:36:02 jim Exp $'''
__version__='$Revision: 1.12 $'[11:-2]

import regex, string, sys
from string import join

StringType=type('')
TupleType=type(())
isFunctionType={}
for name in ['BuiltinFunctionType', 'BuiltinMethodType', 'ClassType',
	     'FunctionType', 'LambdaType', 'MethodType']:
    try: isFunctionType[getattr(types,name)]=1
    except: pass

try: # Add function and method types from Extension Classes
    import ExtensionClass
    isFunctionType[ExtensionClass.PythonMethodType]=1
    isFunctionType[ExtensionClass.ExtensionMethodType]=1
except: pass

isFunctionType=isFunctionType.has_key

class InstanceDict:

    validate=None

    def __init__(self,o,namespace,validate=None):
	self.self=o
	self.cache={}
	self.namespace=namespace
	if validate is None: self.validate=namespace.validate
	else: self.validate=validate

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
		r=str(inst)
	else:
	    try: r=getattr(inst,key)
	    except AttributeError: raise KeyError, key

	v=self.validate
	if v is not None: v(inst,inst,key,r,self.namespace)

	self.cache[key]=r
	return r

class MultiMapping:

    def __init__(self): self.dicts=[]

    def __getitem__(self, key):
        for d in self.dicts:
            try: return d[key]
            except KeyError, AttributeError: pass
        raise KeyError, key

    def push(self,d): self.dicts.insert(0,d)

    def pop(self,n=1): del self.dicts[:n]

    def keys(self):
        kz = []
        for d in self.dicts:
            kz = kz + d.keys()
        return kz

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

        v=self.dicts[key]
	if call:
	    try: isDocTemp=v.isDocTemp
	    except: isDocTemp=None
	    if isDocTemp: v=v(None,self)
	    else:
		try: v=v()
		except (AttributeError,TypeError): pass
        return v

    getitem=__getitem__

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
		section=str(section)
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

	elif type(section) is not StringType:
	    section=section(md)

	if section: rendered.append(section)

    l=len(rendered)
    if l==0: return ''
    elif l==1: return rendered[0]
    return join(rendered, '')
    return rendered


############################################################################## 
#
# $Log: pDocumentTemplate.py,v $
# Revision 1.12  1998/05/13 20:36:02  jim
# Slightly simpler solution to exception dilema.
#
# Revision 1.11  1998/05/13 20:28:02  jim
# Fixed bug in handling conditional tags.
#
# Revision 1.10  1998/04/08 17:47:48  jim
# Fixed bug in calling validation method.
#
# Revision 1.9  1998/04/02 19:06:39  jim
# *** empty log message ***
#
# Revision 1.8  1998/04/02 17:37:40  jim
# Major redesign of block rendering. The code inside a block tag is
# compiled as a template but only the templates blocks are saved, and
# later rendered directly with render_blocks.
#
# Added with tag.
#
# Also, for the HTML syntax, we now allow spaces after # and after end
# or '/'.  So, the tags::
#
#   <!--#
#     with spam
#     -->
#
# and::
#
#   <!--#
#     end with
#     -->
#
# are valid.
#
# Revision 1.7  1997/11/19 15:42:48  jim
# added _ prefix to push and pop methods to make them private
#
# Revision 1.6  1997/11/11 18:39:29  jim
# Added a little compatibility with cDocumentTemplate.
#
# Revision 1.5  1997/10/29 16:59:28  jim
# Changed name of get to getitem.
#
# Revision 1.4  1997/10/28 21:52:06  jim
# Changed to not call document templates if not calling other functions.
#
# Revision 1.3  1997/10/27 17:42:07  jim
# Removed old validation machinery.
#
# Made some changes to synchonize with cDocumentTemplate.
#
# Added a get method on TemplateDicts to do lookup without
# (non-DocumentTemplate) method calls.
#
# Revision 1.2  1997/09/02 19:02:51  jim
# *** empty log message ***
#
# Revision 1.1  1997/08/27 18:55:47  jim
# initial
#
# Revision 1.1  1997/08/13 13:24:58  jim
# *** empty log message ***
#
#
