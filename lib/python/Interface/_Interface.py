##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Interface object implementation

Revision information:
$Id$
"""

from _InterfaceClass import Interface as InterfaceClass

Interface = InterfaceClass("Interface")

# Now we can create the interesting interfaces and wire them up:
def wire():

    from Implements import implements

    from Attribute import Attribute
    from IAttribute import IAttribute
    implements(Attribute, IAttribute)

    from Method import Method
    from IMethod import IMethod
    implements(Method, IMethod)

    from IInterface import IInterface
    implements(InterfaceClass, IInterface)

wire()
del wire
del InterfaceClass
