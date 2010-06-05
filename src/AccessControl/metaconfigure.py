##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
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

import warnings
from zope.security import metaconfigure
from AccessControl.class_init import InitializeClass
from AccessControl.security import protectName

class ClassDirective(metaconfigure.ClassDirective):

    def __protectName(self, name, permission_id):
        self.__context.action(
            discriminator = ('five:protectName', self.__class, name),
            callable = protectName,
            args = (self.__class, name, permission_id)
            )

    def __protectSetAttributes(self, names, permission_id):
        warnings.warn("The set_attribute option of the <require /> directive "
                      "is not supported in Zope 2. "
                      "Ignored for %s" % str(self.__class), stacklevel=3)

    def __protectSetSchema(self, schema, permission):
        warnings.warn("The set_schema option of the <require /> directive "
                      "is not supported in Zope 2. "
                      "Ignored for %s" % str(self.__class), stacklevel=3)

    def __mimic(self, _context, class_):
        warnings.warn("The like_class option of the <require /> directive "
                      "is not supported in Zope 2. "
                      "Ignored for %s" % str(self.__class), stacklevel=3)

    def __call__(self):
        return self.__context.action(
            discriminator = None,
            callable = InitializeClass,
            args = (self.__class,)
            )
