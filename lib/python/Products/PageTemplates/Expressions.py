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

"""Page Template Expression Engine

Page Template-specific implementation of TALES, with handlers
for Python expressions, Python string literals, and paths.
"""

__version__='$Revision: 1.9 $'[11:-2]

import re, sys
from TALES import Engine, CompilerError, _valid_name, NAME_RE, \
     TALESError, Undefined
from string import strip, split, join, replace, lstrip
from DocumentTemplate.DT_Util import TemplateDict
from Acquisition import aq_base, aq_inner, aq_parent

_engine = None
def getEngine():
    global _engine
    if _engine is None:
        _engine = Engine()
        installHandlers(_engine)
    return _engine

def installHandlers(engine):
    reg = engine.registerType
    pe = PathExpr
    for pt in ('standard', 'path', 'nocall', 'exists'):
        reg(pt, pe)
    reg('string', StringExpr)
    reg('python', PythonExpr)
    reg('not', NotExpr)
    reg('import', ImportExpr)

def render(ob, ns):
    """
    Calls the object, possibly a document template, or just returns it if
    not callable.  (From DT_Util.py)
    """
    if hasattr(ob, '__render_with_namespace__'):
        ob = ob.__render_with_namespace__(ns)
    else:
        base = aq_base(ob)
        if callable(base):
            try:
                if getattr(base, 'isDocTemp', 0):
                    ob = ob(aq_parent(ob), ns)
                else:
                    ob = ob()
            except AttributeError, n:
                if str(n) != '__call__':
                    raise
    return ob

path_modifiers = {'if': 0, 'exists': 0, 'nocall':0}

class PathExpr:
    def __init__(self, name, expr):
        self._s = expr
        self._name = name
        self._path = path = split(expr, '/')
        front = path.pop(0)
        fronts = split(replace(replace(front, '(', '( '), ')', ' ) '))
        self._base = base = fronts.pop()
        if not _valid_name(base):
            raise CompilerError, 'Invalid variable name "%s"' % base
        # Parse path modifiers
        self.modifiers = modifiers = path_modifiers.copy()
        if fronts:
            if len(fronts) < 2 or (fronts.pop(0) != '(' or
                                   fronts.pop()  != ')'):
                raise CompilerError, 'Invalid path base "%s"' % front
            for modifier in fronts:
                if not modifiers.has_key(modifier):
                    raise CompilerError, ('Unknown path modifier "%s"'
                                          % modifier)
                modifiers[modifier] = 1
        # Parse path
        self._dynparts = dp = []
        for i in range(len(path)):
            e = path[i]
            if e[:1] == '?' and _valid_name(e[1:]):
                dp.append((i, e[1:]))
        dp.reverse()
        # Choose call method
        on = modifiers.get
        callname = on('if') + on('exists') * 2
        callname = ('Render', 'If', 'Exists', 'IfExists')[callname]
        if on('nocall') and callname == 'Render':
            callname = ''
        self._call_name = '_eval' + callname

    def _evalRender(self, econtext):
        return render(self._eval(econtext), econtext.contexts)

    def _evalIf(self, econtext):
        val = self._eval(econtext)
        if not val:
            return Undefined
        if self.modifiers.has_key('nocall'):
            return val
        return render(val, econtext.contexts)

    def _evalExists(self, econtext):
        try:
            self._eval(econtext)
        except (Undefined, 'Unauthorized'):
            return 0
        return 1

    def _evalIfExists(self, econtext):
        try:
            val = self._eval(econtext)
        except (Undefined, 'Unauthorized'):
            return Undefined
        if self.modifiers.has_key('nocall'):
            return val
        return render(val, econtext.contexts)

    def _eval(self, econtext):
        base = self._base
        path = list(self._path) # Copy!
        contexts = econtext.contexts
        var = contexts['var']
        # Expand dynamic path parts from right to left.
        for i, varname in self._dynparts:
            val = var[varname]
            if type(val) is type(''):
                path[i] = val
            else:
                # If the value isn't a string, assume it's a sequence
                # of path names.
                path[i:i+1] = list(val)
        try:
            __traceback_info__ = base
            if var.has_key(base):
                ob = var[base]
            else:
                ob = contexts[base]
                # Work around lack of security declaration
                if path and (ob is contexts['repeat']):
                    step = path.pop(0)
                    __traceback_info__ = (base, step)
                    ob = ob[step]
            return restrictedTraverse(ob, path)
        except (AttributeError, KeyError, TypeError, IndexError), e:
            raise Undefined, (self._s, sys.exc_info()), sys.exc_info()[2]

    def __call__(self, econtext):
        return getattr(self, self._call_name)(econtext)

    def __str__(self):
        return '%s expression "%s"' % (self._name, self._s)

    def __repr__(self):
        return '<PathExpr %s:%s>' % (self._name, self._s)

            
_interp = re.compile(r'\$(%(n)s)|\${(%(n)s(?:/%(n)s)*)}' % {'n': NAME_RE})

