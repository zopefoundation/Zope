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

from threading import local

# a thread-local object holding arbitrary data
localData = local()
marker = object()


def getRequest(default=None):
    """ return the currently active request object """
    value = getattr(localData, 'request', marker)
    if value is marker:
        return default
    return value


def setRequest(request):
    """ set the request object to be returned by `getRequest` """
    setattr(localData, 'request', request)


def clearRequest():
    """ clear the stored request object """
    setRequest(None)


def getAppRoot(default=None):
    """ return the currently active request object """
    value = getattr(localData, 'app', marker)
    if value is marker:
        return default
    return value


def setAppRoot(app):
    """ set the request object to be returned by `getRequest` """
    setattr(localData, 'app', app)
