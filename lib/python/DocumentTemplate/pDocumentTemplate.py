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


$Id: pDocumentTemplate.py,v 1.1 1997/08/27 18:55:47 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

import regex, string

StringType=type('')
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

    def __init__(self,o,namespace):
	self.self=o
	self.cache={}
	self.namespace=namespace

    def has_key(self,key):
	return hasattr(self.self,key)

    def keys(self):
	return self.self.__dict__.keys()

    def __repr__(self): return 'InstanceDict(%s)' % str(self.self)

    def __getitem__(self,key):

	# sys.stderr.write("Inst %s\n" % str((key,self)))
	try:
	    r=self.cache[key]
	except:
	    if key[:1]=='_':
		if key != '__str__':
		    raise KeyError, key # Don't divuldge private data
		r=str(self.self)
	    else:
		try: r=getattr(self.self,key)
		except AttributeError: raise KeyError, key
		if isFunctionType(type(r)):
		    r=r()
		try: isDocTemp=r.isDocTemp
		except: isDocTemp=0
		if isDocTemp:
		    # There's no point in passing self, since we're
		    # already in the name space
		    #r=r(self.self,self.namespace)
		    r=r(None,self.namespace)
		    # We won't cache results of rendering 
		else:
		    self.cache[key]=r
	# sys.stderr.write("RI %s\n" % str((key,r)))
	return r

class MultiMapping:

    def __init__(self): self.dicts=[]

    def __getitem__(self, key):
        for d in self.dicts:
            try: return d[key]
            except KeyError, AttributeError: pass
        raise KeyError, key

    def push(self,d): self.dicts.insert(0,d)

    def pop(self,n): del self.dicts[:n]

    def keys(self):
        kz = []
        for d in self.dicts:
            kz = kz + d.keys()
        return kz

class TemplateDict:

    def __init__(self):
	m=self.dicts=MultiMapping()
	self.pop=m.pop
	self.push=m.push
	try: self.keys=m.keys
	except: pass

	# if names is None: self._names = {}
	# else: self._names = names
	# self._validator = validator
	# self._do_validation=names or validator

    def setValidation(self,names,validator):
	r=self._names, self._validator
	if names is None: self._names = {}
	else: self._names = names
	self._validator = validator
	self._do_validation=names or validator
	return r

    def __getitem__(self,key):
	# sys.stderr.write("MD %s\n" % str((key,self)))

	# do_validation=self._do_validation
        v=self.dicts[key]
        # validate before calling?
        # if do_validation: self.validate(key, v)
        # if isFunctionType(type(v)):
	try: isDocTemp=v.isDocTemp
	except: isDocTemp=None
	if isDocTemp: v=v(None,self)
	else:
	    try: v=v()
	    except (AttributeError,TypeError): pass
        return v

    _namepat = regex.compile('[^a-z0-9_]', regex.casefold)
    def validate(self, key, value=None):
	"Check key/value for access - raise KeyError if invalid access."

	# names containing other than normal identifier chars are okay
	# names in the programmer-provided list of names are okay
	# key/value pairs the validator function approves are okay
	if (self._namepat.search(key) != -1 or
	    self._names.has_key(key) or
	    (type(self._validator) == FunctionType and
	     self._validator(key, value))): return

	# everything else is verboten...
	raise KeyError, key

def render_blocks(self, md):
    rendered = []
    for section in self.blocks:
	if type(section) is not StringType:
	    section=section(md)
	if section: rendered.append(section)
    rendered=string.join(rendered, '')
    return rendered


############################################################################## 
#
# $Log: pDocumentTemplate.py,v $
# Revision 1.1  1997/08/27 18:55:47  jim
# initial
#
# Revision 1.1  1997/08/13 13:24:58  jim
# *** empty log message ***
#
#
