##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

"""Page Template Expression Engine

Page Template-specific implementation of TALES, with handlers
for Python expressions, string literals, and paths.
"""

__version__='$Revision: 1.27 $'[11:-2]

import re, sys
from TALES import Engine, CompilerError, _valid_name, NAME_RE, \
     TALESError, Undefined, Default
from string import strip, split, join, replace, lstrip
from Acquisition import aq_base, aq_inner, aq_parent

_engine = None
def getEngine():
    global _engine
    if _engine is None:
        _engine = Engine()
        installHandlers(_engine)
        _engine._nocatch = (TALESError, 'Redirect')
    return _engine

def installHandlers(engine):
    reg = engine.registerType
    pe = PathExpr
    for pt in ('standard', 'path', 'exists', 'nocall'):
        reg(pt, pe)
    reg('string', StringExpr)
    reg('python', PythonExpr)
    reg('not', NotExpr)
    reg('defer', DeferExpr)

if sys.modules.has_key('Zope'):
    import AccessControl
    from AccessControl import getSecurityManager
    try:
        from AccessControl import Unauthorized
    except ImportError:
        Unauthorized = "Unauthorized"
    if hasattr(AccessControl, 'full_read_guard'):
        from ZRPythonExpr import PythonExpr, _SecureModuleImporter, \
             call_with_ns
    else:
        from ZPythonExpr import PythonExpr, _SecureModuleImporter, \
             call_with_ns
    SecureModuleImporter = _SecureModuleImporter()
else:
    from PythonExpr import getSecurityManager, PythonExpr
    try:
        from zExceptions import Unauthorized
    except ImportError:
        Unauthorized = "Unauthorized"
    def call_with_ns(f, ns, arg=1):
        if arg==2:
            return f(None, ns)
        else:
            return f(ns)
    
def render(ob, ns):
    """
    Calls the object, possibly a document template, or just returns it if
    not callable.  (From DT_Util.py)
    """
    if hasattr(ob, '__render_with_namespace__'):
        ob = call_with_ns(ob.__render_with_namespace__, ns)
    else:
        base = aq_base(ob)
        if callable(base):
            try:
                if getattr(base, 'isDocTemp', 0):
                    ob = call_with_ns(ob, ns, 2)
                else:
                    ob = ob()
            except AttributeError, n:
                if str(n) != '__call__':
                    raise
    return ob

class PathExpr:
    def __init__(self, name, expr, engine):
        self._s = expr
        self._name = name
        self._paths = map(self._prepPath, split(expr, '|'))

    def _prepPath(self, path):
        path = split(strip(path), '/')
        base = path.pop(0)
        if not _valid_name(base):
            raise CompilerError, 'Invalid variable name "%s"' % base
        # Parse path
        dp = []
        for i in range(len(path)):
            e = path[i]
            if e[:1] == '?' and _valid_name(e[1:]):
                dp.append((i, e[1:]))
        dp.reverse()
        return base, path, dp

    def _eval(self, econtext, securityManager,
              list=list, isinstance=isinstance, StringType=type(''),
              render=render):
        vars = econtext.vars
        exists = 0
        more_paths = len(self._paths)
        for base, path, dp in self._paths:
            more_paths = more_paths - 1
            # Expand dynamic path parts from right to left.
            if dp:
                path = list(path) # Copy!
                for i, varname in dp:
                    val = vars[varname]
                    if isinstance(val, StringType):
                        path[i] = val
                    else:
                        # If the value isn't a string, assume it's a sequence
                        # of path names.
                        path[i:i+1] = list(val)
            try:
                __traceback_info__ = base
                if base == 'CONTEXTS':
                    ob = econtext.contexts
                else:
                    ob = vars[base]
                if isinstance(ob, DeferWrapper):
                    ob = ob()
                if path:
                    ob = restrictedTraverse(ob, path, securityManager)
                exists = 1
                break
            except Undefined:
                if not more_paths:
                    raise
            except (AttributeError, KeyError, TypeError, IndexError,
                    Unauthorized), e:
                if not more_paths:
                    raise Undefined(self._s, sys.exc_info())

        if self._name == 'exists':
            # All we wanted to know is whether one of the paths exist.
            return exists
        if self._name == 'nocall' or isinstance(ob, StringType):
            return ob
        # Return the rendered object
        return render(ob, vars)

    def __call__(self, econtext):
        return self._eval(econtext, getSecurityManager())

    def __str__(self):
        return '%s expression %s' % (self._name, `self._s`)

    def __repr__(self):
        return '%s:%s' % (self._name, `self._s`)

            
