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
'''$Id: DT_Util.py,v 1.78 2001/06/18 18:13:09 chrism Exp $''' 
__version__='$Revision: 1.78 $'[11:-2]

import re, os
from html_quote import html_quote # for import by other modules, dont remove!
from RestrictedPython.Guards import safe_builtins
from RestrictedPython.Utilities import utility_builtins
from RestrictedPython.Eval import RestrictionCapableEval

LIMITED_BUILTINS = 1

str=__builtins__['str'] # Waaaaa, waaaaaaaa needed for pickling waaaaa

ParseError='Document Template Parse Error'
ValidationError='Unauthorized'

def int_param(params,md,name,default=0, st=type('')):
    try: v=params[name]
    except: v=default
    if v:
        try: v=int(v)
        except:
            v=md[v]
            if type(v) is st: v=int(v)
    return v or 0

try:
    import ExtensionClass
    from cDocumentTemplate import InstanceDict, TemplateDict, render_blocks
except: from pDocumentTemplate import InstanceDict, TemplateDict, render_blocks


functype = type(int_param)
class NotBindable:
    # Used to prevent TemplateDict from trying to bind to functions.
    def __init__(self, f):
        self.__call__ = f

d = TemplateDict.__dict__
for name, f in safe_builtins.items() + utility_builtins.items():
    if type(f) is functype:
        d[name] = NotBindable(f)
    else:
        d[name] = f

if LIMITED_BUILTINS:
    # Replace certain builtins with limited versions.
    from RestrictedPython.Limits import limited_builtins
    for name, f in limited_builtins.items():
        if type(f) is functype:
            d[name] = NotBindable(f)
        else:
            d[name] = f

# The functions below are meant to bind to the TemplateDict.

_marker = []  # Create a new marker object.

def careful_getattr(md, inst, name, default=_marker):
    read_guard = md.read_guard
    if read_guard is not None:
        inst = read_guard(inst)
    if default is _marker:
        return getattr(inst, name)
    else:
        return getattr(inst, name, default)

def careful_hasattr(md, inst, name):
    read_guard = md.read_guard
    if read_guard is not None:
        inst = read_guard(inst)
    return hasattr(inst, name)

d['getattr']=careful_getattr
d['hasattr']=careful_hasattr

def namespace(self, **kw):
    """Create a tuple consisting of a single instance whose attributes are
    provided as keyword arguments."""
    if getattr(self, '__class__', None) != TemplateDict:
        raise TypeError,'''A call was made to DT_Util.namespace() with an
        incorrect "self" argument.  It could be caused by a product which
        is not yet compatible with this version of Zope.  The traceback
        information may contain more details.)'''
    return apply(self, (), kw)

d['namespace']=namespace

def render(self, v):
    "Render an object in the way done by the 'name' attribute"
    if hasattr(v, '__render_with_namespace__'):
        v = v.__render_with_namespace__(self)
    else:
        vbase = getattr(v, 'aq_base', v)
        if callable(vbase):
            try:
                if getattr(vbase, 'isDocTemp', 0):
                    v = v(None, self)
                else:
                    v = v()
            except AttributeError, n:
                if n != '__call__':
                    raise
    return v

d['render']=render


class Eval(RestrictionCapableEval):

    def eval(self, md):
        guard = getattr(md, 'read_guard', None)
        if guard is not None:
            self.prepRestrictedCode()
            code = self.rcode
            d = {'_': md, '_vars': md,
                 '_read_': guard, '__builtins__': None}
        else:
            self.prepUnrestrictedCode()
            code = self.ucode
            d = {'_': md, '_vars': md}
        d.update(self.globals)
        has_key = d.has_key
        for name in self.used:
            __traceback_info__ = name
            try:
                if not has_key(name):
                    d[name] = md.getitem(name, 0)
            except KeyError:
                # Swallow KeyErrors since the expression
                # might not actually need the name.  If it
                # does need the name, a NameError will occur.
                pass
        return eval(code, d)

    def __call__(self, **kw):
        # Never used?
        md = TemplateDict()
        md._push(kw)
        return self.eval(md)

simple_name = re.compile('[a-z][a-z0-9_]*', re.I).match

class Add_with_prefix:
    def __init__(self, map, defprefix, prefix):
        self.map = map
        self.defprefix = defprefix
        self.prefix = prefix
    def __setitem__(self, name, value):
        map = self.map
        map[name] = value
        dp = self.defprefix
        if name.startswith(dp + '-'):
            map[self.prefix + name[len(dp):].replace('-', '_')] = value
        else:
            map['%s_%s' % (self.prefix, name)] = value

def add_with_prefix(map, defprefix, prefix):
    if not prefix: return map
    return Add_with_prefix(map, defprefix, prefix)

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
                try: expr=Eval(v)
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
        expr=Eval(name)
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
                 unparmre=re.compile('([\000- ]*([^\000- ="]+))'),
                 qunparmre=re.compile('([\000- ]*("[^"]*"))'),
                 parmre=re.compile('([\000- ]*([^\000- ="]+)=([^\000- ="]+))'),
                 qparmre=re.compile('([\000- ]*([^\000- ="]+)="([^"]*)")'),
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

    # HACK - we precalculate all matches. Maybe we don't need them 
    # all. This should be fixed for performance issues

    mo_p = parmre.match(text)
    mo_q = qparmre.match(text)
    mo_unp = unparmre.match(text)
    mo_unq = qunparmre.match(text)

    if mo_p:
        name=mo_p.group(2).lower()
        value=mo_p.group(3)
        l=len(mo_p.group(1))
    elif mo_q:
        name=mo_q.group(2).lower()
        value=mo_q.group(3)
        l=len(mo_q.group(1))
    elif mo_unp:
        name=mo_unp.group(2)
        l=len(mo_unp.group(1))
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
    elif mo_unq:
        name=mo_unq.group(2)
        l=len(mo_unq.group(1))
        if result: raise ParseError, (
            'Invalid attribute name, "%s"' % name, tag)
        else: result['']=name
        return apply(parse_params,(text[l:],result),parms)
    else:
        if not text or not text.strip(): return result
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

    text=text[l:].strip()
    if text: return apply(parse_params,(text,result),parms)
    else: return result
