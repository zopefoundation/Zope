'''$Id: DT_Util.py,v 1.29 1998/03/26 16:09:11 jim Exp $''' 

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
__version__='$Revision: 1.29 $'[11:-2]

import sys, regex, string, types, math, os
from string import rfind, strip, joinfields, atoi,lower,upper,capitalize
from types import *
from regsub import gsub, sub, split
from __builtin__ import *
import VSEval

ParseError='Document Template Parse Error'
ValidationError='ValidationError'

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

def _tm(m, tag):
    return m + tag and (' in %s' % tag)

def careful_getattr(md, inst, name):
    if name[:1]!='_':
	validate=md.validate

	if validate is None: return getattr(inst, name)

	if hasattr(inst,'aq_acquire'):
	    return inst.aq_acquire(name, validate, md)

	v=getattr(inst, name)
	if validate(inst,inst,name,v,md): return v

    raise ValidationError, name

def careful_getitem(md, mapping, key):
    v=mapping[key]

    if type(v) is type(''): return v # Short-circuit common case

    validate=md.validate
    if validate is None or validate(mapping,mapping,key,v,md): return v
    raise Validation, key

def careful_getslice(md, seq, *indexes):
    v=len(indexes)
    if v==2:
	v=seq[indexes[0]:indexes[1]]
    elif v==1:
	v=seq[indexes[0]:]
    else: v=seq[:]

    if type(seq) is type(''): return v # Short-circuit common case

    validate=md.validate
    if validate is not None:
	for e in v:
	    if not validate(seq,seq,'',e,md):
		raise ValidationError, 'unauthorized access to slice member'

    return v

import string, math, rand, whrandom

class expr_globals: pass
expr_globals=expr_globals()

d=expr_globals.__dict__
for name in ('None', 'abs', 'chr', 'divmod', 'float', 'hash', 'hex', 'int',
	     'len', 'max', 'min', 'oct', 'ord', 'pow', 'round', 'str'):
    d[name]=__builtins__[name]
d['string']=string
d['math']=math
d['rand']=rand
d['whrandom']=whrandom

def test(*args):
    l=len(args)
    for i in range(1, l, 2):
	if args[i-1]: return args[i]

    if l%2: return args[-1]

d['test']=test

def _attr(inst, name, md={}):
    return careful_getattr(md, inst, name)

d['attr']=_attr

class namespace_: pass

def namespace(**kw):
    r=namespace_()
    d=r.__dict__
    for k, v in kw.items(): d[k]=v
    return r,

d['namespace']=namespace

expr_globals={
    '__builtins__':{},
    '_': expr_globals,
    '__guarded_mul__':      VSEval.careful_mul,
    '__guarded_getattr__':  careful_getattr,
    '__guarded_getitem__':  careful_getitem,
    '__guarded_getslice__': careful_getslice,
    }

def name_param(params,tag='',expr=0, attr='name', default_unnamed=1):
    used=params.has_key
    __traceback_info__=params, tag, expr, attr

    if expr and used('expr') and used('') and not used(params['']):
	# Fix up something like: <!--#in expr="whatever" mapping-->
	params[params['']]=default_unnamed
	del params['']
	
    if used(''):
	if used(attr):
	    raise ParseError, _tm('Two %s values were given', (attr,tag))
	if expr:
	    if used('expr'):
		raise ParseError, _tm('%s and expr given', (attr,tag))
	    return params[''],None
	return params['']
    elif used(attr):
	if expr:
	    if used('expr'):
		raise ParseError, _tm('%s and expr given', (attr,tag))
	    return params[attr],None
	return params[attr]
    elif expr and used('expr'):
	name=params['expr']
	expr=VSEval.Eval(name, expr_globals)
	return name, expr
	
    raise ParseError, ('No %s given', (attr,tag))

