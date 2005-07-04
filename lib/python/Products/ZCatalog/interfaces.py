##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ZCatalog z3 interfaces.

$Id$
"""

# create IZCatalog
from Products.Five.fiveconfigure import createZope2Bridge
from IZCatalog import IZCatalog as z2IZCatalog
import interfaces

createZope2Bridge(z2IZCatalog, interfaces, 'IZCatalog')

del createZope2Bridge
del z2IZCatalog
del interfaces
