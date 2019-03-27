##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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

from __future__ import absolute_import

from zope.deferredimport import deprecated


# BBB Zope 5.0
deprecated(
    'Please import from ZServer.Zope2.Startup.starter',
    get_starter='ZServer.Zope2.Startup.starter:get_starter',
    UnixZopeStarter='ZServer.Zope2.Startup.starter:UnixZopeStarter',
    WindowsZopeStarter='ZServer.Zope2.Startup.starter:WindowsZopeStarter',
    ZopeStarter='ZServer.Zope2.Startup.starter:ZopeStarter',
)


def get_wsgi_starter():
    from Zope2.Startup.starter import WSGIStarter
    return WSGIStarter()
