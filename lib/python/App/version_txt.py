##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import os,sys,re

from App.config import getConfiguration

_version_string = None
_zope_version = None

def _test_reset():
    # Needed for testing.
    global _version_string, _zope_version
    _version_string = None
    _zope_version = None

def _prep_version_data():
    global _version_string, _zope_version
    if _version_string is None:
        v = sys.version_info
        pyver = "python %d.%d.%d, %s" % (v[0], v[1], v[2], sys.platform)
        cfg = getConfiguration()
        fn = os.path.join(cfg.softwarehome, 'version.txt')
        expr = re.compile(
            r'(?P<product>[A-Za-z0-9]+) +(?P<major>[0-9]+)'
            '\.(?P<minor>[0-9]+)\.(?P<micro>[0-9]+)'
            '(?P<status>[A-Za-z]+)?(?P<release>[0-9]+)?')
        try:
            s = open(fn).read().strip()
        except IOError:
            ss = 'unreleased version'
            _zope_version = (-1, -1, -1, '', -1)
        else:
            ss = re.sub("\(.*?\)\?","",s)
            dict = expr.match(s).groupdict()
            _zope_version = (
                int(dict.get('major') or -1),
                int(dict.get('minor') or -1),
                int(dict.get('micro') or -1),
                dict.get('status') or '',
                int(dict.get('release') or -1),
                )
        _version_string = "%s, %s" % (ss, pyver)


def version_txt():
    _prep_version_data()
    return '(%s)' % _version_string

def getZopeVersion():
    """
    Format of zope_version tuple:
    (major <int>, minor <int>, micro <int>, status <string>, release <int>)
    If unreleased, integers may be -1.
    """
    _prep_version_data()
    return _zope_version
