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
'''$Id: DT_Util.py,v 1.65 2000/05/26 22:06:08 shane Exp $''' 
__version__='$Revision: 1.65 $'[11:-2]

import regex, string, math, os
from string import strip, join, atoi, lower, split, find
import VSEval

str=__builtins__['str'] # Waaaaa, waaaaaaaa needed for pickling waaaaa

ParseError='Document Template Parse Error'
ValidationError='Unauthorized'


def html_quote(v, name='(Unknown name)', md={},
               character_entities=(
                       (('&'), '&amp;'),
                       (("<"), '&lt;' ),
                       ((">"), '&gt;' ),
                       (('"'), '&quot;'))): #"
        text=str(v)
        for re,name in character_entities:
            if find(text, re) >= 0: text=join(split(text,re),name)
        return text

def int_param(params,md,name,default=0, st=type('')):
    try: v=params[name]
    except: v=default
    if v:
        try: v=atoi(v)
        except:
            v=md[v]
            if type(v) is st: v=atoi(v)
    return v or 0

_marker=[]

def careful_getattr(md, inst, name, default=_marker):
    
    if name[:1]!='_':

        # Try to get the attribute normally so that we don't
        # accidentally acquire when we shouldn't.
        try: v=getattr(inst, name)
        except:
            if default is not _marker:
                return default
            raise

        validate=md.validate

        if validate is None: return v

        if hasattr(inst,'aq_acquire'):
            return inst.aq_acquire(name, validate, md)

        if validate(inst,inst,name,v,md): return v

    raise ValidationError, name

def careful_hasattr(md, inst, name):
    v=getattr(inst, name, _marker)
    if v is not _marker:
        try: 
            if name[:1]!='_':
                validate=md.validate                
                if validate is None: return 1
    
                if hasattr(inst,'aq_acquire'):
                    inst.aq_acquire(name, validate, md)
                    return 1
    
                if validate(inst,inst,name,v,md): return 1
        except: pass
    return 0

def careful_getitem(md, mapping, key):
    v=mapping[key]

    if type(v) is type(''): return v # Short-circuit common case

    validate=md.validate
    if validate is None or validate(mapping,mapping,None,v,md): return v
    raise ValidationError, key

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
            if not validate(seq,seq,None,e,md):
                raise ValidationError, 'unauthorized access to slice member'

    return v

def careful_range(md, iFirst, *args):
    # limited range function from Martijn Pieters
    RANGELIMIT = 1000
    if not len(args):
        iStart, iEnd, iStep = 0, iFirst, 1
    elif len(args) == 1:
        iStart, iEnd, iStep = iFirst, args[0], 1
    elif len(args) == 2:
        iStart, iEnd, iStep = iFirst, args[0], args[1]
    else:
        raise AttributeError, 'range() requires 1-3 int arguments'
    if iStep == 0: raise ValueError, 'zero step for range()'
    iLen = int((iEnd - iStart) / iStep)
    if iLen < 0: iLen = 0
    if iLen >= RANGELIMIT: raise ValueError, 'range() too large'
    return range(iStart, iEnd, iStep)

import string, math, whrandom

try:
    import ExtensionClass
    from cDocumentTemplate import InstanceDict, TemplateDict, render_blocks
    from cDocumentTemplate import cDocument
except: from pDocumentTemplate import InstanceDict, TemplateDict, render_blocks


d=TemplateDict.__dict__
for name in ('None', 'abs', 'chr', 'divmod', 'float', 'hash', 'hex', 'int',
             'len', 'max', 'min', 'oct', 'ord', 'round', 'str'):
    d[name]=__builtins__[name]
d['string']=string
d['math']=math
d['whrandom']=whrandom

def careful_pow(self, x, y, z):
    if not z: raise ValueError, 'pow(x, y, z) with z==0'
    return pow(x,y,z)

d['pow']=careful_pow

try:
    import random
    d['random']=random
except: pass

try:
    import DateTime
    d['DateTime']=DateTime.DateTime
except: pass

def test(self, *args):
    l=len(args)
    for i in range(1, l, 2):
        if args[i-1]: return args[i]

    if l%2: return args[-1]

d['test']=test

def obsolete_attr(self, inst, name, md):
    return careful_getattr(md, inst, name)

d['attr']=obsolete_attr
d['getattr']=careful_getattr
d['hasattr']=careful_hasattr
d['range']=careful_range

class namespace_:
    __allow_access_to_unprotected_subobjects__=1


def namespace(self, **kw):
    """Create a tuple consisting of a single instance whos attributes are
    provided as keyword arguments."""
    try: return self(kw) # Try to use the cDocumentTemplate implementation.
    except AttributeError:
        r=namespace_()
        d=r.__dict__
        for k, v in kw.items(): d[k]=v
        return r,

d['namespace']=namespace

def render(self, v, simple={
    type(''): 1, type(0): 1, type(0.0): 1,
    type([]): 1, type(()): 1,
    }.has_key):
    "Render an object in the way done be the 'name' attribute"

    if not simple(type(v)):
        if hasattr(v,'isDocTemp') and v.isDocTemp:
            v=v(None, self)
        else:
            try: v=v()
            except (AttributeError,TypeError): pass
    return v

d['render']=render

