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
import collections
import re
import sys

import pkg_resources


_version_string = None
_zope_version = None

ZopeVersion = collections.namedtuple(
    "ZopeVersion",
    ["major", "minor", "micro", "status", "release"])


def _prep_version_data():
    global _version_string, _zope_version
    if _version_string is None:
        v = sys.version_info
        pyver = "python %d.%d.%d, %s" % (v[0], v[1], v[2], sys.platform)
        dist = pkg_resources.get_distribution('Zope')
        _version_string = "%s, %s" % (dist.version, pyver)

        expr = re.compile(
            r'(?P<major>[0-9]+)\.(?P<minor>[0-9]+)(\.(?P<micro>[0-9]+))?'
            '(?P<status>[A-Za-z]+)?(?P<release>[0-9]+)?')
        version_dict = expr.match(dist.version).groupdict()
        _zope_version = ZopeVersion(
            int(version_dict.get('major') or -1),
            int(version_dict.get('minor') or -1),
            int(version_dict.get('micro') or -1),
            version_dict.get('status') or '',
            int(version_dict.get('release') or -1))


def version_txt():
    _prep_version_data()
    return '(%s)' % _version_string


def getZopeVersion():
    """return information about the Zope version as a named tuple.

    Format of zope_version tuple:
    (major <int>, minor <int>, micro <int>, status <string>, release <int>)
    If unreleased, integers may be -1.
    """
    _prep_version_data()
    return _zope_version
