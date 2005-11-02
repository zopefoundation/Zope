##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Generic Components ZCML Handlers

$Id: metaconfigure.py 19283 2005-10-31 17:43:51Z philikon $
"""
from Products.Five.security import CheckerPublic, protectName
from Globals import InitializeClass as initializeClass

from zope.app.component.contentdirective import ContentDirective as \
     zope_app_ContentDirective

class ContentDirective(zope_app_ContentDirective):
        
    def __protectName(self, name, permission_id):
        self.__context.action(
            discriminator = ('five:protectName', self.__class, name),
            callable = protectName,
            args = (self.__class, name, permission_id)
            )

    def __call__(self):
        """Handle empty/simple declaration."""
        return self.__context.action(
            discriminator = ('five:initialize:class', self.__class),
            callable = initializeClass,
            args = (self.__class,)
            )
