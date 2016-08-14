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
"""Commonly used functions for WebDAV support modules."""

import re
import urllib

from Acquisition import aq_base, aq_parent
from zExceptions import (
    HTTPConflict,
    HTTPLocked,
    HTTPPreconditionFailed,
    HTTPUnsupportedMediaType,
)
from zope.deferredimport import deprecated

deprecated(
    'Please import from App.Common.',
    iso8601_date='App.Common:iso8601_date',
    rfc1123_date='App.Common:rfc1123_date',
    rfc850_date='App.Common:rfc850_date',
)

deprecated(
    'Please import from OFS.LockItem.',
    _randGen='OFS.Locked:_randGen',
    generateLockToken='OFS.LockItem:generateLockToken',
)


class WebDAVException(Exception):
    pass


class Locked(WebDAVException, HTTPLocked):
    pass


class PreconditionFailed(WebDAVException, HTTPPreconditionFailed):
    pass


class Conflict(WebDAVException, HTTPConflict):
    pass


class UnsupportedMediaType(WebDAVException, HTTPUnsupportedMediaType):
    pass


def absattr(attr):
    if callable(attr):
        return attr()
    return attr


def urljoin(url, s):
    url = url.rstrip('/')
    s = s.lstrip('/')
    return '/'.join((url, s))


def urlfix(url, s):
    n = len(s)
    if url[-n:] == s:
        url = url[:-n]
    if len(url) > 1 and url[-1] == '/':
        url = url[:-1]
    return url


def is_acquired(ob):
    # Return true if this object is not a direct
    # subobject of its __parent__ object.
    if not hasattr(ob, '__parent__'):
        return 0
    if hasattr(aq_base(aq_parent(ob)), absattr(ob.id)):
        return 0
    if hasattr(aq_base(ob), 'isTopLevelPrincipiaApplicationObject') and \
            ob.isTopLevelPrincipiaApplicationObject:
        return 0
    return 1


def urlbase(url, ftype=urllib.splittype, fhost=urllib.splithost):
    # Return a '/' based url such as '/foo/bar', removing
    # type, host and port information if necessary.
    if url[0] == '/':
        return url
    type, uri = ftype(url)
    host, uri = fhost(uri)
    return uri or '/'


def isDavCollection(object):
    """Return true if object is a DAV collection."""
    return getattr(object, '__dav_collection__', 0)


def tokenFinder(token):
    # takes a string like '<opaquelocktoken:afsdfadfadf> and returns the token
    # part.
    if not token:
        return None  # An empty string was passed in
    if token[0] == '[':
        return None  # An Etag was passed in
    if token[0] == '<':
        token = token[1:-1]
    return token[token.find(':') + 1:]


# If: header handling support.  IfParser returns a sequence of
# TagList objects in the order they were parsed which can then
# be used in WebDAV methods to decide whether an operation can
# proceed or to raise HTTP Error 412 (Precondition failed)
IfHdr = re.compile(
    r"(?P<resource><.+?>)?\s*\((?P<listitem>[^)]+)\)"
)

ListItem = re.compile(
    r"(?P<not>not)?\s*(?P<listitem><[a-zA-Z]+:[^>]*>|\[.*?\])",
    re.I)


class TagList:
    def __init__(self):
        self.resource = None
        self.list = []
        self.NOTTED = 0


def IfParser(hdr):
    out = []
    i = 0
    while 1:
        m = IfHdr.search(hdr[i:])
        if not m:
            break

        i = i + m.end()
        tag = TagList()
        tag.resource = m.group('resource')
        if tag.resource:                # We need to delete < >
            tag.resource = tag.resource[1:-1]
        listitem = m.group('listitem')
        tag.NOTTED, tag.list = ListParser(listitem)
        out.append(tag)

    return out


def ListParser(listitem):
    out = []
    NOTTED = 0
    i = 0
    while 1:
        m = ListItem.search(listitem[i:])
        if not m:
            break

        i = i + m.end()
        out.append(m.group('listitem'))
        if m.group('not'):
            NOTTED = 1

    return NOTTED, out
