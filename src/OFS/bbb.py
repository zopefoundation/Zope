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

from zope.deferredimport import deprecated


HAS_ZSERVER = True
try:
    dist = pkg_resources.get_distribution('ZServer')
except pkg_resources.DistributionNotFound:
    HAS_ZSERVER = False


# BBB Zope 5
deprecated(
    'Please import from webdav.Resource. '
    'WebDAV support is back in Zope. This shim will go away in Zope 5.',
    Resource='webdav.Resource:Resource',
)

# BBB Zope 5
deprecated(
    'Please import from webdav.NullResource. '
    'WebDAV support is back in Zope. This shim will go away in Zope 5.',
    NullResource='webdav.NullResource:NullResource',
)

# BBB Zope 5
deprecated(
    'Please import from webdav.Collection. '
    'WebDAV support is back in Zope. This shim will go away in Zope 5.',
    Collection='webdav.Collection:Collection',
)

# BBB Zope 5
deprecated(
    'Please import from webdav.PropertySheet. '
    'WebDAV support is back in Zope. This shim will go away in Zope 5.',
    DAVPropertySheetMixin='webdav.PropertySheet:DAVPropertySheetMixin',
)

# BBB Zope 5
deprecated(
    'Please import from webdav.PropertySheets. '
    'WebDAV support is back in Zope. This shim will go away in Zope 5.',
    DAVProperties='webdav.PropertySheets:DAVProperties',
)