def reorder(self, s, with=None, without=()):
    if with is None: with=s
    d={}
    tt=type(())
    for i in s:
        if type(i) is tt and len(i)==2: k, v = i
        else:                           k= v = i
        d[k]=v
    r=[]
    a=r.append
    h=d.has_key

    for i in without:
        if type(i) is tt and len(i)==2: k, v = i
        else:                           k= v = i
        if h(k): del d[k]
        
    for i in with:
        if type(i) is tt and len(i)==2: k, v = i
        else:                           k= v = i
        if h(k):
            a((k,d[k]))
            del d[k]

    return r

d['reorder']=reorder


expr_globals={
    '__builtins__':{},
    '__guarded_mul__':      VSEval.careful_mul,
    '__guarded_getattr__':  careful_getattr,
    '__guarded_getitem__':  careful_getitem,
    '__guarded_getslice__': careful_getslice,
    }

class Eval(VSEval.Eval):
    
    def eval(self, mapping):
        d={'_vars': mapping, '_': mapping}
        code=self.code
        globals=self.globals
        for name in self.used:
            __traceback_info__ = name
            try: d[name]=mapping.getitem(name,0)
            except KeyError:
                if name=='_getattr':
                    d['__builtins__']=globals
                    exec compiled_getattr in d

        return eval(code,globals,d)


def name_param(params,tag='',expr=0, attr='name', default_unnamed=1):
    used=params.has_key
    __traceback_info__=params, tag, expr, attr

    #if expr and used('expr') and used('') and not used(params['']):
    #   # Fix up something like: <!--#in expr="whatever" mapping-->
    #   params[params['']]=default_unnamed
    #   del params['']
        
    if used(''):
        v=params['']

        if v[:1]=='"' and v[-1:]=='"' and len(v) > 1: # expr shorthand
            if used(attr):
                raise ParseError, ('%s and expr given' % attr, tag)
            if expr:
                if used('expr'):
                    raise ParseError, ('two exprs given', tag)
                v=v[1:-1]
                try: expr=Eval(v, expr_globals)
                except SyntaxError, v:
                    raise ParseError, (
                        '<strong>Expression (Python) Syntax error</strong>:'
                        '\n<pre>\n%s\n</pre>\n' % v[0],
                        tag)
                return v, expr
            else: raise ParseError, (
                'The "..." shorthand for expr was used in a tag '
                'that doesn\'t support expr attributes.',
                tag)

        else: # name shorthand            
            if used(attr):
                raise ParseError, ('Two %s values were given' % attr, tag)
            if expr:
                if used('expr'):
                    # raise 'Waaaaaa', 'waaa'
                    raise ParseError, ('%s and expr given' % attr, tag)
                return params[''],None
            return params['']

    elif used(attr):
        if expr:
            if used('expr'):
                raise ParseError, ('%s and expr given' % attr, tag)
            return params[attr],None
        return params[attr]
    elif expr and used('expr'):
        name=params['expr']
        expr=Eval(name, expr_globals)
        return name, expr
        
    raise ParseError, ('No %s given' % attr, tag)

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

  In addition, a special additional name, '_', is available.  The '_'
  variable provides access to the document template namespace as a
  mapping object.  This variable can be useful for accessing objects
  in a document template namespace that have names that are not legal
  Python variable names::
  
     <!--#var expr="_['sequence-number']*5"-->
  
  This variable also has attributes that provide access to standard
  utility objects.  These attributes include:
  
  - The objects: 'None', 'abs', 'chr', 'divmod', 'float', 'hash',
       'hex', 'int', 'len', 'max', 'min', 'oct', 'ord', 'pow',
       'round', and 'str' from the standard Python builtin module.

  - Special security-aware versions of 'getattr' and 'hasattr',
  
  - The Python 'string', 'math', and 'whrandom' modules, and
  
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

"""

ListType=type([])
def parse_params(text,
                 result=None,
                 tag='',
                 unparmre=regex.compile(
                     '\([\0- ]*\([^\0- =\"]+\)\)'),
                 qunparmre=regex.compile(
                     '\([\0- ]*\("[^"]*"\)\)'),
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
    first specification and it is a
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
        if result:
            if parms.has_key(name):
                if parms[name] is None: raise ParseError, (
                    'Attribute %s requires a value' % name, tag)
                    
                result[name]=parms[name]
            else: raise ParseError, (
                'Invalid attribute name, "%s"' % name, tag)
        else:
            result['']=name
        return apply(parse_params,(text[l:],result),parms)
    elif qunparmre.match(text) >= 0:
        name=qunparmre.group(2)
        l=len(qunparmre.group(1))
        if result: raise ParseError, (
            'Invalid attribute name, "%s"' % name, tag)
        else: result['']=name
        return apply(parse_params,(text[l:],result),parms)
    else:
        if not text or not strip(text): return result
        raise ParseError, ('invalid parameter: "%s"' % text, tag)
    
    if not parms.has_key(name):
        raise ParseError, (
            'Invalid attribute name, "%s"' % name, tag)

    if result.has_key(name):
        p=parms[name]
        if type(p) is not ListType or p:
            raise ParseError, (
                'Duplicate values for attribute "%s"' % name, tag)
            
    result[name]=value

    text=strip(text[l:])
    if text: return apply(parse_params,(text,result),parms)
    else: return result