Expr_doc="""


Python expression support

  Several document template tags, including 'var', 'in', 'if', 'else',
  and 'elif' provide support for using Python expressions via an
  'expr' tag attribute.

  Expressions may be used where a simple variable value is
  inadequate.  For example, an expression might be used to test
  whether a variable is greater than some amount::

     <!--#if expr="age > 18"-->

  or to transform some basic data::

     <!--#var expr="phone[:3]"-->

  Objects available in the document templates namespace may be used.
  Subobjects of these objects may be used as well, although subobject
  access is restricted by the optional validation method.

  In addition, certain special additional names are available:

  '_vars' -- Provides access to the document template namespace as a
     mapping object.  This variable can be useful for accessing
     objects in a document template namespace that have names that are
     not legal Python variable names::

        <!--#var expr="_vars['sequence-number']*5"-->

  '_' -- Provides access to a Python module containing standard
     utility objects.  These utility objects include:

     - The objects: 'None', 'abs', 'chr', 'divmod', 'float', 'hash',
          'hex', 'int', 'len', 'max', 'min', 'oct', 'ord', 'pow',
	  'round', and 'str' from the standard Python builtin module.

     - The Python 'string' module, and

     - The Python 'math' module. 

     - A special function, 'test', that supports if-then expressions.
       The 'test' function accepts any number of arguments.  If the
       first argument is true, then the second argument is returned,
       otherwise if the third argument is true, then the fourth
       argument is returned, and so on.  If there is an odd number of
       arguments, then the last argument is returned in the case that
       none of the tested arguments is true, otherwise None is
       returned. 

     For example, to convert a value to lower case::

       <!--#var expr="_.string.lower(title)"-->

""" #"

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
	    if parms.has_key(name):
		if parms[name] is None: raise ParseError, (
		    'Attribute %s requires a value' % name, tag)
		    
		result[name]=parms[name]
	    else: raise ParseError, (
		'Invalid attribute name, "%s"' % name, tag)
	else:
	    result['']=name
	return apply(parse_params,(text[l:],result),parms)
    else:
	if not text or not strip(text): return result
	raise ParseError, ('invalid parameter: "%s"' % text, tag)
    
    if not parms.has_key(name):
	raise ParseError, (
	    'Invalid attribute name, "%s"' % name, tag)

    result[name]=value

    text=strip(text[l:])
    if text: return apply(parse_params,(text,result),parms)
    else: return result

try: from cDocumentTemplate import InstanceDict, TemplateDict, render_blocks
except: from pDocumentTemplate import InstanceDict, TemplateDict, render_blocks

############################################################################
# $Log: DT_Util.py,v $
# Revision 1.29  1998/03/26 16:09:11  jim
# *** empty log message ***
#
# Revision 1.28  1998/03/26 16:05:46  jim
# *** empty log message ***
#
# Revision 1.27  1998/03/26 14:59:29  jim
# Fixed bug in exporting rand modules.
#
# Revision 1.26  1998/03/12 20:52:11  jim
# Added namespace function to _ module for exprs.
#
# Revision 1.25  1998/03/10 15:04:58  jim
# Added better handling of case like:
#
#   <!--#in expr="whatever" mapping-->
#
# Revision 1.24  1998/03/06 23:22:36  jim
# Added "builtin" 'attr' function: attr(inst,name,_vars)
#
# Revision 1.23  1998/03/04 18:18:40  jim
# Extended the parse_name utility to handle other name-like tags.
#
# Revision 1.22  1998/01/13 19:35:55  jim
# Added rand and whrand.
#
# Revision 1.21  1998/01/12 16:48:40  jim
# Fixed error reporting bug.
#
# Revision 1.20  1997/11/27 00:10:50  jim
# Hacked my way out of using new module.
#
# Revision 1.19  1997/11/25 15:26:34  jim
# Added test to expr documentation.
#
# Revision 1.18  1997/11/25 15:20:30  jim
# Expanded test function to allow any number of arguments.
#
# Revision 1.17  1997/11/19 15:42:47  jim
# added _ prefix to push and pop methods to make them private
#
# Revision 1.16  1997/11/19 15:33:32  jim
# Updated parse_params so that you can define an attribute that, if
# used, must have a value.  This is done by specifying None as a default
# value.
#
# Revision 1.15  1997/11/12 19:44:13  jim
# Took out setting __roles__ for pop and push.
#
# Revision 1.14  1997/11/11 18:13:48  jim
# updated expr machinery to use parse-tree manipulation
#
# Revision 1.13  1997/10/29 22:06:06  jim
# Moved func_code from DT_Util to DT_String.
#
# Took stab at expression documentation.
#
# Revision 1.12  1997/10/29 21:30:24  jim
# Added "builtin" objects.
#
# Revision 1.11  1997/10/29 21:03:26  jim
# *** empty log message ***
#
# Revision 1.10  1997/10/29 20:43:24  jim
# *** empty log message ***
#
# Revision 1.9  1997/10/29 16:58:30  jim
# Modified to explicitly make push and pop private.
#
# Revision 1.8  1997/10/29 16:17:45  jim
# Added careful_getslice.
#
# Revision 1.7  1997/10/28 22:10:46  jim
# changed 'acquire' to 'aq_acquire'.
#
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
