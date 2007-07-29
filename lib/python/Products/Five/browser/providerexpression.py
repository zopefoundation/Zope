##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Provider expression.

$Id$
"""
from zope.contentprovider import interfaces as cp_interfaces
from zope.contentprovider.tales import TALESProviderExpression
from zope.interface import implements

class Z2ProviderExpression(TALESProviderExpression):
    """This legacy provider was needed before to add acquisition wrappers to
    the providers in order for security to work."""

    implements(cp_interfaces.ITALESProviderExpression)
