'''$Id: DT_Util.py,v 1.6 1997/10/28 21:50:01 jim Exp $''' 

############################################################################
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
# If you have questions regarding this software,
# contact:
#
#   Jim Fulton, jim@digicool.com
#
#   (540) 371-6909
#
############################################################################ 
__version__='$Revision: 1.6 $'[11:-2]

import sys, regex, string, types, math, os
from string import rfind, strip, joinfields, atoi,lower,upper,capitalize
from types import *
from regsub import gsub, sub, split
from __builtin__ import *
import VSEval

ParseError='Document Template Parse Error'

def int_param(params,md,name,default=0):
    try: v=params[name]
    except: v=default
    if v:
	try: v=atoi(v)
	except:
	    v=md[v]
	    if type(v)==types.StringType:
		v=atoi(v)
    return v

class func_code:
    def __init__(self,varnames=('self','REQUEST')):
	self.co_varnames=varnames
	self.co_argcount=len(varnames)

def _tm(m, tag):
    return m + tag and (' in %s' % tag)

def careful_getattr(inst, name, md):
    if name[:1]!='_':
	validate=md.validate

	if validate is None: return getattr(inst, name)

	if hasattr(inst,'acquire'): return inst.acquire(name, validate, md)

	v=getattr(inst, name)
	if validate(inst,inst,name,v,md): return v

    raise AttributeError, name

def careful_getitem(mapping, key, md):
    v=mapping[key]
    validate=md.validate
    if validate is None or validate(mapping,mapping,key,v,md): return v
    raise KeyError, key

def name_param(params,tag='',expr=0):
    used=params.has_key
    if used(''):
	if used('name'):
	    raise ParseError, _tm('Two names were given', tag)
	if expr:
	    if used('expr'): raise ParseError, _tm('name and expr given', tag)
	    return params[''],None
	return params['']
    elif used('name'):
	if expr:
	    if used('expr'): raise ParseError, _tm('name and expr given', tag)
	    return params['name'],None
	return params['name']
    elif expr and used('expr'):
	name=params['expr']
	expr=VSEval.Eval(name,
			 __mul__=VSEval.careful_mul,
			 __getattr__=careful_getattr,
			 __getitem__=careful_getitem,
			 )
	return name, expr
	
    raise ParseError, ('No name given', tag)

def parse_params(text,
		 result=None,
		 tag='',
		 unparmre=regex.compile(
		     '\([\0- ]*\([^\0- =\"]+\)\)'),
		 parmre=regex.compile(
		     '\([\0- ]*\([^\0- =\"]+\)=\([^\0- =\"]+\)\)'),
		 qparmre=regex.compile(
		     '\([\0- ]*\([^\0- =\"]+\)="\([^"]*\)\"\)'),
		 **parms):

    """Parse tag parameters

    The format of tag parameters consists of 1 or more parameter
    specifications separated by whitespace.  Each specification
    consists of an unnamed and unquoted value, a valueless name, or a
    name-value pair.  A name-value pair consists of a name and a
    quoted or unquoted value separated by an '='.

    The input parameter, text, gives the text to be parsed.  The
    keyword parameters give valid parameter names and default values.

    If a specification is not a name-value pair and it is not the
    first specification that is not a name-value pair and it is a
    valid parameter name, then it is treated as a name-value pair with
    a value as given in the keyword argument.  Otherwise, if it is not
    a name-value pair, it is treated as an unnamed value.

    The data are parsed into a dictionary mapping names to values.
    Unnamed values are mapped from the name '""'.  Only one value may
    be given for a name and there may be only one unnamed value. """

    result=result or {}

    if parmre.match(text) >= 0:
	name=lower(parmre.group(2))
	value=parmre.group(3)
	l=len(parmre.group(1))
    elif qparmre.match(text) >= 0:
	name=lower(qparmre.group(2))
	value=qparmre.group(3)
	l=len(qparmre.group(1))
    elif unparmre.match(text) >= 0:
	name=unparmre.group(2)
	l=len(unparmre.group(1))
	if result.has_key(''):
	    if parms.has_key(name): result[name]=parms[name]
	    else: raise ParseError, (
		'Invalid parameter name, "%s"' % name, tag)
	else:
	    result['']=name
	return apply(parse_params,(text[l:],result),parms)
    else:
	if not text or not strip(text): return result
	raise InvalidParameter, text
    
    if not parms.has_key(name):
	raise ParseError, (
	    'Invalid parameter name, "%s"' % name, tag)

    result[name]=value

    text=strip(text[l:])
    if text: return apply(parse_params,(text,result),parms)
    else: return result

try: from cDocumentTemplate import InstanceDict, TemplateDict, render_blocks
except: from pDocumentTemplate import InstanceDict, TemplateDict, render_blocks

############################################################################
# $Log: DT_Util.py,v $
# Revision 1.6  1997/10/28 21:50:01  jim
# Updated validation rules to use DT validation method.
#
# Revision 1.5  1997/10/27 17:38:41  jim
# Added some new experimental validation machinery.
# This is, still a work in progress.
#
# Fixed some error generation bugs.
#
# Revision 1.4  1997/09/25 18:56:39  jim
# fixed problem in reporting errors
#
# Revision 1.3  1997/09/22 14:42:50  jim
# added expr
#
# Revision 1.2  1997/09/02 20:35:09  jim
# Various fixes to parsing code.
#
# Revision 1.1  1997/08/27 18:55:43  jim
# initial
#