class StringExpr:
    def __init__(self, name, expr):
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
                    vars.append(PathExpr('path', m.group(1) or m.group(2)))
                    exp = exp[m.end():]
                    m = _interp.search(exp)
                if '$' in exp:
                    raise CompilerError, (
                        '$ must be doubled or followed by a variable name '
                        'in string expression "%s"' % expr)
                parts.append(exp)
            expr = join(parts, '')
        self._expr = expr
        
    def __call__(self, econtext):
        vvals = []
        for var in self._vars:
            vvals.append(var(econtext))
        return self._expr % tuple(vvals)

    def __str__(self):
        return 'string expression %s' % `self._s`

    def __repr__(self):
        return '<StringExpr %s>' % `self._s`

class NotExpr:
    def __init__(self, name, expr, compiler):
        self._s = expr = lstrip(expr)
        self._c = compiler.compile(expr)
        
    def __call__(self, econtext):
        return not econtext.evaluateBoolean(self._c)

    def __repr__(self):
        return '<NotExpr %s>' % `self._s`


if sys.modules.has_key('Zope'):
    from AccessControl import getSecurityManager
    from Products.PythonScripts.Guarded import _marker, \
      GuardedBlock, theGuard, safebin, WriteGuard, ReadGuard, UntupleFunction

    class PythonExpr:
        def __init__(self, name, expr):
            self.expr = expr = strip(expr)
            blk = GuardedBlock('def f():\n return %s\n' % expr)
            if blk.errors:
                raise CompilerError, ('Python expression error:\n%s' %
                                      join(blk.errors, '\n') )
            guards = {'$guard': theGuard, '$write_guard': WriteGuard,
                      '$read_guard': ReadGuard, '__debug__': __debug__}
            self._f = UntupleFunction(blk.t, guards, __builtins__=safebin)
            self._f_varnames = vnames = []
            for vname in self._f.func_code.co_names:
                if vname[0] not in '$_':
                    vnames.append(vname)

        def __call__(self, econtext):
            f = self._f

            # Bind template variables
            var = econtext.contexts['var']
            for vname in self._f_varnames:
                val = var.get(vname, _marker)
                if val is not _marker:
                    f.func_globals[vname] = val

            # Execute the function in a new security context.
            template = econtext.contexts['template']
            security = getSecurityManager()
            security.addContext(template)
            try:
                __traceback_info__ = self.expr
                return f()
            finally:
                security.removeContext(template)

        def __str__(self):
            return 'Python expression "%s"' % self.expr
        def __repr__(self):
            return '<PythonExpr %s>' % self.expr

else:
    class getSecurityManager:
        '''Null security manager'''
        def validate(self, *args, **kwargs):
            return 1
        validateValue = validate
    _marker = []

    class PythonExpr:
        def __init__(self, name, expr):
            try:
                d = {}
                exec 'def f():\n return %s\n' % strip(expr) in d
                self._f = d['f']
            except:
                raise CompilerError, ('Python expression error:\n'
                                      '%s: %s') % sys.exc_info()[:2]
            self._f_varnames = vnames = []
            for vname in self._f.func_code.co_names:
                if vname[0] not in '$_':
                    vnames.append(vname)

        def __call__(self, econtext):
            f = self._f

            # Bind template variables
            var = econtext.contexts['var']
            for vname in self._f_varnames:
                val = var.get(vname, _marker)
                if val is not _marker:
                    f.func_globals[vname] = val

            # Execute the function in a new security context.
            template = econtext.contexts['template']
            return f()
    
class ImportExpr:
    def __init__(self, name, expr):
        self._s = expr
    def __call__(self, econtext):
        return safebin['__import__'](self._s)
    def __repr__(self):
        return '<ImportExpr %s>' % `self._s`

def restrictedTraverse(self, path):

    if not path: return self

    get=getattr
    N=None
    M=[] #marker

    REQUEST={'TraversalRequestNameStack': path}
    securityManager = getSecurityManager()
    
    plen = len(path)
    i = 0
    if not path[0]:
        # If the path starts with an empty string, go to the root first.
        i = 1
        self = self.getPhysicalRoot()
        if not securityManager.validateValue(self):
            raise 'Unauthorized', name
                    
    object = self
    while i < plen:
        __traceback_info__ = (path, i)
        name = path[i]
        i = i + 1

        if name[0] == '_':
            # Never allowed in a URL.
            raise AttributeError, name

        if name=='..':
            o = getattr(object, 'aq_parent', M)
            if o is not M:
                if not securityManager.validate(object, object, name, o):
                    raise 'Unauthorized', name
                object=o
                continue

        t=get(object, '__bobo_traverse__', N)
        if t is not N:
            o=t(REQUEST, name)
                    
            container = None
            if (hasattr(get(object, 'aq_base', object), name)
                and get(object, name) is o):
                container = object
            if not securityManager.validate(object, container, name, o):
                raise 'Unauthorized', name
        else:
            o=get(object, name, M)
            if o is not M:
                # Check security.
                if hasattr(object, 'aq_acquire'):
                    object.aq_acquire(
                        name, validate2, securityManager.validate)
                else:
                    if not securityManager.validate(object, object, name, o):
                        raise 'Unauthorized', name
            else:
                try:
                    o=object[name]
                except (AttributeError, TypeError):
                    raise AttributeError, name
                if not securityManager.validate(object, object, None, o):
                    raise 'Unauthorized', name
        object = o

    return object


def validate2(orig, inst, name, v, real_validate):
    if not real_validate(orig, inst, name, v):
        raise 'Unauthorized', name
    return 1
