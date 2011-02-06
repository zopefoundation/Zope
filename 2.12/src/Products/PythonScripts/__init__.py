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
__doc__='''Python Scripts Product Initialization
$Id$'''

import PythonScript
import standard

# Temporary
from Shared.DC import Scripts
__module_aliases__ = (
    ('Products.PythonScripts.Script', Scripts.Script),
    ('Products.PythonScripts.Bindings', Scripts.Bindings),
    ('Products.PythonScripts.BindingsUI', Scripts.BindingsUI),)

__roles__ = None
__allow_access_to_unprotected_subobjects__ = 1

def initialize(context):
    context.registerClass(
        PythonScript.PythonScript,
        permission='Add Python Scripts',
        constructors=(PythonScript.manage_addPythonScriptForm,
                      PythonScript.manage_addPythonScript),
        icon='www/pyscript.gif'
        )

    context.registerHelp()
    context.registerHelpTitle('Script (Python)')
    global _m
    _m['recompile'] = recompile
    _m['recompile__roles__'] = ('Manager',)

# utility stuff

def recompile(self):
    '''Recompile all Python Scripts'''
    base = self.this()
    scripts = base.ZopeFind(base, obj_metatypes=('Script (Python)',),
                            search_sub=1)
    names = []
    for name, ob in scripts:
        if ob._v_change:
            names.append(name)
            ob._compile()
            ob._p_changed = 1

    if names:
        return 'The following Scripts were recompiled:\n' + '\n'.join(names)
    return 'No Scripts were found that required recompilation.'

import patches
