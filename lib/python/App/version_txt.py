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

v=sys.version_info

_version_string = None
_zope_version = None


def intval(dict, key):
    v = dict.get(key, None)
    if v is None:
        return 0
    else:
        return int(v)

def strval(dict, key):
    v = dict.get(key, None)
    if v is None:
        return ''
    else:
        return str(v)


def _prep_version_data():
    global _version_string, _zope_version
    if _version_string is None:
        try: 
            s = open(os.path.join(SOFTWARE_HOME,'version.txt')).read()
            ss = re.sub("\(.*?\)\?","",s)
            ss = '%s, python %d.%d.%d, %s' % (ss,v[0],v[1],v[2],sys.platform)
            _version_string = ss

            expr = re.compile(
                r'(?P<product>[A-Za-z0-9]+) +(?P<major>[0-9]+)'
                '\.(?P<minor>[0-9]+)\.(?P<micro>[0-9]+)'
                '(?P<status>[A-Za-z]+)?(?P<release>[0-9]+)?')
            dict = expr.match(s).groupdict()
            _zope_version = (
                intval(dict, 'major'),
                intval(dict, 'minor'),
                intval(dict, 'micro'),
                strval(dict, 'status'),
                intval(dict, 'release'))
        except:
            ss = 'unreleased version, python %d.%d.%d, %s' % (
                v[0],v[1],v[2],sys.platform)
            _version_string = ss
            _zope_version = (-1, -1, -1, '', -1)
        

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

