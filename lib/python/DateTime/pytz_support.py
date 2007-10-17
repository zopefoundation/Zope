##############################################################################
#
# Copyright (c) 2007 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
Pytz timezone support.
"""

import pytz
import pytz.reference
from datetime import datetime, timedelta
import re

class Timezone:
    """
    Timezone information returned by PytzCache.__getitem__
    Adapts datetime.tzinfo object to DateTime._timezone interface
    """
    def __init__(self, tzinfo):
        self.tzinfo = tzinfo
        
    def info(self, t=None):
        if t is None:
            dt = datetime.utcnow().replace(tzinfo=pytz.utc)
        else:
            dt = datetime.utcfromtimestamp(t).replace(tzinfo=pytz.utc)

        # need to normalize tzinfo for the datetime to deal with
        # daylight savings time.
        normalized_dt = self.tzinfo.normalize(dt.astimezone(self.tzinfo))
        normalized_tzinfo = normalized_dt.tzinfo
        
        offset = normalized_tzinfo.utcoffset(dt)
        secs = offset.days * 24 * 60 * 60 + offset.seconds
        dst = normalized_tzinfo.dst(dt)
        if dst == timedelta(0):
            is_dst = 0
        else:
            is_dst = 1
        return secs, is_dst, normalized_tzinfo.tzname(dt)


class PytzCache:
    """
    Wrapper for the DateTime._cache class that uses pytz for
    timezone information where possible.
    """
    def __init__(self, cache):
        self.cache = cache
        self._zlst = list(pytz.common_timezones)
        for name in cache._zlst:
            if name not in self._zlst:
                self._zlst.append(name)
        self._zmap = dict(cache._zmap)
        self._zmap.update(dict([(name.lower(), name)
                            for name in pytz.common_timezones]))
        self._zidx = self._zmap.keys()
        
    def __getitem__(self, key):
        try:
            name = self._zmap[key.lower()]
            return Timezone(pytz.timezone(name))
        except (KeyError, pytz.UnknownTimeZoneError):
            return self.cache[key]
    
