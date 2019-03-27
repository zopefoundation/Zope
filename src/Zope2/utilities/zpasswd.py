##############################################################################
#
# Copyright (c) 2001,2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from zope.deferredimport import deprecated


# BBB Zope 5.0
deprecated(
    'Please import from ZServer.Zope2.utilities.zpasswd',
    generate_salt='ZServer.Zope2.utilities.zpasswd:generate_salt',
    generate_passwd='ZServer.Zope2.utilities.zpasswd:generate_passwd',
    write_generated_password=('ZServer.Zope2.utilities.zpasswd:'
                              'write_generated_password'),
    write_access='ZServer.Zope2.utilities.zpasswd:write_access',
    get_password='ZServer.Zope2.utilities.zpasswd:get_password',
    write_inituser='ZServer.Zope2.utilities.zpasswd:write_inituser',
    usage='ZServer.Zope2.utilities.zpasswd:usage',
    main='ZServer.Zope2.utilities.zpasswd:main',
)
