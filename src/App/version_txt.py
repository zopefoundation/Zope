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
VERSION_PATTERN = r"""
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
"""


def _prep_version_data():
    global _version_string, _zope_version
    if _zope_version is None:
        v = sys.version_info
        pyver = "python %d.%d.%d, %s" % (v[0], v[1], v[2], sys.platform)
        dist = pkg_resources.get_distribution('Zope')
        _version_string = f"{dist.version}, {pyver}"
        _zope_version = _parse_version_data(dist.version)


def _parse_version_data(version_string):
    expr = re.compile(r"^\s*" + VERSION_PATTERN + r"\s*$",
                      re.VERBOSE | re.IGNORECASE)
    version_dict = expr.match(version_string).groupdict()
    rel = tuple(int(i) for i in version_dict['release'].split('.'))
    micro = rel[2] if len(rel) >= 3 else 0
    if version_dict['pre']:
        micro = f'{micro}{version_dict["pre"]}'

    return ZopeVersion(
        rel[0] if len(rel) >= 1 else 0,
        rel[1] if len(rel) >= 2 else 0,
        micro,
        version_dict.get('dev_l') or '',
        int(version_dict.get('dev_n') or -1))


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
