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

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.ImageFile import ImageFile
from os.path import dirname

import App


class misc_(object):
    "Miscellaneous product information"
    security = ClassSecurityInfo()
    security.declareObjectPublic()


InitializeClass(misc_)


class p_(object):
    "Shared system information"
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    app_dir = dirname(App.__file__)
    zopelogo_png = ImageFile('www/zopelogo.png', app_dir)


InitializeClass(p_)


class Misc_(object):
    "Miscellaneous product information"
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    def __init__(self, name, dict):
        self._d = dict
        self.__name__ = name

    def __str__(self):
        return self.__name__

    def __getitem__(self, name):
        return self._d[name]

    def __setitem__(self, name, v):
        self._d[name] = v


InitializeClass(Misc_)
