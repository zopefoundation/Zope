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
__doc__='''Collected utilities to support database indexing.


$Id: __init__.py,v 1.9 2001/11/28 15:51:11 matt Exp $'''
__version__='$Revision: 1.9 $'[11:-2]
import warnings
warnings.warn("The usage of the SearchIndex package is deprecated since \
Zope 2.4.\n\
This package is only kept for backwards compatibility for a while\n\
and will go away in a future release.\n\
\n\
Please use instead the re-factored modules in Products/PluginIndexes.\n\
",DeprecationWarning)

