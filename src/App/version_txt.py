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
import sys

import pkg_resources

_version_string = None


def _prep_version_data():
    global _version_string
    if _version_string is None:
        v = sys.version_info
        pyver = "python %d.%d.%d, %s" % (v[0], v[1], v[2], sys.platform)
        dist = pkg_resources.get_distribution('Zope2')
        _version_string = "%s, %s" % (dist.version, pyver)


def version_txt():
    _prep_version_data()
    return '(%s)' % _version_string
