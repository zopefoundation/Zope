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

from zope.deferredimport import deprecated


_prefix = 'ZServer.Zope2.utilities.mkzopeinstance:'

# BBB Zope 5.0
deprecated(
    'Please import from ZServer.Zope2.utilities.mkzopeinstance.',
    main=_prefix + 'main',
    usage=_prefix + 'usage',
    get_skeltarget=_prefix + 'get_skeltarget',
    get_inituser=_prefix + 'get_inituser',
    write_inituser=_prefix + 'write_inituser',
    check_buildout=_prefix + 'check_buildout',
    get_zope2path=_prefix + 'get_zope2path',
)
