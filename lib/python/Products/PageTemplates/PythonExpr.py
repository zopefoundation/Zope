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

"""Generic Python Expression Handler
"""

__version__='$Revision: 1.7 $'[11:-2]

from TALES import CompilerError
from sys import exc_info

class getSecurityManager:
    '''Null security manager'''
    def validate(self, *args, **kwargs):
        return 1
    addContext = removeContext = validateValue = validate

class PythonExpr:
    def __init__(self, name, expr, engine):
        self.expr = expr = expr.strip().replace('\n', ' ')
        try:
            d = {}
            exec 'def f():\n return %s\n' % expr.strip() in d
            self._f = d['f']
        except:
            raise CompilerError, ('Python expression error:\n'
                                  '%s: %s') % exc_info()[:2]
        self._get_used_names()

    def _get_used_names(self):
        self._f_varnames = vnames = []
        for vname in self._f.func_code.co_names:
            if vname[0] not in '$_':
                vnames.append(vname)

    def _bind_used_names(self, econtext):
        # Bind template variables
        names = {}
        vars = econtext.vars
        getType = econtext._engine.getTypes().get
        for vname in self._f_varnames:
            has, val = vars.has_get(vname)
            if not has:
                has = val = getType(vname)
                if has:
                    val = ExprTypeProxy(vname, val, econtext)
            if has:
                names[vname] = val
        return names

    def __call__(self, econtext):
        __traceback_info__ = self.expr
        f = self._f
        f.func_globals.update(self._bind_used_names(econtext))        
        return f()

    def __str__(self):
        return 'Python expression "%s"' % self.expr
    def __repr__(self):
        return '<PythonExpr %s>' % self.expr

class ExprTypeProxy:
    '''Class that proxies access to an expression type handler'''
    def __init__(self, name, handler, econtext):
        self._name = name
        self._handler = handler
        self._econtext = econtext
    def __call__(self, text):
        return self._handler(self._name, text,
                             self._econtext._engine)(self._econtext)

