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

import pkg_resources

HAS_ZSERVER = True
try:
    dist = pkg_resources.get_distribution('ZServer')
except pkg_resources.DistributionNotFound:
    HAS_ZSERVER = False

NullResource = None


class Resource(object):
    def dav__init(self, request, response):
        pass

    def dav__validate(self, object, methodname, REQUEST):
        pass

    def dav__simpleifhandler(self, request, response, method='PUT',
                             col=0, url=None, refresh=0):
        pass


class Collection(Resource):
    pass


class DAVPropertySheetMixin(object):
    pass


class DAVProperties(object):
    pass
