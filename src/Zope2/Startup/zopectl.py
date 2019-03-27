##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
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

from zope.deferredimport import deprecated


# BBB Zope 5.0
deprecated(
    'Please import from ZServer.Zope2.Startup.zopectl',
    _ignoreSIGCHLD='ZServer.Zope2.Startup.zopectl:_ignoreSIGCHLD',
    main='ZServer.Zope2.Startup.zopectl:main',
    quote_command='ZServer.Zope2.Startup.zopectl:quote_command',
    run='ZServer.Zope2.Startup.zopectl:run',
    string_list='ZServer.Zope2.Startup.zopectl:string_list',
    WIN='ZServer.Zope2.Startup.zopectl:WIN',
    ZopeCmd='ZServer.Zope2.Startup.zopectl:ZopeCmd',
    ZopeCtlOptions='ZServer.Zope2.Startup.zopectl:ZopeCtlOptions',
)
