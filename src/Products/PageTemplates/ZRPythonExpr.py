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
"""Zope-specific Python Expression Handler

Handler for Python expressions that uses the RestrictedPython package.
"""

from AccessControl import safe_builtins
from AccessControl.ZopeGuards import get_safe_globals
from AccessControl.ZopeGuards import guarded_getattr
from DocumentTemplate._DocumentTemplate import InstanceDict
from DocumentTemplate._DocumentTemplate import TemplateDict
from DocumentTemplate.security import RestrictedDTML
from RestrictedPython import compile_restricted_eval
from zope.tales.pythonexpr import PythonExpr


class PythonExpr(PythonExpr):
    _globals = get_safe_globals()
    _globals['_getattr_'] = guarded_getattr
    _globals['__debug__'] = __debug__

    def __init__(self, name, expr, engine):
        self.text = self.expr = text = expr.strip().replace('\n', ' ')
        code, err, warn, use = compile_restricted_eval(
            text, self.__class__.__name__)

        if err:
            raise engine.getCompilerError()(
                'Python expression error:\n%s' % '\n'.join(err))

        self._varnames = list(use.keys())
        self._code = code

    def __call__(self, econtext):
        __traceback_info__ = self.text
        vars = self._bind_used_names(econtext, {})
        vars.update(self._globals)
        return eval(self._code, vars, {})


class _SecureModuleImporter:
    __allow_access_to_unprotected_subobjects__ = True

    def __getitem__(self, module):
        mod = safe_builtins['__import__'](module)
        path = module.split('.')
        for name in path[1:]:
            mod = getattr(mod, name)
        return mod


class Rtd(RestrictedDTML, TemplateDict):
    this = None


def call_with_ns(f, ns, arg=1):
    td = Rtd()
    # prefer 'context' to 'here';  fall back to 'None'
    this = ns.get('context', ns.get('here'))
    td.this = this
    request = ns.get('request', {})
    if hasattr(request, 'taintWrapper'):
        request = request.taintWrapper()
    td._push(request)
    td._push(InstanceDict(td.this, td))
    td._push(ns)
    try:
        if arg == 2:
            return f(None, td)
        else:
            return f(td)
    finally:
        td._pop(3)
