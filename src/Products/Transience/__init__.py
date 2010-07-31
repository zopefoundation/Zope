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
"""
Transience initialization routines
"""

import ZODB # this is to help out testrunner, don't remove.
import Transience
# import of MaxTransientObjectsExceeded for easy import from scripts,
# this is protected by a module security info declaration in the
# Sessions package.
from Transience import MaxTransientObjectsExceeded

def initialize(context):
    context.registerClass(
        Transience.TransientObjectContainer,
        permission=Transience.ADD_CONTAINER_PERM,
        icon='www/datacontainer.gif',
        constructors=(Transience.constructTransientObjectContainerForm,
                      Transience.constructTransientObjectContainer)
        )
    context.registerHelp()
    context.registerHelpTitle('Zope Help')
