##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""Zope-specific Python Expression Handler

Handler for Python expressions that uses the RestrictedPython package.
"""

__version__='$Revision: 1.11 $'[11:-2]

from AccessControl import safe_builtins
from AccessControl.ZopeGuards import guarded_getattr, get_safe_globals
from RestrictedPython import compile_restricted_eval
from TALES import CompilerError

from PythonExpr import PythonExpr

class PythonExpr(PythonExpr):
    _globals = get_safe_globals()
    _globals['_getattr_'] = guarded_getattr
    _globals['__debug__' ] = __debug__

    def __init__(self, name, expr, engine):
        self.expr = expr = expr.strip().replace('\n', ' ')
        code, err, warn, use = compile_restricted_eval(expr, str(self))
        if err:
            raise CompilerError, ('Python expression error:\n%s' %
                                  '\n'.join(err) )
        self._f_varnames = use.keys()
        self._code = code

    def __call__(self, econtext):
        __traceback_info__ = self.expr
        code = self._code
        g = self._bind_used_names(econtext)
        g.update(self._globals)
        return eval(code, g, {})

class _SecureModuleImporter:
    __allow_access_to_unprotected_subobjects__ = 1
    def __getitem__(self, module):
        mod = safe_builtins['__import__'](module)
        path = module.split('.')
        for name in path[1:]:
            mod = getattr(mod, name)
        return mod

from DocumentTemplate.DT_Util import TemplateDict, InstanceDict
from AccessControl.DTML import RestrictedDTML
class Rtd(RestrictedDTML, TemplateDict):
    this = None

def call_with_ns(f, ns, arg=1):
    td = Rtd()
    # prefer 'context' to 'here';  fall back to 'None'
    this = ns.get('context', ns.get('here'))
    td.this = this
    request = ns.get('request', {})
    td._push(request)
    td._push(InstanceDict(td.this, td))
    td._push(ns)
    try:
        if arg==2:
            return f(None, td)
        else:
            return f(td)
    finally:
        td._pop(3)