_interp = re.compile(r'\$(%(n)s)|\${(%(n)s(?:/%(n)s)*)}' % {'n': NAME_RE})

class StringExpr:
    def __init__(self, name, expr, engine):
        self._s = expr
        if '%' in expr:
            expr = replace(expr, '%', '%%')
        self._vars = vars = []
        if '$' in expr:
            parts = []
            for exp in split(expr, '$$'):
                if parts: parts.append('$')
                m = _interp.search(exp)
                while m is not None:
                    parts.append(exp[:m.start()])
                    parts.append('%s')
                    vars.append(PathExpr('path', m.group(1) or m.group(2),
                                         engine))
                    exp = exp[m.end():]
                    m = _interp.search(exp)
                if '$' in exp:
                    raise CompilerError, (
                        '$ must be doubled or followed by a simple path')
                parts.append(exp)
            expr = join(parts, '')
        self._expr = expr
        
    def __call__(self, econtext):
        vvals = []
        for var in self._vars:
            v = var(econtext)
            if isinstance(v, Exception):
                raise v
            vvals.append(v)
        return self._expr % tuple(vvals)

    def __str__(self):
        return 'string expression %s' % `self._s`

    def __repr__(self):
        return 'string:%s' % `self._s`

class NotExpr:
    def __init__(self, name, expr, compiler):
        self._s = expr = lstrip(expr)
        self._c = compiler.compile(expr)
        
    def __call__(self, econtext):
        return not econtext.evaluateBoolean(self._c)

    def __repr__(self):
        return 'not:%s' % `self._s`

class DeferWrapper:
    def __init__(self, expr, econtext):
        self._expr = expr
        self._econtext = econtext

    def __str__(self):
        return str(self())

    def __call__(self):
        return self._expr(self._econtext)

class DeferExpr:
    def __init__(self, name, expr, compiler):
        self._s = expr = lstrip(expr)
        self._c = compiler.compile(expr)
        
    def __call__(self, econtext):
        return DeferWrapper(self._c, econtext)

    def __repr__(self):
        return 'defer:%s' % `self._s`


def restrictedTraverse(self, path, securityManager,
                       get=getattr, has=hasattr, N=None, M=[]):

    i = 0
    if not path[0]:
        # If the path starts with an empty string, go to the root first.
        self = self.getPhysicalRoot()
        if not securityManager.validateValue(self):
            raise Unauthorized, name
        i = 1

    plen = len(path)
    REQUEST={'TraversalRequestNameStack': path}
    validate = securityManager.validate
    object = self
    while i < plen:
        __traceback_info__ = (path, i)
        name = path[i]
        i = i + 1

        if name[0] == '_':
            # Never allowed in a URL.
            raise AttributeError, name

        if name=='..':
            o = get(object, 'aq_parent', M)
            if o is not M:
                if not validate(object, object, name, o):
                    raise Unauthorized, name
                object=o
                continue

        t=get(object, '__bobo_traverse__', N)
        if t is not N:
            o=t(REQUEST, name)
                    
            container = None
            if has(o, 'im_self'):
                container = o.im_self
            elif (has(get(object, 'aq_base', object), name)
                and get(object, name) == o):
                container = object
            if not validate(object, container, name, o):
                raise Unauthorized, name
        else:
            o=get(object, name, M)
            if o is not M:
                # Check security.
                if has(object, 'aq_acquire'):
                    object.aq_acquire(
                        name, validate2, validate)
                else:
                    if not validate(object, object, name, o):
                        raise Unauthorized, name
            else:
                try:
                    o=object[name]
                except (AttributeError, TypeError):
                    raise AttributeError, name
                if not validate(object, object, name, o):
                    raise Unauthorized, name
        object = o

    return object


def validate2(orig, inst, name, v, real_validate):
    if not real_validate(orig, inst, name, v):
        raise Unauthorized, name
    return 1
