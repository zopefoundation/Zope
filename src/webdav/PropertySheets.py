##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

from cgi import escape
import sys

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityManagement import getSecurityManager
from App.Common import iso8601_date
from App.Common import rfc1123_date
from OFS.interfaces import IWriteLock
from OFS.PropertySheets import Virtual, PropertySheet, View

from webdav.common import isDavCollection
from webdav.common import urlbase

if sys.version_info >= (3, ):
    basestring = str
    unicode = str


def absattr(attr):
    if callable(attr):
        return attr()
    return attr


def xml_escape(value):
    from webdav.xmltools import escape
    if not isinstance(value, basestring):
        value = unicode(value)
    if not isinstance(value, unicode):
        value = value.decode('utf-8')
    value = escape(value)
    return value.encode('utf-8')


class DAVProperties(Virtual, PropertySheet, View):
    """WebDAV properties"""

    id = 'webdav'
    _md = {'xmlns': 'DAV:'}
    pm = ({'id': 'creationdate', 'mode': 'r'},
          {'id': 'displayname', 'mode': 'r'},
          {'id': 'resourcetype', 'mode': 'r'},
          {'id': 'getcontenttype', 'mode': 'r'},
          {'id': 'getcontentlength', 'mode': 'r'},
          {'id': 'source', 'mode': 'r'},
          {'id': 'supportedlock', 'mode': 'r'},
          {'id': 'lockdiscovery', 'mode': 'r'},
          )

    def getProperty(self, id, default=None):
        method = 'dav__%s' % id
        if not hasattr(self, method):
            return default
        return getattr(self, method)()

    def _setProperty(self, id, value, type='string', meta=None):
        raise ValueError('%s cannot be set.' % escape(id))

    def _updateProperty(self, id, value):
        raise ValueError('%s cannot be updated.' % escape(id))

    def _delProperty(self, id):
        raise ValueError('%s cannot be deleted.' % escape(id))

    def _propertyMap(self):
        # Only use getlastmodified if returns a value
        if hasattr(self.v_self(), '_p_mtime'):
            return self.pm + ({'id': 'getlastmodified', 'mode': 'r'},)
        return self.pm

    def propertyMap(self):
        return [dict.copy() for dict in self._propertyMap()]

    def dav__creationdate(self):
        return iso8601_date(43200.0)

    def dav__displayname(self):
        return absattr(xml_escape(self.v_self().title_or_id()))

    def dav__resourcetype(self):
        vself = self.v_self()
        if isDavCollection(vself):
            return '<n:collection/>'
        return ''

    def dav__getlastmodified(self):
        return rfc1123_date(self.v_self()._p_mtime)

    def dav__getcontenttype(self):
        vself = self.v_self()
        if hasattr(vself, 'content_type'):
            return absattr(vself.content_type)
        if hasattr(vself, 'default_content_type'):
            return absattr(vself.default_content_type)
        return ''

    def dav__getcontentlength(self):
        vself = self.v_self()
        if hasattr(vself, 'get_size'):
            return vself.get_size()
        return ''

    def dav__source(self):
        vself = self.v_self()
        if hasattr(vself, 'document_src'):
            url = urlbase(vself.absolute_url())
            return '\n  <n:link>\n' \
                   '  <n:src>%s</n:src>\n' \
                   '  <n:dst>%s/document_src</n:dst>\n' \
                   '  </n:link>\n  ' % (url, url)
        return ''

    def dav__supportedlock(self):
        vself = self.v_self()
        out = '\n'
        if IWriteLock.providedBy(vself):
            out += ('  <n:lockentry>\n'
                    '  <d:lockscope><d:exclusive/></d:lockscope>\n'
                    '  <d:locktype><d:write/></d:locktype>\n'
                    '  </n:lockentry>\n  ')
        return out

    def dav__lockdiscovery(self):
        security = getSecurityManager()
        user = security.getUser().getId()

        vself = self.v_self()
        out = '\n'
        if IWriteLock.providedBy(vself):
            locks = vself.wl_lockValues(killinvalids=1)
            for lock in locks:

                creator = lock.getCreator()[-1]
                if creator == user:
                    fake = 0
                else:
                    fake = 1

                out = '%s\n%s' % (
                    out, lock.asLockDiscoveryProperty('n', fake=fake))

            out = '%s\n' % out

        return out

InitializeClass(DAVProperties)
