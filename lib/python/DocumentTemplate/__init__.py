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
__doc__='''Package wrapper for Document Template

This wrapper allows the (now many) document template modules to be
segregated in a separate package.

$Id: __init__.py,v 1.16 2001/11/28 15:50:55 matt Exp $'''
__version__='$Revision: 1.16 $'[11:-2]

import ExtensionClass # work-around for import bug.
from DocumentTemplate import String, File, HTML, HTMLDefault, HTMLFile
