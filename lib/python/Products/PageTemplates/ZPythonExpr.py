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

"""Old Zope-specific Python Expression Handler

Handler for Python expressions, using the pre-Python 2.1 restriction
machinery from PythonScripts.
"""

__version__='$Revision: 1.8 $'[11:-2]

from AccessControl import getSecurityManager
from Products.PythonScripts.Guarded import _marker, \
     GuardedBlock, theGuard, safebin, WriteGuard, ReadGuard, UntupleFunction
from TALES import CompilerError

from PythonExpr import PythonExpr

class PythonExpr(PythonExpr):
    def __init__(self, name, expr, engine):
        self.expr = expr = expr.strip().replace('\n', ' ')
        blk = GuardedBlock('def f():\n return \\\n %s\n' % expr)
        if blk.errors:
            raise CompilerError, ('Python expression error:\n%s' %
                                  '\n'.join(blk.errors) )
        guards = {'$guard': theGuard, '$write_guard': WriteGuard,
                  '$read_guard': ReadGuard, '__debug__': __debug__}
        self._f = UntupleFunction(blk.t, guards, __builtins__=safebin)
        self._get_used_names()

class _SecureModuleImporter:
    __allow_access_to_unprotected_subobjects__ = 1
    def __getitem__(self, module):
        mod = safebin['__import__'](module)
        path = module.split('.')
        for name in path[1:]:
            mod = getattr(mod, name)
        return mod

from DocumentTemplate.DT_Util import TemplateDict, InstanceDict
def validate(accessed, container, name, value, dummy):
    return getSecurityManager().validate(accessed, container, name, value)
def call_with_ns(f, ns, arg=1):
    td = TemplateDict()
    td.validate = validate
    td.this = ns['here']
    td._push(ns['request'])
    td._push(InstanceDict(td.this, td))
    td._push(ns)
    try:
        if arg==2:
            return f(None, td)
        else:
            return f(td)
    finally:
        td._pop(3)
