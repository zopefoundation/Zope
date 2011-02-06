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
"""DTML Utilities

$Id$"""

import re

# for import by other modules, dont remove!
from DocumentTemplate.html_quote import html_quote, ustr

from DocumentTemplate.cDocumentTemplate import InstanceDict, TemplateDict
from DocumentTemplate.cDocumentTemplate import render_blocks, safe_callable
from DocumentTemplate.cDocumentTemplate import join_unicode

from RestrictedPython.Guards import safe_builtins
from RestrictedPython.Utilities import utility_builtins
from RestrictedPython.Eval import RestrictionCapableEval

test = utility_builtins['test'] # for backwards compatibility, dont remove!

LIMITED_BUILTINS = 1

str=__builtins__['str'] # Waaaaa, waaaaaaaa needed for pickling waaaaa

class ParseError(Exception):
    """Document Template Parse Error"""

from zExceptions import Unauthorized as ValidationError

def int_param(params,md,name,default=0, st=type('')):
    v = params.get(name, default)
    if v:
        try:
            v = int(v)
        except:
            v = md[v]
            if isinstance(v, str):
                v = int(v)
    return v or 0

functype = type(int_param)
class NotBindable:
    # Used to prevent TemplateDict from trying to bind to functions.
    def __init__(self, f):
        self.__call__ = f

for name, f in safe_builtins.items() + utility_builtins.items():
    if type(f) is functype:
        f = NotBindable(f)
    setattr(TemplateDict, name, f)

if LIMITED_BUILTINS:
    # Replace certain builtins with limited versions.
    from RestrictedPython.Limits import limited_builtins
    for name, f in limited_builtins.items():
        if type(f) is functype:
            f = NotBindable(f)
        setattr(TemplateDict, name, f)

try:
    # Wrap the string module so it can deal with TaintedString strings.
    from ZPublisher.TaintedString import TaintedString
    from types import FunctionType, BuiltinFunctionType, StringType
    import string

    class StringModuleWrapper:
        def __getattr__(self, key):
            attr = getattr(string, key)
            if (isinstance(attr, FunctionType) or
                isinstance(attr, BuiltinFunctionType)):
                return StringFunctionWrapper(attr)
            else:
                return attr

    class StringFunctionWrapper:
        def __init__(self, method):
            self._method = method

        def __call__(self, *args, **kw):
            tainted = 0
            args = list(args)
            for i in range(len(args)):
                if isinstance(args[i], TaintedString):
                    tainted = 1
                    args[i] = str(args[i])
            for k, v in kw.items():
                if isinstance(v, TaintedString):
                    tainted = 1
                    kw[k] = str(v)
            args = tuple(args)

            retval = self._method(*args, **kw)
            if tainted and isinstance(retval, StringType) and '<' in retval:
                retval = TaintedString(retval)
            return retval

    TemplateDict.string = StringModuleWrapper()

except ImportError:
    # Use the string module already defined in RestrictedPython.Utilities
    pass

# The functions below are meant to bind to the TemplateDict.

_marker = []  # Create a new marker object.

def careful_getattr(md, inst, name, default=_marker):

    get = md.guarded_getattr
    if get is None:
        get = getattr
    try:
        return get(inst, name)
    except AttributeError:
        if default is _marker:
            raise
        return default

def careful_hasattr(md, inst, name):

    get = md.guarded_getattr
    if get is None:
        get = getattr
    try:
        get(inst, name)
    except (AttributeError, ValidationError, KeyError):
        return 0
    else:
        return 1

TemplateDict.getattr = careful_getattr
TemplateDict.hasattr = careful_hasattr

def namespace(self, **kw):
    """Create a tuple consisting of a single instance whose attributes are
    provided as keyword arguments."""
    if not (getattr(self, '__class__', None) == TemplateDict or
            isinstance(self, TemplateDict)):
        raise TypeError,'''A call was made to DT_Util.namespace() with an
        incorrect "self" argument.  It could be caused by a product which
        is not yet compatible with this version of Zope.  The traceback
        information may contain more details.)'''
    return self(**kw)

TemplateDict.namespace = namespace

def render(self, v):
    "Render an object in the way done by the 'name' attribute"
    if hasattr(v, '__render_with_namespace__'):
        v = v.__render_with_namespace__(self)
    else:
        vbase = getattr(v, 'aq_base', v)
        if safe_callable(vbase):
            if getattr(vbase, 'isDocTemp', 0):
                v = v(None, self)
            else:
                v = v()
    return v

TemplateDict.render = render


class Eval(RestrictionCapableEval):

    def eval(self, md):
        gattr = getattr(md, 'guarded_getattr', None)
        if gattr is not None:
            gitem = getattr(md, 'guarded_getitem', None)
            self.prepRestrictedCode()
            code = self.rcode
            d = {'_': md, '_vars': md,
                 '_getattr_': gattr,
                 '_getitem_': gitem,
                 '__builtins__': None}
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
                raise ParseError('%s and expr given' % attr, tag)
            if expr:
                if used('expr'):
                    raise ParseError('two exprs given', tag)
                v=v[1:-1]
                try: expr=Eval(v)
                except SyntaxError, v:
                    raise ParseError(
                        '<strong>Expression (Python) Syntax error</strong>:'
                        '\n<pre>\n%s\n</pre>\n' % v[0],
                        tag)
                return v, expr
            else: raise ParseError(
                'The "..." shorthand for expr was used in a tag '
                'that doesn\'t support expr attributes.',
                tag)

        else: # name shorthand
            if used(attr):
                raise ParseError('Two %s values were given' % attr, tag)
            if expr:
                if used('expr'):
                    # raise 'Waaaaaa', 'waaa'
                    raise ParseError('%s and expr given' % attr, tag)
                return params[''],None
            return params['']

    elif used(attr):
        if expr:
            if used('expr'):
                raise ParseError('%s and expr given' % attr, tag)
            return params[attr],None
        return params[attr]
    elif expr and used('expr'):
        name=params['expr']
        expr=Eval(name)
        return name, expr

    raise ParseError('No %s given' % attr, tag)

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

  - The Python 'string', 'math', and 'random' modules, and

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
                if parms[name] is None: raise ParseError(
                    'Attribute %s requires a value' % name, tag)

                result[name]=parms[name]
            else: raise ParseError(
                'Invalid attribute name, "%s"' % name, tag)
        else:
            result['']=name
        return parse_params(text[l:],result,**parms)
    elif mo_unq:
        name=mo_unq.group(2)
        l=len(mo_unq.group(1))
        if result: raise ParseError(
            'Invalid attribute name, "%s"' % name, tag)
        else: result['']=name
        return parse_params(text[l:],result,**parms)
    else:
        if not text or not text.strip(): return result
        raise ParseError('invalid parameter: "%s"' % text, tag)

    if not parms.has_key(name):
        raise ParseError(
            'Invalid attribute name, "%s"' % name, tag)

    if result.has_key(name):
        p=parms[name]
        if type(p) is not ListType or p:
            raise ParseError(
                'Duplicate values for attribute "%s"' % name, tag)

    result[name]=value

    text=text[l:].strip()
    if text: return parse_params(text,result,**parms)
    else: return result
