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
"""Generic Python Expression Handler

$Id$
"""
# BBB 2005/05/01 -- remove after 12 months
import zope.deferredimport
zope.deferredimport.deprecatedFrom(
    "Zope 2 uses the Zope 3 ZPT engine now.  The PythonExpr type can be "
    "imported from zope.tales.pythonexpr.",
    "zope.tales.pythonexpr",
    "PythonExpr", "ExprTypeProxy"
    )
