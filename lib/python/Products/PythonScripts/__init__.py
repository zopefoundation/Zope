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
__doc__='''Python Scripts Product Initialization
$Id: __init__.py,v 1.8 2001/11/28 15:51:05 matt Exp $'''
__version__='$Revision: 1.8 $'[11:-2]

import PythonScript
try:
    import standard
except: pass

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
    
