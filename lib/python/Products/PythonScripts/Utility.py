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
"""Utility module for making simple security assertions for
   Python scripts."""

__version__='$Revision: 1.4 $'[11:-2]

from AccessControl import ModuleSecurityInfo, ClassSecurityInfo
from Globals import InitializeClass
import string

def allow_module(module_name):
    """Allow a module and all its contents to be used from a
    restricted Script. The argument module_name may be a simple
    or dotted module or package name. Note that if a package
    path is given, all modules in the path will be available."""
    ModuleSecurityInfo(module_name).setDefaultAccess(1)
    dot = string.find(module_name, '.')
    while dot > 0:
        ModuleSecurityInfo(module_name[:dot]).setDefaultAccess(1)
        dot = string.find(module_name, '.', dot + 1)

def allow_class(Class):
    """Allow a class and all of its methods to be used from a
    restricted Script.  The argument Class must be a class."""
    Class._security = sec = ClassSecurityInfo()
    sec.declareObjectPublic()
    sec.setDefaultAccess(1)
    sec.apply(Class)
    InitializeClass(Class)

