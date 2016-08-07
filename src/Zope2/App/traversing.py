##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

from zExceptions import Forbidden
from zope.interface.interface import InterfaceClass
from zope.traversing import namespace


class resource(namespace.view):

    def traverse(self, name, ignored):
        # The context is important here, since it becomes the parent of the
        # resource, which is needed to generate the absolute URL.
        res = namespace.getResource(self.context, name, self.request)
        if isinstance(res, InterfaceClass):
            raise Forbidden('Access to traverser is forbidden.')
        return res
